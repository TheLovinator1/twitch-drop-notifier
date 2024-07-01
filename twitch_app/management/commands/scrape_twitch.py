import asyncio
import logging
import typing
from pathlib import Path
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from platformdirs import user_data_dir
from playwright.async_api import Playwright, async_playwright
from playwright.async_api._generated import Response

from twitch_app.models import (
    DropBenefit,
    DropCampaign,
    Game,
    Organization,
    TimeBasedDrop,
    User,
)

if TYPE_CHECKING:
    from playwright.async_api._generated import BrowserContext, Page

# Where to store the Firefox profile
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

logger: logging.Logger = logging.getLogger("twitch.management.commands.scrape_twitch")


async def insert_data(data: dict) -> None:  # noqa: PLR0914, C901
    """Insert data into the database.

    Args:
        data: The data from Twitch.
    """
    user_data: dict = data.get("data", {}).get("user")
    if not user_data:
        logger.debug("No user data found")
        return

    user_id = user_data["id"]
    drop_campaign_data = user_data["dropCampaign"]
    if not drop_campaign_data:
        return

    # Create or get the organization
    owner_data = drop_campaign_data["owner"]
    owner, created = await sync_to_async(Organization.objects.get_or_create)(
        id=owner_data["id"],
        defaults={"name": owner_data["name"]},
    )
    if created:
        logger.debug("Organization created: %s", owner)

    # Create or get the game
    game_data = drop_campaign_data["game"]
    game, created = await sync_to_async(Game.objects.get_or_create)(
        id=game_data["id"],
        defaults={
            "slug": game_data["slug"],
            "display_name": game_data["displayName"],
        },
    )
    if created:
        logger.debug("Game created: %s", game)

    # Create the drop campaign
    drop_campaign, created = await sync_to_async(DropCampaign.objects.get_or_create)(
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
    if created:
        logger.debug("Drop campaign created: %s", drop_campaign)

    # Create time-based drops
    for drop_data in drop_campaign_data["timeBasedDrops"]:
        drop_benefit_edges = drop_data["benefitEdges"]
        drop_benefits = []

        for edge in drop_benefit_edges:
            benefit_data = edge["benefit"]
            benefit_owner_data = benefit_data["ownerOrganization"]

            benefit_owner, created = await sync_to_async(
                Organization.objects.get_or_create,
            )(
                id=benefit_owner_data["id"],
                defaults={"name": benefit_owner_data["name"]},
            )
            if created:
                logger.debug("Benefit owner created: %s", benefit_owner)

            benefit_game_data = benefit_data["game"]
            benefit_game, created = await sync_to_async(Game.objects.get_or_create)(
                id=benefit_game_data["id"],
                defaults={"name": benefit_game_data["name"]},
            )
            if created:
                logger.debug("Benefit game created: %s", benefit_game)

            benefit, created = await sync_to_async(DropBenefit.objects.get_or_create)(
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
            if created:
                logger.debug("Benefit created: %s", benefit)

        time_based_drop, created = await sync_to_async(
            TimeBasedDrop.objects.get_or_create,
        )(
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

        if created:
            logger.debug("Time-based drop created: %s", time_based_drop)

    # Create or get the user
    user, created = await sync_to_async(User.objects.get_or_create)(id=user_id)
    await sync_to_async(user.drop_campaigns.add)(drop_campaign)
    if created:
        logger.debug("User created: %s", user)


class Command(BaseCommand):
    help = "Scrape Twitch Drops Campaigns with login using Firefox"

    async def run(  # noqa: PLR6301, C901
        self,
        playwright: Playwright,
    ) -> list[dict[str, typing.Any]]:
        profile_dir: Path = Path(data_dir / "firefox-profile")
        profile_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(
            "Launching Firefox browser with user data directory: %s",
            profile_dir,
        )

        browser: BrowserContext = await playwright.firefox.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
        )
        logger.debug("Launched Firefox browser")

        page: Page = await browser.new_page()
        json_data: list[dict] = []

        async def handle_response(response: Response) -> None:
            if "https://gql.twitch.tv/gql" in response.url:
                try:
                    body: typing.Any = await response.json()
                    json_data.extend(body)
                except Exception:
                    logger.exception(
                        "Failed to parse JSON from %s",
                        response.url,
                    )

        page.on("response", handle_response)
        await page.goto("https://www.twitch.tv/drops/campaigns")
        logger.debug("Navigated to Twitch drops campaigns page")

        logged_in = False
        while not logged_in:
            try:
                await page.wait_for_selector(
                    'div[data-a-target="top-nav-avatar"]',
                    timeout=30000,
                )
                logged_in = True
                logger.info("Logged in to Twitch")
            except KeyboardInterrupt as e:
                raise KeyboardInterrupt from e
            except Exception:  # noqa: BLE001
                await asyncio.sleep(5)
                logger.info("Waiting for login")

        await page.wait_for_load_state("networkidle")
        logger.debug("Page loaded. Scraping data...")

        await browser.close()

        for num, campaign in enumerate(json_data, start=1):
            logger.info("Processing JSON %d of %d", num, len(json_data))
            if not isinstance(campaign, dict):
                continue

            if "dropCampaign" in campaign.get("data", {}).get("user", {}):
                await insert_data(campaign)

            if "dropCampaigns" in campaign.get("data", {}).get("user", {}):
                await insert_data(campaign)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)


if __name__ == "__main__":
    Command().handle()
