"""
Centralized UI labels with database configuration and humanized fallback.

Resolution Priority:
1. Backend view/context overrides (explicit `labels={...}` dict).
2. Database-backed `Configuration` (<module>_template_label) for the active project language.
3. Humanized title-case fallback for unregistered keys (e.g. `sign_in` -> `Sign In`).
"""

import logging
from typing import Any

from django.conf import settings

from core.apps.configurations import get_configuration_model

LOGGER = logging.getLogger(__name__)


def get_current_ui_language() -> str:
    """
    Determine the project-wide UI language using settings.LANGUAGE_CODE.
    """
    return getattr(settings, "LANGUAGE_CODE", "en")


def extract_label_for_language(value: Any, language: str) -> Any:
    """
    Extract localized string from a language dict, falling back only to 'en'.
    """
    if isinstance(value, dict):
        return value.get(language, value.get("en"))
    return value


def get_db_template_labels(
    interface_type: str = "users_template_label",
    language: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve template labels from the Configuration database table or cache.
    Extracts labels for the target language.

    If database is unreachable, unmigrated, or configuration is not found,
    smoothly falls back to an empty dictionary so humanized fallbacks apply.
    """
    if not language:
        language = get_current_ui_language()

    try:
        Configuration = get_configuration_model()
        config_details = Configuration.get_configuration(interface_type)

        if isinstance(config_details, dict):
            labels_source = config_details.get("labels", config_details)
            if isinstance(labels_source, dict):
                return {
                    k: extract_label_for_language(v, language)
                    for k, v in labels_source.items()
                }
    except Exception as exc:
        LOGGER.debug(
            "Could not load database configuration '%s' (fallback to humanized labels): %s",
            interface_type,
            exc,
        )

    return {}


class LabelDict(dict):
    """
    Transparent dictionary proxy for template labels.

    Priority:
    1. Custom backend-provided label (if present in backend dict).
    2. Database-backed / cached label (from defaults).
    3. Humanized fallback based on key name if not found.
    """

    def __init__(
        self,
        backend_labels: dict[str, Any] | None = None,
        defaults: dict[str, Any] | None = None,
    ):
        super().__init__()
        self.defaults = defaults or {}
        if backend_labels:
            if isinstance(backend_labels, LabelDict):
                self.update(backend_labels)
            elif isinstance(backend_labels, dict):
                self.update({k: v for k, v in backend_labels.items() if v is not None})

    def __getitem__(self, key: str) -> Any:
        if key in self:
            return super().__getitem__(key)
        if key in self.defaults:
            return self.defaults[key]
        return key.replace("_", " ").title()

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key in self:
            return super().get(key)
        if key in self.defaults:
            return self.defaults[key]
        return default if default is not None else key.replace("_", " ").title()


def get_default_labels(language: str | None = None) -> LabelDict:
    """Return a fresh LabelDict with database defaults or humanized fallback."""
    return resolve_labels(language=language)


def resolve_labels(
    backend_labels: Any = None,
    interface_type: str = "users_template_label",
    language: str | None = None,
) -> LabelDict:
    """
    Resolve template labels with the following priority:
    1. Explicit backend view/context overrides (`backend_labels`).
    2. Database-backed / cached `Configuration` (<module>_template_label) for the current language.
    3. Humanized fallback based on key name if not found.
    """
    if isinstance(backend_labels, LabelDict):
        return backend_labels

    if not language:
        language = get_current_ui_language()

    db_labels = get_db_template_labels(interface_type=interface_type, language=language)
    custom_labels = backend_labels if isinstance(backend_labels, dict) else None

    return LabelDict(backend_labels=custom_labels, defaults=db_labels)
