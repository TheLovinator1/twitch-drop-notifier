# Generated by Django 5.0.6 on 2024-07-01 15:17

import django.db.models.deletion
import django.db.models.functions.text
import simple_history.models
from django.conf import settings
from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: list[tuple[str, str]] = [
        ("twitch_app", "0002_game_image_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations: list[Operation] = [
        migrations.CreateModel(
            name="HistoricalDropBenefit",
            fields=[
                ("id", models.TextField(db_index=True)),
                ("created_at", models.DateTimeField(blank=True, null=True)),
                ("entitlement_limit", models.IntegerField(blank=True, null=True)),
                ("image_asset_url", models.URLField(blank=True, null=True)),
                ("is_ios_available", models.BooleanField(blank=True, null=True)),
                ("name", models.TextField(blank=True, null=True)),
                (
                    "added_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "modified_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="twitch_app.game",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "owner_organization",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="twitch_app.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical drop benefit",
                "verbose_name_plural": "historical drop benefits",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalDropCampaign",
            fields=[
                ("id", models.TextField(db_index=True)),
                ("account_link_url", models.URLField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                ("details_url", models.URLField(blank=True, null=True)),
                ("end_at", models.DateTimeField(blank=True, null=True)),
                ("image_url", models.URLField(blank=True, null=True)),
                ("name", models.TextField(blank=True, null=True)),
                ("start_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.TextField(blank=True, null=True)),
                (
                    "added_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "modified_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="twitch_app.game",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="twitch_app.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical drop campaign",
                "verbose_name_plural": "historical drop campaigns",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalGame",
            fields=[
                ("id", models.TextField(db_index=True)),
                ("slug", models.TextField(blank=True, null=True)),
                (
                    "twitch_url",
                    models.GeneratedField(  # type: ignore  # noqa: PGH003
                        db_persist=True,
                        expression=django.db.models.functions.text.Concat(
                            models.Value("https://www.twitch.tv/directory/category/"),
                            "slug",
                        ),
                        output_field=models.TextField(),
                    ),
                ),
                (
                    "image_url",
                    models.GeneratedField(  # type: ignore  # noqa: PGH003
                        db_persist=True,
                        expression=django.db.models.functions.text.Concat(
                            models.Value("https://static-cdn.jtvnw.net/ttv-boxart/"),
                            "id",
                            models.Value("_IGDB.jpg"),
                        ),
                        output_field=models.URLField(),
                    ),
                ),
                ("display_name", models.TextField(blank=True, null=True)),
                (
                    "added_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "modified_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical game",
                "verbose_name_plural": "historical games",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalTimeBasedDrop",
            fields=[
                ("id", models.TextField(db_index=True)),
                ("required_subs", models.IntegerField(blank=True, null=True)),
                ("end_at", models.DateTimeField(blank=True, null=True)),
                ("name", models.TextField(blank=True, null=True)),
                (
                    "required_minutes_watched",
                    models.IntegerField(blank=True, null=True),
                ),
                ("start_at", models.DateTimeField(blank=True, null=True)),
                (
                    "added_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "modified_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical time based drop",
                "verbose_name_plural": "historical time based drops",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalUser",
            fields=[
                ("id", models.TextField(db_index=True)),
                (
                    "added_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "modified_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical user",
                "verbose_name_plural": "historical users",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
