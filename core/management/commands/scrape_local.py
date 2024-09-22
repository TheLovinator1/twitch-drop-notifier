import asyncio
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from core.management.commands.scrape_twitch import process_json_data

logger: logging.Logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape local files."

    def handle(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, ARG002, PLR6301
        """Scrape local files.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        dir_name = Path("json2")
        for num, file in enumerate(Path(dir_name).rglob("*.json")):
            logger.info("Processing %s", file)

            with file.open(encoding="utf-8") as f:
                try:
                    load_json = json.load(f)
                except json.JSONDecodeError:
                    logger.exception("Failed to load JSON from %s", file)
                    continue
                asyncio.run(main=process_json_data(num=num, campaign=load_json, local=True))


if __name__ == "__main__":
    Command().handle()
