import typing

from core.utils.app_settings import BaseSettings
from core.utils.app_settings.types import Constance


class CRMSettings(BaseSettings):
    """
    App settings and runtime configuration for CRM application.
    """

    SETTINGS_KEY = "CORE_CRM_SETTINGS"

    MAX_DOCUMENT_UPLOAD_SIZE = Constance(
        default=10 * 1024 * 1024,  # 10 MB
        data_type=int,
        help_text="Maximum allowed file size in bytes for uploaded KYC identification documents.",
    )
    OCR_NATIVE_TEXT_MIN_CHARS = Constance(
        default=50,
        data_type=int,
        help_text="Minimum character count in native PDF text layer to prefer digital text over OCR.",
    )

    def get_crm_config(self) -> dict[str, typing.Any]:
        """
        Retrieve database-backed Configuration object for crm_configuration,
        falling back to Constance app_settings and built-in defaults.

        Returns:
            dict[str, typing.Any]: Configuration dictionary with resolved settings.
        """
        defaults = {
            "max_document_upload_size": self.MAX_DOCUMENT_UPLOAD_SIZE,
            "ocr_native_text_min_chars": self.OCR_NATIVE_TEXT_MIN_CHARS,
        }
        try:
            from core.apps.configurations import (  # noqa: PLC0415
                get_configuration_model,
            )

            Configuration = get_configuration_model()
            config_details = Configuration.get_configuration(
                interface_type="crm_configuration"
            )
            if isinstance(config_details, dict):
                return {**defaults, **config_details}
        except Exception:
            pass
        return defaults

    @property
    def max_document_upload_size(self) -> int:
        """
        Get max document upload size from database Configuration or Constance.

        Returns:
            int: Maximum document size in bytes.
        """
        return int(
            self.get_crm_config().get(
                "max_document_upload_size", self.MAX_DOCUMENT_UPLOAD_SIZE
            )
        )

    @property
    def ocr_native_text_min_chars(self) -> int:
        """
        Get min native text chars from database Configuration or Constance.

        Returns:
            int: Minimum character threshold.
        """
        return int(
            self.get_crm_config().get(
                "ocr_native_text_min_chars", self.OCR_NATIVE_TEXT_MIN_CHARS
            )
        )
