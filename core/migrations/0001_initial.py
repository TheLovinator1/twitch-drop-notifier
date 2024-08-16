# Generated by Django 5.1 on 2024-08-16 02:38

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations: list[Operation] = [
        migrations.CreateModel(
            name="DropCampaign",
            fields=[
                ("created_at", models.DateTimeField(auto_created=True, null=True)),
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("modified_at", models.DateTimeField(auto_now=True, null=True)),
                ("account_link_url", models.URLField(null=True)),
                ("description", models.TextField(null=True)),
                ("details_url", models.URLField(null=True)),
                ("ends_at", models.DateTimeField(null=True)),
                ("starts_at", models.DateTimeField(null=True)),
                ("image_url", models.URLField(null=True)),
                ("name", models.TextField(null=True)),
                ("status", models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Game",
            fields=[
                ("twitch_id", models.TextField(primary_key=True, serialize=False)),
                ("game_url", models.URLField(default="https://www.twitch.tv/", null=True)),
                ("name", models.TextField(default="Game name unknown", null=True)),
                (
                    "box_art_url",
                    models.URLField(default="https://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg", null=True),
                ),
                ("slug", models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Owner",
            fields=[
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("name", models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={"unique": "A user with that username already exists."},
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name="username",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",  # noqa: E501
                        verbose_name="active",
                    ),
                ),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",  # noqa: E501
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Channel",
            fields=[
                ("twitch_id", models.TextField(primary_key=True, serialize=False)),
                ("display_name", models.TextField(default="Channel name unknown", null=True)),
                ("name", models.TextField(null=True)),
                ("twitch_url", models.URLField(default="https://www.twitch.tv/", null=True)),
                ("live", models.BooleanField(default=False)),
                ("drop_campaigns", models.ManyToManyField(related_name="channels", to="core.dropcampaign")),
            ],
        ),
        migrations.AddField(
            model_name="dropcampaign",
            name="game",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="drop_campaigns",
                to="core.game",
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="org",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="games",
                to="core.owner",
            ),
        ),
        migrations.CreateModel(
            name="RewardCampaign",
            fields=[
                ("created_at", models.DateTimeField(auto_created=True, null=True)),
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("modified_at", models.DateTimeField(auto_now=True, null=True)),
                ("name", models.TextField(null=True)),
                ("brand", models.TextField(null=True)),
                ("starts_at", models.DateTimeField(null=True)),
                ("ends_at", models.DateTimeField(null=True)),
                ("status", models.TextField(null=True)),
                ("summary", models.TextField(null=True)),
                ("instructions", models.TextField(null=True)),
                ("reward_value_url_param", models.TextField(null=True)),
                ("external_url", models.URLField(null=True)),
                ("about_url", models.URLField(null=True)),
                ("is_site_wide", models.BooleanField(null=True)),
                ("sub_goal", models.PositiveBigIntegerField(null=True)),
                ("minute_watched_goal", models.PositiveBigIntegerField(null=True)),
                ("image_url", models.URLField(null=True)),
                (
                    "game",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reward_campaigns",
                        to="core.game",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Reward",
            fields=[
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("name", models.TextField(null=True)),
                ("banner_image_url", models.URLField(null=True)),
                ("thumbnail_image_url", models.URLField(null=True)),
                ("earnable_until", models.DateTimeField(null=True)),
                ("redemption_instructions", models.TextField(null=True)),
                ("redemption_url", models.URLField(null=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rewards",
                        to="core.rewardcampaign",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TimeBasedDrop",
            fields=[
                ("created_at", models.DateTimeField(auto_created=True, null=True)),
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("modified_at", models.DateTimeField(auto_now=True, null=True)),
                ("required_subs", models.PositiveBigIntegerField(null=True)),
                ("ends_at", models.DateTimeField(null=True)),
                ("name", models.TextField(null=True)),
                ("required_minutes_watched", models.PositiveBigIntegerField(null=True)),
                ("starts_at", models.DateTimeField(null=True)),
                (
                    "drop_campaign",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drops",
                        to="core.dropcampaign",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Benefit",
            fields=[
                ("created_at", models.DateTimeField(auto_created=True, null=True)),
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("modified_at", models.DateTimeField(auto_now=True, null=True)),
                ("twitch_created_at", models.DateTimeField(null=True)),
                ("entitlement_limit", models.PositiveBigIntegerField(null=True)),
                ("image_url", models.URLField(null=True)),
                ("is_ios_available", models.BooleanField(null=True)),
                ("name", models.TextField(null=True)),
                (
                    "time_based_drop",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="benefits",
                        to="core.timebaseddrop",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Webhook",
            fields=[
                ("avatar", models.TextField(null=True)),
                ("channel_id", models.TextField(null=True)),
                ("guild_id", models.TextField(null=True)),
                ("id", models.TextField(primary_key=True, serialize=False)),
                ("name", models.TextField(null=True)),
                ("type", models.TextField(null=True)),
                ("token", models.TextField()),
                ("url", models.TextField()),
                ("seen_drops", models.ManyToManyField(related_name="seen_drops", to="core.dropcampaign")),
                (
                    "subscribed_live_games",
                    models.ManyToManyField(related_name="subscribed_live_games", to="core.game"),
                ),
                (
                    "subscribed_live_owners",
                    models.ManyToManyField(related_name="subscribed_live_owners", to="core.owner"),
                ),
                ("subscribed_new_games", models.ManyToManyField(related_name="subscribed_new_games", to="core.game")),
                (
                    "subscribed_new_owners",
                    models.ManyToManyField(related_name="subscribed_new_owners", to="core.owner"),
                ),
            ],
            options={
                "unique_together": {("id", "token")},
            },
        ),
    ]
