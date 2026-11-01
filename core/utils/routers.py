import typing

from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_nested.routers import NestedDefaultRouter, NestedSimpleRouter


def get_api_router_instance() -> typing.Union[DefaultRouter, SimpleRouter]:
    """
    Get api router for router's across application
    """
    api_router = SimpleRouter()
    if settings.DEBUG:
        api_router = DefaultRouter()

    return api_router


def get_nested_api_router_instance(
    parent_router,
) -> typing.Union[NestedDefaultRouter, NestedSimpleRouter]:
    """
    Get api router for router's across application
    """
    api_router = NestedSimpleRouter(parent_router)
    if settings.DEBUG:
        api_router = NestedDefaultRouter(parent_router)

    return api_router
