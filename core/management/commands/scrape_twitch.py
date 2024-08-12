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

from core.models.twitch import Benefit, Channel, DropCampaign, Game, Owner, Reward, RewardCampaign, TimeBasedDrop

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
    profile_dir: Path = Path(get_data_dir() / "chrome-profile")
    profile_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Launching Chrome browser with user data directory: %s", profile_dir)
    return profile_dir


def save_json(campaign: dict, dir_name: str) -> None:
    """Save JSON data to a file.

    Args:
        campaign (dict): The JSON data to save.
        dir_name (Path): The directory to save the JSON data to.
    """
    save_dir: Path = Path(dir_name)
    save_dir.mkdir(parents=True, exist_ok=True)

    # File name is the hash of the JSON data
    file_name: str = f"{hash(json.dumps(campaign))}.json"

    with Path(save_dir / file_name).open(mode="w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=4)


async def add_reward_campaign(campaign: dict) -> None:
    """Add a reward campaign to the database.

    Args:
        campaign (dict): The reward campaign to add.
    """
    logger.info("Adding reward campaign to database")
    for reward_campaign in campaign["data"]["rewardCampaignsAvailableToUser"]:
        our_reward_campaign, created = await RewardCampaign.objects.aget_or_create(
            id=reward_campaign["id"],
            defaults={
                "name": reward_campaign["name"],
                "brand": reward_campaign["brand"],
                "starts_at": reward_campaign["startsAt"],
                "ends_at": reward_campaign["endsAt"],
                "status": reward_campaign["status"],
                "summary": reward_campaign["summary"],
                "instructions": reward_campaign["instructions"],
                "reward_value_url_param": reward_campaign["rewardValueURLParam"],
                "external_url": reward_campaign["externalURL"],
                "about_url": reward_campaign["aboutURL"],
                "is_site_wide": reward_campaign["isSitewide"],
                "sub_goal": reward_campaign["unlockRequirements"]["subsGoal"],
                "minute_watched_goal": reward_campaign["unlockRequirements"]["minuteWatchedGoal"],
                "image_url": reward_campaign["image"]["image1xURL"],
                # "game" # To be implemented
            },
        )
        if created:
            logger.info("Added reward campaign %s", our_reward_campaign.id)
        else:
            logger.info("Updated reward campaign %s", our_reward_campaign.id)

        if reward_campaign["game"]:
            # TODO(TheLovinator): Add game to reward campaign  # noqa: TD003
            # TODO(TheLovinator): Send JSON to Discord # noqa: TD003
            logger.error("Not implemented: Add game to reward campaign, JSON: %s", reward_campaign["game"])

        # Add rewards
        for reward in reward_campaign["rewards"]:
            our_reward, created = await Reward.objects.aget_or_create(
                id=reward["id"],
                defaults={
                    "name": reward["name"],
                    "banner_image_url": reward["bannerImage"]["image1xURL"],
                    "thumbnail_image_url": reward["thumbnailImage"]["image1xURL"],
                    "earnable_until": reward["earnableUntil"],
                    "redemption_instructions": reward["redemptionInstructions"],
                    "redemption_url": reward["redemptionURL"],
                    "campaign": our_reward_campaign,
                },
            )
            if created:
                logger.info("Added reward %s", our_reward.id)
            else:
                logger.info("Updated reward %s", our_reward.id)


async def add_or_update_game(game_json: dict, owner: Owner | None) -> Game | None:
    """Add or update a game in the database.

    Args:
        game_json (dict): The game to add or update.
        owner (Owner): The owner of the game.

    Returns:
        Game: The game that was added or updated.
    """
    if game_json:
        game_url: str | None = (
            f"https://www.twitch.tv/directory/game/{game_json["slug"]}" if game_json["slug"] else None
        )
        our_game, created = await Game.objects.aget_or_create(
            twitch_id=game_json["id"],
            defaults={
                "slug": game_json["slug"],
                "name": game_json["displayName"],
                "game_url": game_url,
                "org": owner,
                # TODO(TheLovinator): Add box_art_url to game  # noqa: TD003
            },
        )
        if created:
            logger.info("Added game %s", our_game.twitch_id)
        else:
            logger.info("Updated game %s", our_game.twitch_id)
        return our_game
    return None


async def add_or_update_owner(owner_json: dict) -> Owner | None:
    """Add or update an owner in the database.

    Args:
        owner_json (dict): The owner to add or update.

    Returns:
        Owner: The owner that was added or updated.
    """
    if owner_json:
        our_owner, created = await Owner.objects.aget_or_create(
            id=owner_json["id"],
            defaults={"name": owner_json["name"]},
        )
        if created:
            logger.info("Added owner %s", our_owner.id)
        else:
            logger.info("Updated owner %s", our_owner.id)
        return our_owner
    return None


async def add_or_update_channels(channels_json: list[dict]) -> list[Channel] | None:
    """Add or update channels in the database.

    Args:
        channels_json (list[dict]): The channels to add or update.

    Returns:
        list[Channel]: The channels that were added or updated.
    """
    if not channels_json:
        return None

    channels: list[Channel] = []
    for channel_json in channels_json:
        twitch_url: str | None = f"https://www.twitch.tv/{channel_json["name"]}" if channel_json["name"] else None
        our_channel, created = await Channel.objects.aget_or_create(
            twitch_id=channel_json["id"],
            defaults={
                "name": channel_json["name"],
                "display_name": channel_json["displayName"],
                "twitch_url": twitch_url,
                "live": False,  # Toggle this later
            },
        )
        if created:
            logger.info("Added channel %s", our_channel.twitch_id)
        else:
            logger.info("Updated channel %s", our_channel.twitch_id)
        channels.append(our_channel)

    return channels


async def add_benefit(benefit: dict, time_based_drop: TimeBasedDrop) -> None:
    """Add a benefit to the database.

    Args:
        benefit (dict): The benefit to add.
        time_based_drop (TimeBasedDrop): The time-based drop the benefit belongs to.
    """
    our_benefit, created = await Benefit.objects.aget_or_create(
        id=benefit["id"],
        defaults={
            "twitch_created_at": benefit["createdAt"],
            "entitlement_limit": benefit["entitlementLimit"],
            "image_url": benefit["imageAssetURL"],
            "is_ios_available": benefit["isIosAvailable"],
            "name": benefit["name"],
            "time_based_drop": time_based_drop,
        },
    )
    if created:
        logger.info("Added benefit %s", our_benefit.id)
    else:
        logger.info("Updated benefit %s", our_benefit.id)


async def add_drop_campaign(drop_campaign: dict) -> None:
    """Add a drop campaign to the database.

    Args:
        drop_campaign (dict): The drop campaign to add.
    """
    logger.info("Adding drop campaign to database")
    owner: Owner | None = await add_or_update_owner(drop_campaign["owner"])
    game: Game | None = await add_or_update_game(drop_campaign["game"], owner)
    channels: list[Channel] | None = await add_or_update_channels(drop_campaign["allow"]["channels"])

    our_drop_campaign, created = await DropCampaign.objects.aget_or_create(
        id=drop_campaign["id"],
        defaults={
            "account_link_url": drop_campaign["accountLinkURL"],
            "description": drop_campaign["description"],
            "details_url": drop_campaign["detailsURL"],
            "ends_at": drop_campaign["endAt"],
            "starts_at": drop_campaign["startAt"],
            "image_url": drop_campaign["imageURL"],
            "name": drop_campaign["name"],
            "status": drop_campaign["status"],
            "game": game,
        },
    )
    if created:
        logger.info("Added drop campaign %s", our_drop_campaign.id)
    else:
        logger.info("Updated drop campaign %s", our_drop_campaign.id)

    if channels:
        our_drop_campaign.channels.aset(channels)  # type: ignore  # noqa: PGH003

    # Add time-based drops
    for time_based_drop in drop_campaign["timeBasedDrops"]:
        if time_based_drop["preconditionDrops"]:
            # TODO(TheLovinator): Add precondition drops to time-based drop  # noqa: TD003
            # TODO(TheLovinator): Send JSON to Discord # noqa: TD003
            logger.error("Not implemented: Add precondition drops to time-based drop, JSON: %s", time_based_drop)

        our_time_based_drop, created = await TimeBasedDrop.objects.aget_or_create(
            id=time_based_drop["id"],
            defaults={
                "required_subs": time_based_drop["requiredSubs"],
                "ends_at": time_based_drop["endAt"],
                "name": time_based_drop["name"],
                "required_minutes_watched": time_based_drop["requiredMinutesWatched"],
                "starts_at": time_based_drop["startAt"],
                "drop_campaign": our_drop_campaign,
            },
        )
        if created:
            logger.info("Added time-based drop %s", our_time_based_drop.id)
        else:
            logger.info("Updated time-based drop %s", our_time_based_drop.id)

        # Add benefits
        for benefit_edge in time_based_drop["benefitEdges"]:
            await add_benefit(benefit_edge["benefit"], our_time_based_drop)


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
        logger.warning("Campaign is not a dictionary")
        return

    # This is a Reward Campaign
    if "rewardCampaignsAvailableToUser" in campaign["data"]:
        save_json(campaign, "reward_campaigns")
        await add_reward_campaign(campaign)

    if "dropCampaign" in campaign.get("data", {}).get("user", {}):
        if not campaign["data"]["user"]["dropCampaign"]:
            logger.warning("No drop campaign found")
            return

        save_json(campaign, "drop_campaign")
        await add_drop_campaign(campaign["data"]["user"]["dropCampaign"])

    if "dropCampaigns" in campaign.get("data", {}).get("user", {}):
        for drop_campaign in campaign["data"]["currentUser"]["dropCampaigns"]:
            save_json(campaign, "drop_campaigns")
            await add_drop_campaign(drop_campaign)


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

        await browser.close()

        for num, campaign in enumerate(json_data, start=1):
            await process_json_data(num=num, campaign=campaign)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)


if __name__ == "__main__":
    Command().handle()
