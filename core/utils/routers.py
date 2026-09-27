import typing

from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter


def get_api_router_instance() -> typing.Union[DefaultRouter, SimpleRouter]:
    """
    Get api router for router's across application
    """
    api_router = SimpleRouter()
    if settings.DEBUG:
        api_router = DefaultRouter()

    return api_router
