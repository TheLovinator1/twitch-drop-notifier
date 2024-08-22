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

from core.models import Benefit, Channel, DropCampaign, Game, Owner, Reward, RewardCampaign, TimeBasedDrop

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
            our_reward_campaign: RewardCampaign = await handle_reward_campaign(reward_campaign)

            if "rewards" in reward_campaign:
                for reward in reward_campaign["rewards"]:
                    await handle_rewards(reward, our_reward_campaign)


async def handle_rewards(reward: dict, reward_campaign: RewardCampaign | None) -> None:
    """Add or update a reward in the database.

    Args:
        reward (dict): The JSON from Twitch.
        reward_campaign (RewardCampaign | None): The reward campaign the reward belongs to.
    """
    mappings: dict[str, str] = {
        "name": "name",
        "earnableUntil": "earnable_until",
        "redemptionInstructions": "redemption_instructions",
        "redemptionURL": "redemption_url",
    }

    defaults: dict = {new_key: reward[key] for key, new_key in mappings.items() if reward.get(key)}
    if reward_campaign:
        defaults["campaign"] = reward_campaign

        if reward.get("bannerImage"):
            defaults["banner_image_url"] = reward["bannerImage"]["image1xURL"]

        if reward.get("thumbnailImage"):
            defaults["thumbnail_image_url"] = reward["thumbnailImage"]["image1xURL"]

        reward_instance, created = await Reward.objects.aupdate_or_create(id=reward["id"], defaults=defaults)
    if created:
        logger.info("Added reward %s", reward_instance.id)


async def handle_reward_campaign(reward_campaign: dict) -> RewardCampaign:
    """Add or update a reward campaign in the database.

    Args:
        reward_campaign (dict): The reward campaign JSON from Twitch.

    Returns:
        RewardCampaign: The reward campaign that was added or updated.
    """
    mappings: dict[str, str] = {
        "name": "name",
        "brand": "brand",
        "createdAt": "created_at",
        "startsAt": "starts_at",
        "endsAt": "ends_at",
        "status": "status",
        "summary": "summary",
        "instructions": "instructions",
        "rewardValueURLParam": "reward_value_url_param",
        "externalURL": "external_url",
        "aboutURL": "about_url",
        "isSitewide": "is_site_wide",
    }

    defaults: dict = {new_key: reward_campaign[key] for key, new_key in mappings.items() if reward_campaign.get(key)}
    unlock_requirements: dict = reward_campaign.get("unlockRequirements", {})
    if unlock_requirements.get("subsGoal"):
        defaults["sub_goal"] = unlock_requirements["subsGoal"]
    if unlock_requirements.get("minuteWatchedGoal"):
        defaults["minute_watched_goal"] = unlock_requirements["minuteWatchedGoal"]

    if reward_campaign.get("image"):
        defaults["image_url"] = reward_campaign["image"]["image1xURL"]

    reward_campaign_instance, created = await RewardCampaign.objects.aupdate_or_create(
        id=reward_campaign["id"],
        defaults=defaults,
    )
    if created:
        logger.info("Added reward campaign %s", reward_campaign_instance.id)

    if reward_campaign["game"]:
        # TODO(TheLovinator): Add game to reward campaign  # noqa: TD003
        # TODO(TheLovinator): Send JSON to Discord # noqa: TD003
        logger.error("Not implemented: Add game to reward campaign, JSON: %s", reward_campaign["game"])
    return reward_campaign_instance


async def add_or_update_game(game_json: dict | None, owner: Owner | None) -> Game | None:
    """Add or update a game in the database.

    Args:
        game_json (dict): The game to add or update.
        owner (Owner): The owner of the game.

    Returns:
        Game: The game that was added or updated.
    """
    if not game_json:
        return None

    mappings: dict[str, str] = {
        "slug": "slug",
        "displayName": "name",
        "boxArtURL": "box_art_url",
    }
    defaults: dict = {new_key: game_json[key] for key, new_key in mappings.items() if game_json.get(key)}
    if game_json.get("slug"):
        defaults["game_url"] = f"https://www.twitch.tv/directory/game/{game_json["slug"]}"

    our_game, created = await Game.objects.aupdate_or_create(twitch_id=game_json["id"], defaults=defaults)
    if created:
        logger.info("Added game %s", our_game.twitch_id)

    if owner:
        await owner.games.aadd(our_game)  # type: ignore  # noqa: PGH003

    return our_game


async def add_or_update_owner(owner_json: dict | None) -> Owner | None:
    """Add or update an owner in the database.

    Args:
        owner_json (dict): The owner to add or update.

    Returns:
        Owner: The owner that was added or updated.
    """
    if not owner_json:
        return None

    defaults: dict[str, str] = {}
    if owner_json.get("name"):
        defaults["name"] = owner_json["name"]

    our_owner, created = await Owner.objects.aupdate_or_create(id=owner_json.get("id"), defaults=defaults)
    if created:
        logger.info("Added owner %s", our_owner.id)

    return our_owner


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
        defaults: dict[str, str] = {}
        if channel_json.get("displayName"):
            defaults["display_name"] = channel_json["displayName"]

        if channel_json.get("name"):
            defaults["name"] = channel_json["name"]
            defaults["twitch_url"] = f'https://www.twitch.tv/{channel_json["name"]}'

        our_channel, created = await Channel.objects.aupdate_or_create(twitch_id=channel_json["id"], defaults=defaults)
        if created:
            logger.info("Added channel %s", our_channel.twitch_id)

        channels.append(our_channel)

    return channels


async def add_benefit(benefit: dict, time_based_drop: TimeBasedDrop) -> None:
    """Add a benefit to the database.

    Args:
        benefit (dict): The benefit to add.
        time_based_drop (TimeBasedDrop): The time-based drop the benefit belongs to.
    """
    mappings: dict[str, str] = {
        "createdAt": "twitch_created_at",
        "entitlementLimit": "entitlement_limit",
        "imageAssetURL": "image_url",
        "isIosAvailable": "is_ios_available",
        "name": "name",
    }
    defaults: dict[str, str] = {new_key: benefit[key] for key, new_key in mappings.items() if benefit.get(key)}
    our_benefit, created = await Benefit.objects.aupdate_or_create(id=benefit["id"], defaults=defaults)
    if created:
        logger.info("Added benefit %s", our_benefit.id)

    if time_based_drop:
        await time_based_drop.benefits.aadd(our_benefit)  # type: ignore  # noqa: PGH003


async def add_drop_campaign(drop_campaign: dict | None) -> None:
    """Add a drop campaign to the database.

    Args:
        drop_campaign (dict): The drop campaign to add.
    """
    if not drop_campaign:
        return

    defaults: dict[str, str | Game | Owner] = {}

    owner: Owner | None = await get_owner(drop_campaign)

    if drop_campaign.get("game"):
        game: Game | None = await add_or_update_game(drop_campaign["game"], owner)
        if game:
            defaults["game"] = game

    mappings: dict[str, str] = {
        "accountLinkURL": "account_link_url",
        "description": "description",
        "detailsURL": "details_url",
        "endAt": "ends_at",
        "startAt": "starts_at",
        "imageURL": "image_url",
        "name": "name",
        "status": "status",
    }
    for key, new_key in mappings.items():
        if drop_campaign.get(key):
            defaults[new_key] = drop_campaign[key]

    our_drop_campaign, created = await DropCampaign.objects.aupdate_or_create(
        id=drop_campaign["id"],
        defaults=defaults,
    )
    if created:
        logger.info("Added drop campaign %s", our_drop_campaign.id)

    if drop_campaign.get("allow") and drop_campaign["allow"].get("channels"):
        channels: list[Channel] | None = await add_or_update_channels(drop_campaign["allow"]["channels"])
        if channels:
            for channel in channels:
                await channel.drop_campaigns.aadd(our_drop_campaign)

    await add_time_based_drops(drop_campaign, our_drop_campaign)


async def get_owner(drop_campaign: dict) -> Owner | None:
    """Get the owner of the drop campaign.

    Args:
        drop_campaign (dict): The drop campaign containing the owner.

    Returns:
        Owner: The owner of the drop campaign.
    """
    owner = None
    if drop_campaign.get("owner"):
        owner: Owner | None = await add_or_update_owner(drop_campaign["owner"])
    return owner


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
            logger.error("Not implemented: Add precondition drops to time-based drop, JSON: %s", time_based_drop)

        mappings: dict[str, str] = {
            "requiredSubs": "required_subs",
            "endAt": "ends_at",
            "name": "name",
            "requiredMinutesWatched": "required_minutes_watched",
            "startAt": "starts_at",
        }
        defaults: dict[str, str | DropCampaign] = {
            new_key: time_based_drop[key] for key, new_key in mappings.items() if time_based_drop.get(key)
        }
        if our_drop_campaign:
            defaults["drop_campaign"] = our_drop_campaign

        our_time_based_drop, created = await TimeBasedDrop.objects.aupdate_or_create(
            id=time_based_drop["id"],
            defaults=defaults,
        )
        if created:
            logger.info("Added time-based drop %s", our_time_based_drop.id)

        if time_based_drop.get("benefitEdges") and our_time_based_drop:
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
