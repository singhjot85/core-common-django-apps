"""
Asynchronous Celery and Celery Beat cron tasks for CRM Customer Identifications.

TODO: Document scanning is a Celery Beat cron-scheduled batch task (`process_unverified_identifications_cron`)
rather than a per-upload manual trigger. Once Celery Beat is deployed and configured in the project,
periodic batch polling will process pending records automatically on a schedule.
"""

import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

from core.apps.crm import get_customer_identification_model
from core.apps.crm.constants import IdentityStatusChoices
from core.apps.crm.services.ocr import (
    InvalidDocumentError,
    OCRExtractionError,
    process_document,
)

LOGGER = logging.getLogger(__name__)


def process_identification_record(identification) -> bool:
    """
    Execute OCR and verification pipeline for a single CustomerIdentification instance.

    Uses a single try-except-finally block with granular exception catching
    and unified final state persistence.

    Args:
        identification: CustomerIdentification instance with an attached document file.

    Returns:
        bool: True if verification succeeded, False otherwise.
    """
    if not identification.document:
        LOGGER.warning(
            "Identification %s has no document attached; skipping OCR.",
            identification.pk,
        )
        return False

    is_verified = False
    status_value = IdentityStatusChoices.VERIFICATION_FAILED.value
    details: dict[str, Any] = {}
    verified_on = None
    update_fields = ["status", "is_verified", "details", "modified"]

    try:
        with identification.document.open("rb") as doc_file:
            pdf_bytes = doc_file.read()

        result = process_document(pdf_bytes, doc_type=identification.type)

        if result.get("error_code") or not result.get("data"):
            details = {"error": result.get("error_code", "no_data_extracted")}
        else:
            status_value = IdentityStatusChoices.VERIFIED.value
            is_verified = True
            verified_on = timezone.now().date()
            details = result.get("data", {})
            update_fields.append("verified_on")
            LOGGER.info(
                "Successfully verified identification %s (type=%s, confidence=%s)",
                identification.pk,
                identification.type,
                result.get("confidence"),
            )
    except (InvalidDocumentError, OCRExtractionError) as exc:
        LOGGER.warning(
            "Document validation or OCR error for identification %s: %s",
            identification.pk,
            exc,
        )
        details = {"error": getattr(exc, "code", "document_error")}
    except (OSError, IOError) as exc:
        LOGGER.error(
            "Could not read document file for identification %s: %s",
            identification.pk,
            exc,
        )
        details = {"error": "file_read_error"}
    except Exception as exc:
        LOGGER.exception(
            "Unexpected error processing identification %s: %s",
            identification.pk,
            exc,
        )
        details = {"error": "unexpected_error"}
    finally:
        identification.status = status_value
        identification.is_verified = is_verified
        identification.details = details
        if verified_on is not None:
            identification.verified_on = verified_on
        identification.save(update_fields=list(set(update_fields)))

    return is_verified


@shared_task(
    bind=True,
    name="core.apps.crm.tasks.process_customer_identification_ocr",
    max_retries=3,
    default_retry_delay=60,
)
def process_customer_identification_ocr(self, identification_id: str) -> None:
    """
    Process an individual CustomerIdentification record by primary key.

    TODO: This task should not be manually queued per upload; once Celery Beat is configured,
    background document processing is performed periodically by Celery Beat running
    `process_unverified_identifications_cron` at its configured cron schedule.
    """
    CustomerIdentification = get_customer_identification_model()
    try:
        identification = CustomerIdentification.available_objects.get(
            pk=identification_id
        )
    except CustomerIdentification.DoesNotExist:
        LOGGER.error("Customer identification %s not found.", identification_id)
        return

    process_identification_record(identification)


@shared_task(
    bind=True,
    name="core.apps.crm.tasks.process_unverified_identifications_cron",
)
def process_unverified_identifications_cron(
    self, batch_size: int = 50
) -> dict[str, int]:
    """
    Periodic Celery Beat cron task to scan and process unverified identification documents.

    Queries pending or unverified CustomerIdentification records that have uploaded documents,
    and runs the OCR verification engine across them in batches.

    Args:
        batch_size (int): Maximum records to process per cron invocation. Defaults to 50.

    Returns:
        dict[str, int]: Summary count of processed, verified, and failed records.
    """
    CustomerIdentification = get_customer_identification_model()
    pending_records = (
        CustomerIdentification.available_objects.filter(
            status__in=[
                IdentityStatusChoices.PENDING.value,
                IdentityStatusChoices.UNVERIFIED.value,
            ],
            document__isnull=False,
        )
        .exclude(document="")
        .select_related("customer")[:batch_size]
    )

    stats = {"total": 0, "verified": 0, "failed": 0}
    for record in pending_records:
        stats["total"] += 1
        success = process_identification_record(record)
        if success:
            stats["verified"] += 1
        else:
            stats["failed"] += 1

    LOGGER.info(
        "Completed OCR cron batch: %s total, %s verified, %s failed.",
        stats["total"],
        stats["verified"],
        stats["failed"],
    )
    return stats
