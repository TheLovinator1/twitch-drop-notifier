"""Tests for the views in the core app."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.http import HttpResponse
from django.urls import reverse

if TYPE_CHECKING:
    from django.test import Client
    from django.test.client import _MonkeyPatchedWSGIResponse  # type: ignore[import]


@pytest.mark.django_db
def test_index_view(client: Client) -> None:
    """Test index view."""
    url: str = reverse(viewname="core:index")
    response: _MonkeyPatchedWSGIResponse = client.get(url)

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
