from __future__ import annotations

import logging

from django.views.generic import ListView

from twitch_app.models import (
    Game,
)

logger: logging.Logger = logging.getLogger(__name__)


class GameView(ListView):
    model = Game
    template_name: str = "games.html"
    context_object_name: str = "games"
    paginate_by = 100
