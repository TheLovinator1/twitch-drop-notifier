# Generated by Django 5.0.6 on 2024-07-01 15:44

import auto_prefetch
import django.db.models.deletion
import django.db.models.manager
from django.db import migrations
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: list[tuple[str, str]] = [
        ("twitch_app", "0005_alter_dropbenefit_options_alter_dropcampaign_options_and_more"),
    ]

    operations: list[Operation] = [
        migrations.AlterModelOptions(
            name="dropbenefit",
            options={
                "base_manager_name": "prefetch_manager",
                "ordering": ("name",),
                "verbose_name": "Drop Benefit",
                "verbose_name_plural": "Drop Benefits",
            },
        ),
        migrations.AlterModelOptions(
            name="dropcampaign",
            options={
                "base_manager_name": "prefetch_manager",
                "ordering": ("name",),
                "verbose_name": "Drop Campaign",
                "verbose_name_plural": "Drop Campaigns",
            },
        ),
        migrations.AlterModelOptions(
            name="game",
            options={
                "base_manager_name": "prefetch_manager",
                "ordering": ("display_name",),
                "verbose_name": "Game",
                "verbose_name_plural": "Games",
            },
        ),
        migrations.AlterModelOptions(
            name="organization",
            options={
                "base_manager_name": "prefetch_manager",
                "ordering": ("name",),
                "verbose_name": "Organization",
                "verbose_name_plural": "Organizations",
            },
        ),
        migrations.AlterModelOptions(
            name="timebaseddrop",
            options={
                "base_manager_name": "prefetch_manager",
                "ordering": ("name",),
                "verbose_name": "Time-Based Drop",
                "verbose_name_plural": "Time-Based Drops",
            },
        ),
        migrations.AlterModelManagers(
            name="dropbenefit",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name="dropcampaign",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name="game",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name="organization",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name="timebaseddrop",
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterField(
            model_name="dropbenefit",
            name="game",
            field=auto_prefetch.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="twitch_app.game"),
        ),
        migrations.AlterField(
            model_name="dropbenefit",
            name="owner_organization",
            field=auto_prefetch.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="twitch_app.organization"),
        ),
        migrations.AlterField(
            model_name="dropcampaign",
            name="game",
            field=auto_prefetch.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="drop_campaigns",
                to="twitch_app.game",
            ),
        ),
        migrations.AlterField(
            model_name="dropcampaign",
            name="owner",
            field=auto_prefetch.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="drop_campaigns",
                to="twitch_app.organization",
            ),
        ),
        migrations.AlterField(
            model_name="historicaldropbenefit",
            name="game",
            field=auto_prefetch.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="twitch_app.game",
            ),
        ),
        migrations.AlterField(
            model_name="historicaldropbenefit",
            name="owner_organization",
            field=auto_prefetch.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="twitch_app.organization",
            ),
        ),
        migrations.AlterField(
            model_name="historicaldropcampaign",
            name="game",
            field=auto_prefetch.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="twitch_app.game",
            ),
        ),
        migrations.AlterField(
            model_name="historicaldropcampaign",
            name="owner",
            field=auto_prefetch.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="twitch_app.organization",
            ),
        ),
    ]
