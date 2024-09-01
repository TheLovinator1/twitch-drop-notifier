import asyncio
import json
import logging
import typing
from pathlib import Path
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand
from platformdirs import user_data_dir
from playwright.async_api import Playwright, async_playwright
from playwright.async_api._generated import Response

from core.models import Benefit, DropCampaign, Game, Owner, Reward, RewardCampaign, TimeBasedDrop

if TYPE_CHECKING:
    from playwright.async_api._generated import BrowserContext, Page


logger: logging.Logger = logging.getLogger(__name__)


def get_data_dir() -> Path:
    """Get the data directory.

    Returns:
        Path: The data directory.
    """
    return Path(
        user_data_dir(
            appname="TTVDrops",
            appauthor="TheLovinator",
            roaming=True,
            ensure_exists=True,
        ),
    )


def get_profile_dir() -> Path:
    """Get the profile directory for the browser.

    Returns:
        Path: The profile directory.
    """
    profile_dir = Path(get_data_dir() / "chrome-profile")
    profile_dir.mkdir(parents=True, exist_ok=True)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Launching Chrome browser with user data directory: %s", profile_dir)
    return profile_dir


def save_json(campaign: dict | None, dir_name: str) -> None:
    """Save JSON data to a file.

    Args:
        campaign (dict): The JSON data to save.
        dir_name (Path): The directory to save the JSON data to.
    """
    if not campaign:
        return

    save_dir = Path(dir_name)
    save_dir.mkdir(parents=True, exist_ok=True)

    # File name is the hash of the JSON data
    file_name: str = f"{hash(json.dumps(campaign))}.json"

    with Path(save_dir / file_name).open(mode="w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=4)


async def add_reward_campaign(campaign: dict | None) -> None:
    """Add a reward campaign to the database.

    Args:
        campaign (dict): The reward campaign to add.
    """
    if not campaign:
        return
    if "data" in campaign and "rewardCampaignsAvailableToUser" in campaign["data"]:
        for reward_campaign in campaign["data"]["rewardCampaignsAvailableToUser"]:
            our_reward_campaign, created = await RewardCampaign.objects.aupdate_or_create(id=reward_campaign["id"])
            await our_reward_campaign.import_json(reward_campaign)
            if created:
                logger.info("Added reward campaign %s", our_reward_campaign)

            if "rewards" in reward_campaign:
                for reward in reward_campaign["rewards"]:
                    reward_instance, created = await Reward.objects.aupdate_or_create(id=reward["id"])
                    await reward_instance.import_json(reward, our_reward_campaign)
                    if created:
                        logger.info("Added reward %s", reward_instance)


async def add_drop_campaign(drop_campaign: dict | None) -> None:
    """Add a drop campaign to the database.

    Args:
        drop_campaign (dict): The drop campaign to add.
    """
    if not drop_campaign:
        return

    if drop_campaign.get("game"):
        owner, created = await Owner.objects.aupdate_or_create(id=drop_campaign["owner"]["id"])
        owner.import_json(drop_campaign["owner"])

        game, created = await Game.objects.aupdate_or_create(id=drop_campaign["game"]["id"])
        await game.import_json(drop_campaign["game"], owner)
        if created:
            logger.info("Added game %s", game)

    our_drop_campaign, created = await DropCampaign.objects.aupdate_or_create(id=drop_campaign["id"])
    await our_drop_campaign.import_json(drop_campaign, game)

    if created:
        logger.info("Added drop campaign %s", our_drop_campaign.id)

    await add_time_based_drops(drop_campaign, our_drop_campaign)


async def add_time_based_drops(drop_campaign: dict, our_drop_campaign: DropCampaign) -> None:
    """Add time-based drops to the database.

    Args:
        drop_campaign (dict): The drop campaign containing time-based drops.
        our_drop_campaign (DropCampaign): The drop campaign object in the database.
    """
    for time_based_drop in drop_campaign.get("timeBasedDrops", []):
        time_based_drop: dict[str, typing.Any]
        if time_based_drop.get("preconditionDrops"):
            # TODO(TheLovinator): Add precondition drops to time-based drop  # noqa: TD003
            # TODO(TheLovinator): Send JSON to Discord  # noqa: TD003
            msg = "Not implemented: Add precondition drops to time-based drop"
            raise NotImplementedError(msg)

        our_time_based_drop, created = await TimeBasedDrop.objects.aupdate_or_create(id=time_based_drop["id"])
        await our_time_based_drop.import_json(time_based_drop, our_drop_campaign)

        if created:
            logger.info("Added time-based drop %s", our_time_based_drop.id)

        if our_time_based_drop and time_based_drop.get("benefitEdges"):
            for benefit_edge in time_based_drop["benefitEdges"]:
                benefit, created = await Benefit.objects.aupdate_or_create(id=benefit_edge["benefit"])
                await benefit.import_json(benefit_edge["benefit"], our_time_based_drop)
                if created:
                    logger.info("Added benefit %s", benefit.id)


async def process_json_data(num: int, campaign: dict | None) -> None:
    """Process JSON data.

    Args:
        num (int): The number of the JSON data.
        campaign (dict): The JSON data to process.
    """
    logger.info("Processing JSON %d", num)
    if not campaign:
        logger.warning("No campaign found for JSON %d", num)
        return

    if not isinstance(campaign, dict):
        logger.warning("Campaign is not a dictionary. %s", campaign)
        return

    # This is a Reward Campaign
    if "rewardCampaignsAvailableToUser" in campaign.get("data", {}):
        save_json(campaign=campaign, dir_name="reward_campaigns")
        await add_reward_campaign(campaign=campaign)

    if "dropCampaign" in campaign.get("data", {}).get("user", {}):
        save_json(campaign=campaign, dir_name="drop_campaign")
        if campaign.get("data", {}).get("user", {}).get("dropCampaign"):
            await add_drop_campaign(drop_campaign=campaign["data"]["user"]["dropCampaign"])

    if "dropCampaigns" in campaign.get("data", {}).get("currentUser", {}):
        for drop_campaign in campaign["data"]["currentUser"]["dropCampaigns"]:
            save_json(campaign=campaign, dir_name="drop_campaigns")
            await add_drop_campaign(drop_campaign=drop_campaign)


class Command(BaseCommand):
    help = "Scrape Twitch Drops Campaigns with login using Firefox"

    @staticmethod
    async def run(playwright: Playwright) -> list[dict[str, typing.Any]]:
        profile_dir: Path = get_profile_dir()
        browser: BrowserContext = await playwright.chromium.launch_persistent_context(
            channel="chrome",
            user_data_dir=profile_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
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
                    selector='div[data-a-target="top-nav-avatar"]',
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

        await browser.close()

        for num, campaign in enumerate(json_data, start=1):
            await process_json_data(num=num, campaign=campaign)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright=playwright)


if __name__ == "__main__":
    Command().handle()
