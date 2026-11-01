import typing

from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_nested.routers import NestedDefaultRouter, NestedSimpleRouter


def get_api_router_instance() -> typing.Union[DefaultRouter, SimpleRouter]:
    """
    Return a top-level router instance configured for the active environment.

    Selects ``DefaultRouter`` when ``settings.DEBUG`` is enabled (providing browsable
    API documentation and hyperlinked endpoints) or ``SimpleRouter`` in production.

    Returns:
        DefaultRouter | SimpleRouter: Configured top-level DRF router instance.
    """
    return DefaultRouter() if settings.DEBUG else SimpleRouter()


def get_nested_api_router_instance(
    parent_router: typing.Union[DefaultRouter, SimpleRouter],
    parent_prefix: str,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> typing.Union[NestedDefaultRouter, NestedSimpleRouter]:
    """
    Return a nested router instance configured for the active environment.

    Selects ``NestedDefaultRouter`` when ``settings.DEBUG`` is enabled (providing
    the browsable API root and format suffixes) or ``NestedSimpleRouter`` in
    production for lean, deterministic URL routing.

    Args:
        parent_router (SimpleRouter | DefaultRouter): The parent router instance
            that registered the top-level resource.
        parent_prefix (str): Prefix of the parent resource (e.g. 'customers').
        *args: Additional positional arguments forwarded to the nested router constructor.
        **kwargs: Additional keyword arguments (e.g. lookup='customer') forwarded
            to the nested router constructor.

    Returns:
        NestedDefaultRouter | NestedSimpleRouter: Configured nested DRF router instance.
    """
    router_class = NestedDefaultRouter if settings.DEBUG else NestedSimpleRouter
    return router_class(parent_router, parent_prefix, *args, **kwargs)
