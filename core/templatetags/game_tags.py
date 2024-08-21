from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeText
from django.utils.timesince import timesince
from django.utils.timezone import now

from core.models import Benefit, DropCampaign, Game, TimeBasedDrop

register = template.Library()


@register.simple_tag
def render_game_card(game: Game) -> SafeText:
    """Render the game card HTML.

    Args:
        game: The game object.

    Returns:
        The rendered HTML string.
    """
    box_art_url: str = game.box_art_url or "https://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg"
    name: str = game.name or "Game name unknown"
    slug: str = game.slug or "game-name-unknown"
    drop_campaigns: list[DropCampaign] = game.drop_campaigns.all()  # type: ignore  # noqa: PGH003
    return format_html(
        """
    <div class="card mb-4 shadow-sm">
        <div class="row g-0">
            <div class="col-md-2">
                <img src="{}" alt="{} box art" class="img-fluid rounded-start" height="283" width="212" loading="lazy">
            </div>
            <div class="col-md-10">
                <div class="card-body">
                    <h2 class="card-title h5">
                        <a href="https://www.twitch.tv/directory/category/{}" class="text-decoration-none">{}</a>
                    </h2>
                    <div class="mt-auto">
                        <!-- Insert nice buttons -->
                    </div>
                    {}
                </div>
            </div>
        </div>
    </div>
    """,
        box_art_url,
        name,
        slug,
        name,
        render_campaigns(drop_campaigns),
    )


def render_campaigns(campaigns: list[DropCampaign]) -> SafeText:
    """Render the campaigns HTML.

    Args:
        campaigns: The list of campaigns.

    Returns:
        The rendered HTML string.
    """
    campaign_html: str = ""
    for campaign in campaigns:
        if campaign.details_url == campaign.account_link_url:
            link_html: SafeText = format_html(
                '<a href="{}" class="text-decoration-none">Details</a>',
                campaign.details_url,
            )
        else:
            link_html: SafeText = format_html(
                '<a href="{}" class="text-decoration-none">Details</a> | <a href="{}" class="text-decoration-none">Link Account</a>',  # noqa: E501
                campaign.details_url,
                campaign.account_link_url,
            )

        remaining_time: str = timesince(now(), campaign.ends_at) if campaign.ends_at else "Failed to calculate time"
        starts_at: str = campaign.starts_at.strftime("%A %d %B %H:%M") if campaign.starts_at else ""
        ends_at: str = campaign.ends_at.strftime("%A %d %B %H:%M") if campaign.ends_at else ""
        drops: list[TimeBasedDrop] = campaign.drops.all()  # type: ignore  # noqa: PGH003
        campaign_html += format_html(
            """
        <div class="mt-3">
            {}
            <p class="mb-2 text-muted">Ends in: <abbr title="{} - {}">{}</abbr></p>
            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3">
                {}
            </div>
        </div>
        """,
            link_html,
            starts_at,
            ends_at,
            remaining_time,
            render_drops(drops),
        )

    return format_html(campaign_html)


def render_drops(drops: list[TimeBasedDrop]) -> SafeText:
    """Render the drops HTML.

    Args:
        drops: The list of drops.

    Returns:
        The rendered HTML string.
    """
    drop_html: str = ""
    for drop in drops:
        benefits: list[Benefit] = drop.benefits.all()  # type: ignore  # noqa: PGH003
        for benefit in benefits:
            image_url: str = benefit.image_url or "https://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg"
            name: str = benefit.name or "Drop name unknown"
            drop_html += format_html(
                """
            <div class="col d-flex align-items-center position-relative">
                <img src="{}" alt="{} drop image" class="img-fluid rounded me-3" height="50" width="50" loading="lazy">
                {}
            </div>
            """,
                image_url,
                name,
                name,
            )
    return format_html(drop_html)
