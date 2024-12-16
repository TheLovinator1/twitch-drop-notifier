# Generated by Django 5.1.4 on 2024-12-16 18:28
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    """This migration alters the options of the User model to order by username."""

    dependencies: list[tuple[str, str]] = [
        ("core", "0001_initial"),
    ]

    operations: list[Operation] = [
        migrations.AlterModelOptions(
            name="user",
            options={"ordering": ["username"]},
        ),
    ]
