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

from core.models import Benefit, DropCampaign, Game, Owner, RewardCampaign, TimeBasedDrop

if TYPE_CHECKING:
    from playwright.async_api._generated import BrowserContext, Page


logger: logging.Logger = logging.getLogger(__name__)


def get_profile_dir() -> Path:
    """Get the profile directory for the browser.

    Returns:
        Path: The profile directory.
    """
    data_dir = Path(
        user_data_dir(appname="TTVDrops", appauthor="TheLovinator", roaming=True, ensure_exists=True),
    )
    profile_dir: Path = data_dir / "chrome-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Launching Chrome browser with user data directory: %s", profile_dir)
    return profile_dir


def save_json(campaign: dict | None, *, local: bool) -> None:
    """Save JSON data to a file.

    Args:
        campaign (dict): The JSON data to save.
        local (bool): Only save JSON data if we are scraping from the web.
    """
    if local:
        return

    if not campaign:
        return

    save_dir = Path("json")
    save_dir.mkdir(parents=True, exist_ok=True)

    # File name is the hash of the JSON data
    file_name: str = f"{hash(json.dumps(campaign))}.json"

    with Path(save_dir / file_name).open(mode="w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=4)


async def add_reward_campaign(reward_campaign: dict | None) -> None:
    """Add a reward campaign to the database.

    Args:
        reward_campaign (dict): The reward campaign to add.
    """
    if not reward_campaign:
        return

    our_reward_campaign, created = await RewardCampaign.objects.aupdate_or_create(twitch_id=reward_campaign["id"])
    await our_reward_campaign.aimport_json(reward_campaign)
    if created:
        logger.info("Added reward campaign %s", our_reward_campaign)


async def add_drop_campaign(drop_campaign: dict | None) -> None:
    """Add a drop campaign to the database.

    Args:
        drop_campaign (dict): The drop campaign to add.
    """
    if not drop_campaign:
        return

    if not drop_campaign.get("owner", {}):
        logger.error("Owner not found in drop campaign %s", drop_campaign)
        return

    owner, created = await Owner.objects.aupdate_or_create(twitch_id=drop_campaign["owner"]["id"])
    await owner.aimport_json(data=drop_campaign["owner"])
    if created:
        logger.info("Added owner %s", owner.twitch_id)

    if not drop_campaign.get("game", {}):
        logger.error("Game not found in drop campaign %s", drop_campaign)
        return

    game, created = await Game.objects.aupdate_or_create(twitch_id=drop_campaign["game"]["id"])
    await game.aimport_json(data=drop_campaign["game"], owner=owner)
    if created:
        logger.info("Added game %s", game)

    our_drop_campaign, created = await DropCampaign.objects.aupdate_or_create(twitch_id=drop_campaign["id"])
    await our_drop_campaign.aimport_json(drop_campaign, game)
    if created:
        logger.info("Added drop campaign %s", our_drop_campaign.twitch_id)

    await add_time_based_drops(drop_campaign, our_drop_campaign)

    # Check if eventBasedDrops exist
    if drop_campaign.get("eventBasedDrops"):
        # TODO(TheLovinator): Add event-based drops  # noqa: TD003
        msg = "Not implemented: Add event-based drops"
        raise NotImplementedError(msg)


async def add_time_based_drops(drop_campaign: dict, our_drop_campaign: DropCampaign) -> None:
    """Add time-based drops to the database.

    Args:
        drop_campaign (dict): The drop campaign containing time-based drops.
        our_drop_campaign (DropCampaign): The drop campaign object in the database.
    """
    for time_based_drop in drop_campaign.get("timeBasedDrops", []):
        if time_based_drop.get("preconditionDrops"):
            # TODO(TheLovinator): Add precondition drops to time-based drop  # noqa: TD003
            # TODO(TheLovinator): Send JSON to Discord  # noqa: TD003
            msg = "Not implemented: Add precondition drops to time-based drop"
            raise NotImplementedError(msg)

        our_time_based_drop, created = await TimeBasedDrop.objects.aupdate_or_create(twitch_id=time_based_drop["id"])
        await our_time_based_drop.aimport_json(time_based_drop, our_drop_campaign)

        if created:
            logger.info("Added time-based drop %s", our_time_based_drop.twitch_id)

        if our_time_based_drop and time_based_drop.get("benefitEdges"):
            for benefit_edge in time_based_drop["benefitEdges"]:
                benefit, created = await Benefit.objects.aupdate_or_create(twitch_id=benefit_edge["benefit"])
                await benefit.aimport_json(benefit_edge["benefit"], our_time_based_drop)
                if created:
                    logger.info("Added benefit %s", benefit.twitch_id)


async def handle_drop_campaigns(drop_campaign: dict) -> None:
    """Handle drop campaigns.

    We need to grab the game image in data.currentUser.dropCampaigns.game.boxArtURL.

    Args:
        drop_campaign (dict): The drop campaign to handle.
    """
    if not drop_campaign:
        return

    if drop_campaign.get("game", {}).get("boxArtURL"):
        owner_id = drop_campaign.get("owner", {}).get("id")
        if not owner_id:
            logger.error("Owner ID not found in drop campaign %s", drop_campaign)
            return

        owner, created = await Owner.objects.aupdate_or_create(twitch_id=drop_campaign["owner"]["id"])
        await owner.aimport_json(drop_campaign["owner"])
        if created:
            logger.info("Added owner %s", owner.twitch_id)

        game_obj, created = await Game.objects.aupdate_or_create(twitch_id=drop_campaign["game"]["id"])
        await game_obj.aimport_json(data=drop_campaign["game"], owner=owner)
        if created:
            logger.info("Added game %s", game_obj.twitch_id)


async def process_json_data(num: int, campaign: dict | None, *, local: bool) -> None:
    """Process JSON data.

    Args:
        num (int): The number of the JSON data.
        campaign (dict): The JSON data to process.
        local (bool): Only save JSON data if we are scraping from the web.
    """
    logger.info("Processing JSON %d", num)
    if not campaign:
        logger.warning("No campaign found for JSON %d", num)
        return

    if not isinstance(campaign, dict):
        logger.warning("Campaign is not a dictionary. %s", campaign)
        return

    save_json(campaign=campaign, local=local)

    if campaign.get("data", {}).get("rewardCampaignsAvailableToUser"):
        for reward_campaign in campaign["data"]["rewardCampaignsAvailableToUser"]:
            await add_reward_campaign(reward_campaign=reward_campaign)

    if campaign.get("data", {}).get("user", {}).get("dropCampaign"):
        await add_drop_campaign(drop_campaign=campaign["data"]["user"]["dropCampaign"])

    if campaign.get("data", {}).get("currentUser", {}).get("dropCampaigns"):
        for drop_campaign in campaign["data"]["currentUser"]["dropCampaigns"]:
            await handle_drop_campaigns(drop_campaign=drop_campaign)


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
            await process_json_data(num=num, campaign=campaign, local=True)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright=playwright)


if __name__ == "__main__":
    Command().handle()
