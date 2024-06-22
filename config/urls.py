from django.contrib import admin
from django.urls import include, path
from django.urls.resolvers import URLResolver

app_name: str = "config"

urlpatterns: list[URLResolver] = [
    path(route="admin/", view=admin.site.urls),
    path(route="", view=include(arg="core.urls")),
]
