from typing import TYPE_CHECKING

import pytest
from django.test import Client
from django.urls import reverse

if TYPE_CHECKING:
    from django.http import HttpResponse


@pytest.mark.django_db
def test_index_view(client: Client) -> None:
    """Test index view."""
    url: str = reverse(viewname="core:index")
    response: HttpResponse = client.get(url)
    assert response.status_code == 200
