from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeText
from django.utils.timesince import timesince
from django.utils.timezone import now

from core.models import Reward, RewardCampaign

register = template.Library()


@register.simple_tag
def render_campaign(campaign: RewardCampaign) -> SafeText:
    """Render the campaign HTML.

    Args:
        campaign: The campaign object.

    Returns:
        The rendered HTML string.
    """
    time_remaining = timesince(now(), campaign.ends_at)
    ends_in: str = f'{campaign.ends_at.strftime("%A %d %B %H:%M %Z")}' if campaign.ends_at else ""
    starts_in: str = f'{campaign.starts_at.strftime("%A %d %B %H:%M %Z")}' if campaign.starts_at else ""

    # Start building the HTML
    html: str = f"""
    <div class="card mb-4 shadow-sm" id="campaign-{campaign.id}">
        <div class="row g-0">
            <div class="col-md-2">
                <img src="{campaign.image_url}"
                     alt="{campaign.name}"
                     class="img-fluid rounded-start"
                     height="283"
                     width="212"
                     loading="lazy">
            </div>
            <div class="col-md-10">
                <div class="card-body">
                    <h2 class="card-title h5" id="#reward-{campaign.id}">
                        <a href="#campaign-{campaign.id}" class="plain-text-item">{campaign.name}</a>
                    </h2>
                    <p class="card-text text-muted">{campaign.summary}</p>
                    <p class="mb-2 text-muted">
                        Ends in: <abbr title="{starts_in} - {ends_in}">{time_remaining}</abbr>
                    </p>
                    <a href="{campaign.external_url}"
                       class="btn btn-primary"
                       target="_blank">Learn More</a>
    """

    # Add instructions if present
    if campaign.instructions:
        html += f"""
        <div class="mt-3">
            <h3 class="h6">Instructions</h3>
            <p>{campaign.instructions}</p>
        </div>
        """

    # Add rewards if present
    if campaign.rewards.exists():  # type: ignore  # noqa: PGH003
        html += """
        <div class="mt-3">
            <h3 class="h6">Rewards</h3>
            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-2">
        """
        for reward in campaign.rewards.all():  # type: ignore  # noqa: PGH003
            reward: Reward
            html += f"""
            <div class="col d-flex align-items-center position-relative">
                <img src="{reward.thumbnail_image_url}"
                     alt="{reward.name} reward image"
                     class="img-fluid rounded me-3"
                     height="50"
                     width="50"
                     loading="lazy">
                <div>
                    <strong>{reward.name}</strong>
                </div>
            </div>
            """
        html += "</div></div>"

    # Close the main divs
    html += """
                </div>
            </div>
        </div>
    </div>
    """

    return format_html(html)
