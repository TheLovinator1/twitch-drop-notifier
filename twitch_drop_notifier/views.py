from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.template import loader
from django.views.decorators.http import require_GET


def index(request: HttpRequest) -> HttpResponse:
    """/ index page.

    Args:
        request: The request.

    Returns:
        HttpResponse: The response.
    """
    template = loader.get_template(template_name="index.html")
    context = {}
    return HttpResponse(content=template.render(context, request))


robots_txt_content = """User-agent: *
Allow: /
"""


@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:  # noqa: ARG001
    """robots.txt page."""
    return HttpResponse(robots_txt_content, content_type="text/plain")


@require_GET
def contact(request: HttpRequest) -> HttpResponse:
    """/contact page.

    Args:
        request: The request.

    Returns:
        HttpResponse: The response.
    """
    template = loader.get_template(template_name="contact.html")
    context = {}
    return HttpResponse(content=template.render(context, request))


@require_GET
def privacy(request: HttpRequest) -> HttpResponse:
    """/privacy page.

    Args:
        request: The request.

    Returns:
        HttpResponse: The response.
    """
    template = loader.get_template(template_name="privacy.html")
    context = {}
    return HttpResponse(content=template.render(context, request))


@require_GET
def terms(request: HttpRequest) -> HttpResponse:
    """/terms page.

    Args:
        request: The request.

    Returns:
        HttpResponse: The response.
    """
    template = loader.get_template(template_name="terms.html")
    context = {}
    return HttpResponse(content=template.render(context, request))
