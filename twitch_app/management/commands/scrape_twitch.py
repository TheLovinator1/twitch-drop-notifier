import asyncio
import logging
import typing
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from platformdirs import user_data_dir
from playwright.async_api import Playwright, async_playwright
from playwright.async_api._generated import Response

from twitch_app.models import Game, Image, Reward, RewardCampaign, UnlockRequirements

if TYPE_CHECKING:
    from playwright.async_api._generated import BrowserContext, Page

# Where to store the Chrome profile
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

logger: logging.Logger = logging.getLogger(__name__)


async def add_reward_campaign(json_data: dict) -> None:
    """Add data from JSON to the database."""
    for campaign_data in json_data["data"]["rewardCampaignsAvailableToUser"]:
        # Add or get Game
        game_data = campaign_data["game"]
        if game_data:
            game, _ = await sync_to_async(Game.objects.get_or_create)(
                id=game_data["id"],
                slug=game_data["slug"],
                defaults={
                    "display_name": game_data["displayName"],
                    "typename": game_data["__typename"],
                },
            )
        else:
            logger.warning("%s is not for a game?", campaign_data["name"])
            game = None

        # Add or get Image
        image_data = campaign_data["image"]
        image, _ = await sync_to_async(Image.objects.get_or_create)(
            image1_x_url=image_data["image1xURL"],
            defaults={"typename": image_data["__typename"]},
        )

        # Create Reward instances
        rewards = []
        for reward_data in campaign_data["rewards"]:
            banner_image_data = reward_data["bannerImage"]
            banner_image, _ = await sync_to_async(Image.objects.get_or_create)(
                image1_x_url=banner_image_data["image1xURL"],
                defaults={"typename": banner_image_data["__typename"]},
            )

            thumbnail_image_data = reward_data["thumbnailImage"]
            thumbnail_image, _ = await sync_to_async(Image.objects.get_or_create)(
                image1_x_url=thumbnail_image_data["image1xURL"],
                defaults={"typename": thumbnail_image_data["__typename"]},
            )

            reward, _ = await sync_to_async(Reward.objects.get_or_create)(
                id=reward_data["id"],
                name=reward_data["name"],
                banner_image=banner_image,
                thumbnail_image=thumbnail_image,
                earnable_until=datetime.fromisoformat(reward_data["earnableUntil"].replace("Z", "+00:00")),
                redemption_instructions=reward_data["redemptionInstructions"],
                redemption_url=reward_data["redemptionURL"],
                typename=reward_data["__typename"],
            )
            rewards.append(reward)

        # Add or get Unlock Requirements
        unlock_requirements_data = campaign_data["unlockRequirements"]
        _, _ = await sync_to_async(UnlockRequirements.objects.get_or_create)(
            subs_goal=unlock_requirements_data["subsGoal"],
            defaults={
                "minute_watched_goal": unlock_requirements_data["minuteWatchedGoal"],
                "typename": unlock_requirements_data["__typename"],
            },
        )

        # Create Reward Campaign
        reward_campaign, _ = await sync_to_async(RewardCampaign.objects.get_or_create)(
            id=campaign_data["id"],
            name=campaign_data["name"],
            brand=campaign_data["brand"],
            starts_at=datetime.fromisoformat(campaign_data["startsAt"].replace("Z", "+00:00")),
            ends_at=datetime.fromisoformat(campaign_data["endsAt"].replace("Z", "+00:00")),
            status=campaign_data["status"],
            summary=campaign_data["summary"],
            instructions=campaign_data["instructions"],
            external_url=campaign_data["externalURL"],
            reward_value_url_param=campaign_data["rewardValueURLParam"],
            about_url=campaign_data["aboutURL"],
            is_sitewide=campaign_data["isSitewide"],
            game=game,
            image=image,
            typename=campaign_data["__typename"],
        )

        # Add Rewards to the Campaign
        for reward in rewards:
            await sync_to_async(reward_campaign.rewards.add)(reward)

        await sync_to_async(reward_campaign.save)()


class Command(BaseCommand):
    help = "Scrape Twitch Drops Campaigns with login using Firefox"

    async def run(  # noqa: PLR6301, C901
        self,
        playwright: Playwright,
    ) -> list[dict[str, typing.Any]]:
        args = []

        # disable navigator.webdriver:true flag
        args.append("--disable-blink-features=AutomationControlled")

        profile_dir: Path = Path(data_dir / "chrome-profile")
        profile_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(
            "Launching Chrome browser with user data directory: %s",
            profile_dir,
        )

        browser: BrowserContext = await playwright.chromium.launch_persistent_context(
            channel="chrome",
            user_data_dir=profile_dir,
            headless=False,
            args=args,
        )
        logger.debug("Launched Chrome browser")

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
                    timeout=300000,
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

        # Wait 5 seconds for the page to load
        # await asyncio.sleep(5)

        await browser.close()

        for num, campaign in enumerate(json_data, start=1):
            logger.info("Processing JSON %d of %d", num, len(json_data))
            if not isinstance(campaign, dict):
                continue

            if "rewardCampaignsAvailableToUser" in campaign["data"]:
                await add_reward_campaign(campaign)

            if "dropCampaign" in campaign.get("data", {}).get("user", {}):  # noqa: SIM102
                if not campaign["data"]["user"]["dropCampaign"]:
                    continue

            if "dropCampaigns" in campaign.get("data", {}).get("user", {}):
                msg = "Multiple dropCampaigns not supported"
                raise NotImplementedError(msg)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)


if __name__ == "__main__":
    Command().handle()
