"""
URL resolution and route-building utilities for explicit API registration.

Transforms declarative URL mappings (file_path, version, api_path) into
versioned Django URLResolver instances without relying on automatic module discovery.
"""

import typing

from django.urls import URLResolver, include, path

URL_ENTRY_TYPE: typing.TypeAlias = (
    tuple[str, typing.Optional[str], str] | tuple[str, str]
)
URL_MAPPING_TYPE: typing.TypeAlias = typing.Sequence[URL_ENTRY_TYPE]


def resolve_and_build_paths(
    url_mapping: URL_MAPPING_TYPE,
    prefix: typing.Optional[str] = "api",
) -> list[URLResolver]:
    """
    Construct versioned Django URLResolver patterns from an explicit URL mapping sequence.

    Each mapping entry defines:
    - ``file_path`` (str): Dotted Python import path to the target `urls` module.
    - ``version`` (str | None): API version segment (e.g. 'v1'). Defaults to 'v1' if omitted or None.
    - ``api_path`` (str): Resource path segment (e.g. 'users', 'customers').

    Normalizes slashes and ensures each included resolver ends with a trailing slash
    so sub-routes concatenate cleanly.

    Args:
        url_mapping (URL_MAPPING_TYPE): Sequence of URL mapping tuples.
        prefix (str, optional): Optional top-level URL prefix. Defaults to 'api'.

    Returns:
        list[URLResolver]: List of Django URLResolver objects.

    Raises:
        ValueError: If any mapping entry does not match the expected 2-tuple or 3-tuple format.
    """
    url_patterns: list[URLResolver] = []

    for entry in url_mapping:
        if len(entry) == 3:
            file_path, version, api_path = entry
        elif len(entry) == 2:
            file_path, api_path = entry
            version = "v1"
        else:
            raise ValueError(f"Invalid URL mapping entry, got: {entry!r}")

        clean_prefix = prefix.strip("/") if prefix else ""
        clean_path = api_path.strip("/")
        clean_version = (version or "v1").strip("/")

        parts = [p for p in (clean_prefix, clean_path, clean_version) if p]
        route = f"{'/'.join(parts)}/" if parts else ""

        mapping = path(route, include(file_path))
        url_patterns.append(mapping)

    return url_patterns
