# Generated by Django 5.1 on 2024-09-15 19:40
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: list[tuple[str, str]] = [
        ("core", "0004_alter_dropcampaign_name_alter_game_box_art_url_and_more"),
    ]

    operations: list[Operation] = [
        migrations.AlterModelOptions(
            name="benefit",
            options={"ordering": ["-twitch_created_at"]},
        ),
        migrations.AlterModelOptions(
            name="dropcampaign",
            options={"ordering": ["ends_at"]},
        ),
        migrations.AlterModelOptions(
            name="reward",
            options={"ordering": ["-earnable_until"]},
        ),
        migrations.AlterModelOptions(
            name="rewardcampaign",
            options={"ordering": ["-starts_at"]},
        ),
        migrations.AlterModelOptions(
            name="timebaseddrop",
            options={"ordering": ["required_minutes_watched"]},
        ),
    ]
