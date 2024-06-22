from typing import TYPE_CHECKING

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse

if TYPE_CHECKING:
    from django.http import HttpResponse


@pytest.fixture()
def factory() -> RequestFactory:
    """Factory for creating requests."""
    return RequestFactory()


@pytest.mark.django_db()
def test_index_view(client: Client) -> None:
    """Test index view."""
    url: str = reverse(viewname="core:index")
    response: HttpResponse = client.get(url)
    assert response.status_code == 200
