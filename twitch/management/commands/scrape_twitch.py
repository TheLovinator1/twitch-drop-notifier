import asyncio
import typing
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from platformdirs import user_data_dir
from playwright.async_api import Playwright, async_playwright
from playwright.async_api._generated import Response

from twitch.models import (
    Channel,
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
    User,
)

if TYPE_CHECKING:
    from playwright.async_api._generated import BrowserContext, Page

data_dir = Path(
    user_data_dir(
        appname="TTVDrops",
        appauthor="TheLovinator",
        roaming=True,
        ensure_exists=True,
    ),
)

if not data_dir:
    msg = "DATA_DIR is not set in settings.py"
    raise ValueError(msg)


async def insert_data(data: dict) -> None:  # noqa: PLR0914
    """Insert data into the database.

    Args:
        data: The data from Twitch.
    """
    user_data: dict = data.get("data", {}).get("user")
    if not user_data:
        return

    user_id = user_data["id"]
    drop_campaign_data = user_data["dropCampaign"]
    if not drop_campaign_data:
        return

    # Create or get the organization
    owner_data = drop_campaign_data["owner"]
    owner, _ = await sync_to_async(Organization.objects.get_or_create)(
        id=owner_data["id"],
        defaults={"name": owner_data["name"]},
    )

    # Create or get the game
    game_data = drop_campaign_data["game"]
    game, _ = await sync_to_async(Game.objects.get_or_create)(
        id=game_data["id"],
        defaults={
            "slug": game_data["slug"],
            "display_name": game_data["displayName"],
        },
    )

    # Create the drop campaign
    drop_campaign, _ = await sync_to_async(DropCampaign.objects.get_or_create)(
        id=drop_campaign_data["id"],
        defaults={
            "account_link_url": drop_campaign_data["accountLinkURL"],
            "description": drop_campaign_data["description"],
            "details_url": drop_campaign_data["detailsURL"],
            "end_at": drop_campaign_data["endAt"],
            "image_url": drop_campaign_data["imageURL"],
            "name": drop_campaign_data["name"],
            "start_at": drop_campaign_data["startAt"],
            "status": drop_campaign_data["status"],
            "game": game,
            "owner": owner,
        },
    )
    if not drop_campaign_data["allow"]:
        return

    if not drop_campaign_data["allow"]["channels"]:
        return

    # Create channels
    for channel_data in drop_campaign_data["allow"]["channels"]:
        channel, _ = await sync_to_async(Channel.objects.get_or_create)(
            id=channel_data["id"],
            defaults={
                "display_name": channel_data["displayName"],
                "name": channel_data["name"],
            },
        )
        await sync_to_async(drop_campaign.channels.add)(channel)

    # Create time-based drops
    for drop_data in drop_campaign_data["timeBasedDrops"]:
        drop_benefit_edges = drop_data["benefitEdges"]
        drop_benefits = []

        for edge in drop_benefit_edges:
            benefit_data = edge["benefit"]
            benefit_owner_data = benefit_data["ownerOrganization"]

            benefit_owner, _ = await sync_to_async(Organization.objects.get_or_create)(
                id=benefit_owner_data["id"],
                defaults={"name": benefit_owner_data["name"]},
            )

            benefit_game_data = benefit_data["game"]
            benefit_game, _ = await sync_to_async(Game.objects.get_or_create)(
                id=benefit_game_data["id"],
                defaults={"name": benefit_game_data["name"]},
            )

            benefit, _ = await sync_to_async(DropBenefit.objects.get_or_create)(
                id=benefit_data["id"],
                defaults={
                    "created_at": benefit_data["createdAt"],
                    "entitlement_limit": benefit_data["entitlementLimit"],
                    "image_asset_url": benefit_data["imageAssetURL"],
                    "is_ios_available": benefit_data["isIosAvailable"],
                    "name": benefit_data["name"],
                    "owner_organization": benefit_owner,
                    "game": benefit_game,
                },
            )
            drop_benefits.append(benefit)

        time_based_drop, _ = await sync_to_async(TimeBasedDrop.objects.get_or_create)(
            id=drop_data["id"],
            defaults={
                "required_subs": drop_data["requiredSubs"],
                "end_at": drop_data["endAt"],
                "name": drop_data["name"],
                "required_minutes_watched": drop_data["requiredMinutesWatched"],
                "start_at": drop_data["startAt"],
            },
        )
        await sync_to_async(time_based_drop.benefits.set)(drop_benefits)
        await sync_to_async(drop_campaign.time_based_drops.add)(time_based_drop)

    # Create or get the user
    user, _ = await sync_to_async(User.objects.get_or_create)(id=user_id)
    await sync_to_async(user.drop_campaigns.add)(drop_campaign)


class Command(BaseCommand):
    help = "Scrape Twitch Drops Campaigns with login using Firefox"

    async def run(self, playwright: Playwright) -> list[Any]:
        profile_dir: Path = Path(data_dir / "firefox-profile")
        profile_dir.mkdir(parents=True, exist_ok=True)

        browser: BrowserContext = await playwright.firefox.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
        )

        page: Page = await browser.new_page()
        json_data: list[dict] = []

        async def handle_response(response: Response) -> None:
            if "https://gql.twitch.tv/gql" in response.url:
                try:
                    body: typing.Any = await response.json()
                    json_data.extend(body)
                except Exception:  # noqa: BLE001
                    self.stdout.write(f"Failed to parse JSON from {response.url}")

        page.on("response", handle_response)
        await page.goto("https://www.twitch.tv/drops/campaigns")

        logged_in = False
        while not logged_in:
            try:
                await page.wait_for_selector(
                    'div[data-a-target="top-nav-avatar"]',
                    timeout=30000,
                )
                logged_in = True
                self.stdout.write("Logged in")
            except KeyboardInterrupt as e:
                raise KeyboardInterrupt from e
            except Exception:  # noqa: BLE001
                await asyncio.sleep(5)
                self.stdout.write("Waiting for login")

        await page.wait_for_load_state("networkidle")
        await browser.close()

        for campaign in json_data:
            if not isinstance(campaign, dict):
                continue

            if "dropCampaign" in campaign.get("data", {}).get("user", {}):
                await insert_data(campaign)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)


if __name__ == "__main__":
    Command().handle()
