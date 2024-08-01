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

from twitch_app.models import (
    Allow,
    Benefit,
    BenefitEdge,
    Channel,
    DropCampaign,
    Game,
    Image,
    Owner,
    Reward,
    RewardCampaign,
    TimeBasedDrop,
    UnlockRequirements,
)

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


async def add_or_get_game(json_data: dict, name: str) -> tuple[Game | None, bool]:
    """Add or get Game from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.
        name (str): Name of the drop campaign.

    Returns:
        tuple[Game | None, bool]: Game instance and whether it was created.
    """
    if not json_data:
        logger.warning("%s is not for a game?", name)
        return None, False

    game, created = await Game.objects.aupdate_or_create(
        id=json_data["id"],
        defaults={
            "slug": json_data.get("slug"),
            "display_name": json_data.get("displayName"),
            "typename": json_data.get("__typename"),
        },
    )

    return game, created


async def add_or_get_owner(json_data: dict, name: str) -> tuple[Owner | None, bool]:
    """Add or get Owner from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.
        name (str): Name of the drop campaign.

    Returns:
        Owner: Owner instance.
    """
    if not json_data:
        logger.warning("Owner data is missing for %s", name)
        return None, False

    owner, created = await Owner.objects.aupdate_or_create(
        id=json_data["id"],
        defaults={
            "display_name": json_data.get("name"),
            "typename": json_data.get("__typename"),
        },
    )

    return owner, created


async def add_or_get_allow(json_data: dict, name: str) -> tuple[Allow | None, bool]:
    """Add or get Allow from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.
        name (str): Name of the drop campaign.

    Returns:
        Allow: Allow instance.
    """
    if not json_data:
        logger.warning("Allow data is missing for %s", name)
        return None, False

    allow, created = await Allow.objects.aupdate_or_create(
        is_enabled=json_data.get("isEnabled"),
        typename=json_data.get("__typename"),
    )

    return allow, created


async def add_or_get_time_based_drops(
    time_based_drops_data: list[dict] | None,
    owner: Owner | None,
    game: Game | None,
) -> list[TimeBasedDrop]:
    """Handle TimeBasedDrops from JSON data.

    Args:
        time_based_drops_data (list[dict]): Time based drops data from JSON.
        owner (Owner): Owner instance.
        game (Game): Game instance.

    Returns:
        list[TimeBasedDrop]: TimeBasedDrop instances.
    """
    time_based_drops: list[TimeBasedDrop] = []

    if not time_based_drops_data:
        logger.warning("No time based drops found")
        return []

    for time_based_drop_data in time_based_drops_data:
        time_based_drop, _ = await TimeBasedDrop.objects.aupdate_or_create(
            id=time_based_drop_data["id"],
            defaults={
                "created_at": time_based_drop_data.get("createdAt"),
                "entitlement_limit": time_based_drop_data.get("entitlementLimit"),
                "image_asset_url": time_based_drop_data.get("imageAssetURL"),
                "is_ios_available": time_based_drop_data.get("isIosAvailable"),
                "name": time_based_drop_data.get("name"),
                "owner_organization": owner,
                "game": game,
                "typename": time_based_drop_data.get("__typename"),
            },
        )

        benefit_edges_data: list[dict] = time_based_drop_data.get("benefitEdges", [])
        for benefit_edge_data in benefit_edges_data:
            benefit_data: dict = benefit_edge_data.get("benefit", {})
            benefit, _ = await Benefit.objects.aupdate_or_create(
                id=benefit_data["id"],
                defaults={
                    "created_at": benefit_data.get("createdAt"),
                    "entitlement_limit": benefit_data.get("entitlementLimit"),
                    "image_asset_url": benefit_data.get("imageAssetURL"),
                    "is_ios_available": benefit_data.get("isIosAvailable"),
                    "name": benefit_data.get("name"),
                    "owner_organization": owner,
                    "game": game,
                    "typename": benefit_data.get("__typename"),
                },
            )

            await BenefitEdge.objects.aupdate_or_create(
                benefit=benefit,
                defaults={
                    "entitlement_limit": benefit_edge_data.get("entitlementLimit"),
                    "typename": benefit_edge_data.get("__typename"),
                },
            )

        time_based_drops.append(time_based_drop)

    return time_based_drops


async def add_or_get_drop_campaign(
    drop_campaign_data: dict,
    game: Game | None,
    owner: Owner | None,
) -> tuple[DropCampaign | None, bool]:
    """Handle DropCampaign from JSON data.

    Args:
        drop_campaign_data (dict): Drop campaign data from JSON.
        game (Game): Game instance.
        owner (Owner): Owner instance.

    Returns:
        tuple[DropCampaign, bool]: DropCampaign instance and whether it was created.
    """
    if not drop_campaign_data:
        logger.warning("No drop campaign data found")
        return None, False

    drop_campaign, _ = await DropCampaign.objects.aupdate_or_create(
        id=drop_campaign_data["id"],
        defaults={
            # "allow": allow, # We add this later
            "account_link_url": drop_campaign_data.get("accountLinkURL"),
            "description": drop_campaign_data.get("description"),
            "details_url": drop_campaign_data.get("detailsURL"),
            "ends_at": drop_campaign_data.get("endAt"),
            # event_based_drops =  ???? # TODO(TheLovinator): Find out what this is  # noqa: TD003
            "game": game,
            "image_url": drop_campaign_data.get("imageURL"),
            "name": drop_campaign_data.get("name"),
            "owner": owner,
            "starts_at": drop_campaign_data.get("startAt"),
            "status": drop_campaign_data.get("status"),
            # "time_based_drops": time_based_drops, # We add this later
            "typename": drop_campaign_data.get("__typename"),
        },
    )

    return drop_campaign, True


async def add_or_get_channel(json_data: dict) -> tuple[Channel | None, bool]:
    """Add or get Channel from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.

    Returns:
        tuple[Channel | None, bool]: Channel instance and whether it was created.
    """
    if not json_data:
        logger.warning("Channel data is missing")
        return None, False

    channel, created = await Channel.objects.aupdate_or_create(
        id=json_data["id"],
        defaults={
            "display_name": json_data.get("displayName"),
            "name": json_data.get("name"),
            "typename": json_data.get("__typename"),
        },
    )

    return channel, created


async def add_drop_campaign(json_data: dict) -> None:
    """Add data from JSON to the database."""
    # Get the data from the JSON
    user_data: dict = json_data.get("data", {}).get("user", {})
    drop_campaign_data: dict = user_data.get("dropCampaign", {})

    # Add or get Game
    game_data: dict = drop_campaign_data.get("game", {})
    game, _ = await add_or_get_game(json_data=game_data, name=drop_campaign_data.get("name", "Unknown Drop Campaign"))

    # Add or get Owner
    owner_data: dict = drop_campaign_data.get("owner", {})
    owner, _ = await add_or_get_owner(
        json_data=owner_data,
        name=drop_campaign_data.get("name", "Unknown Drop Campaign"),
    )

    # Add or get Allow
    allow_data: dict = drop_campaign_data.get("allow", {})
    allow, _ = await add_or_get_allow(
        json_data=allow_data,
        name=drop_campaign_data.get("name", "Unknown Drop Campaign"),
    )

    # Add channels to Allow
    if allow:
        channel_data: list[dict] = allow_data.get("channels", [])

        if channel_data:
            for json_channel in channel_data:
                channel, _ = await add_or_get_channel(json_channel)
                if channel:
                    await allow.channels.aadd(channel)

    # Add or get TimeBasedDrops
    time_based_drops_data = drop_campaign_data.get("timeBasedDrops", [])
    time_based_drops: list[TimeBasedDrop] = await add_or_get_time_based_drops(time_based_drops_data, owner, game)

    # Add or get DropCampaign
    drop_campaign, _ = await add_or_get_drop_campaign(
        drop_campaign_data=drop_campaign_data,
        game=game,
        owner=owner,
    )
    if drop_campaign:
        drop_campaign.allow = allow
        await drop_campaign.time_based_drops.aset(time_based_drops)
        await drop_campaign.asave()

        logger.info("Added Drop Campaign: %s", drop_campaign.name or "Unknown Drop Campaign")


async def add_or_get_image(json_data: dict) -> tuple[Image | None, bool]:
    """Add or get Image from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.

    Returns:
        tuple[Image | None, bool]: Image instance and whether it was created.
    """
    # TODO(TheLovinator): We should download the image and store it locally  # noqa: TD003
    if not json_data:
        logger.warning("Image data is missing")
        return None, False

    if not json_data.get("image1xURL"):
        logger.warning("Image URL is missing")
        return None, False

    image, created = await Image.objects.aupdate_or_create(
        image1_x_url=json_data.get("image1xURL"),
        defaults={
            "typename": json_data.get("__typename"),
        },
    )

    return image, created


async def add_or_get_rewards(json_data: dict) -> list[Reward]:
    """Add or get Rewards from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.

    Returns:
        list[Reward]: Reward instances
    """
    rewards: list[Reward] = []

    if not json_data:
        logger.warning("No rewards found")
        return []

    if "rewards" not in json_data:
        logger.warning("No rewards found")
        return []

    rewards_json: list[dict] = json_data.get("rewards", [])
    for reward_data in rewards_json:
        # Add or get bannerImage
        banner_image_data: dict = reward_data.get("bannerImage", {})
        if banner_image_data:
            banner_image, _ = await sync_to_async(Image.objects.get_or_create)(
                image1_x_url=banner_image_data["image1xURL"],
                defaults={"typename": banner_image_data["__typename"]},
            )

        # Add or get thumbnailImage
        thumbnail_image_data = reward_data.get("thumbnailImage", {})
        if thumbnail_image_data:
            thumbnail_image, _ = await sync_to_async(Image.objects.get_or_create)(
                image1_x_url=thumbnail_image_data["image1xURL"],
                defaults={"typename": thumbnail_image_data["__typename"]},
            )

        # Convert earnableUntil to a datetime object
        earnable_until: str | None = reward_data.get("earnableUntil")
        earnable_until_date: datetime | None = None
        if earnable_until:
            earnable_until_date = datetime.fromisoformat(earnable_until.replace("Z", "+00:00"))

        reward, _ = await sync_to_async(Reward.objects.get_or_create)(
            id=reward_data["id"],
            defaults={
                "name": reward_data.get("name"),
                "banner_image": banner_image,
                "thumbnail_image": thumbnail_image,
                "earnable_until": earnable_until_date,
                "redemption_instructions": reward_data.get("redemptionInstructions"),
                "redemption_url": reward_data.get("redemptionURL"),
                "typename": reward_data.get("__typename"),
            },
        )
        rewards.append(reward)

    return rewards


async def add_or_get_unlock_requirements(json_data: dict) -> tuple[UnlockRequirements | None, bool]:
    """Add or get UnlockRequirements from JSON data.

    Args:
        json_data (dict): JSON data to add to the database.

    Returns:
        tuple[UnlockRequirements | None, bool]: UnlockRequirements instance and whether it was created.
    """
    if not json_data:
        logger.warning("Unlock Requirements data is missing")
        return None, False

    unlock_requirements, created = await UnlockRequirements.objects.aget_or_create(
        subs_goal=json_data["subsGoal"],
        defaults={
            "minute_watched_goal": json_data["minuteWatchedGoal"],
            "typename": json_data["__typename"],
        },
    )

    return unlock_requirements, created


async def add_reward_campaign(json_data: dict) -> None:
    """Add data from JSON to the database.

    Args:
        json_data (dict): JSON data to add to the database.

    Returns:
        None: No return value.
    """
    campaign_data: list[dict] = json_data["data"]["rewardCampaignsAvailableToUser"]
    for campaign in campaign_data:
        # Add or get Game
        game_data: dict = campaign.get("game", {})
        game, _ = await add_or_get_game(json_data=game_data, name=campaign.get("name", "Unknown Reward Campaign"))

        # Add or get Image
        image_data: dict = campaign.get("image", {})
        image, _ = await add_or_get_image(json_data=image_data)

        # Add or get Rewards
        rewards: list[Reward] = await add_or_get_rewards(campaign)

        # Add or get Unlock Requirements
        unlock_requirements_data: dict = campaign["unlockRequirements"]
        unlock_requirements, _ = await add_or_get_unlock_requirements(unlock_requirements_data)

        # Create Reward Campaign
        reward_campaign, _ = await RewardCampaign.objects.aget_or_create(
            id=campaign["id"],
            defaults={
                "name": campaign.get("name"),
                "brand": campaign.get("brand"),
                "starts_at": campaign.get("startsAt"),
                "ends_at": campaign.get("endsAt"),
                "status": campaign.get("status"),
                "summary": campaign.get("summary"),
                "instructions": campaign.get("instructions"),
                "external_url": campaign.get("externalURL"),
                "reward_value_url_param": campaign.get("rewardValueURLParam"),
                "about_url": campaign.get("aboutURL"),
                "is_sitewide": campaign.get("isSitewide"),
                "game": game,
                "unlock_requirements": unlock_requirements,
                "image": image,
                # "rewards": rewards, # We add this later
                "typename": campaign.get("__typename"),
            },
        )

        # Add Rewards to the Campaign
        for reward in rewards:
            await reward_campaign.rewards.aadd(reward)

        await reward_campaign.asave()


class Command(BaseCommand):
    help = "Scrape Twitch Drops Campaigns with login using Firefox"

    async def run(  # noqa: PLR6301, C901
        self,
        playwright: Playwright,
    ) -> list[dict[str, typing.Any]]:
        args: list[str] = []

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

            if "dropCampaign" in campaign.get("data", {}).get("user", {}):
                if not campaign["data"]["user"]["dropCampaign"]:
                    logger.warning("No drop campaign found")
                    continue
                await add_drop_campaign(campaign)

            if "dropCampaigns" in campaign.get("data", {}).get("user", {}):
                for drop_campaign in campaign["data"]["user"]["dropCampaigns"]:
                    await add_drop_campaign(drop_campaign)

        return json_data

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ARG002, ANN003
        asyncio.run(self.run_with_playwright())

    async def run_with_playwright(self) -> None:
        async with async_playwright() as playwright:
            await self.run(playwright)


if __name__ == "__main__":
    Command().handle()
