from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from model_utils.fields import StatusField

from core.apps.crm.constants import IdentityStatusChoices, IdentityTypeChoices
from core.utils.models import BaseModel


def crm_identity_document_path(
    instance: AbstractCustomerIdentification,
):
    """
    Document file save path for AbstractCustomerIdentification
    """
    path = f"{connection.schema_name}/{instance.type}"
    if instance.customer:
        path += f"/{instance.customer.id}"

    return path


class AbstractCustomerIdentification(BaseModel):
    """
    Abstract model for Customer KYC and Identification records.
    Supports Generic Foreign Key (GFK) to attach identity verification details or document instances.
    """

    DOCUMENT_UPLOAD_PATH = crm_identity_document_path
    VERIFICATION_STATUSES = IdentityStatusChoices.choices

    is_verified = models.BooleanField(default=False)
    verified_on = models.DateField(null=True, blank=True)
    status = StatusField(
        choices_name="VERIFICATION_STATUSES",
        default=IdentityStatusChoices.UNVERIFIED.value,
    )

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="identifications",
    )
    type = models.CharField(
        max_length=32,
        choices=IdentityTypeChoices.choices,
        default=IdentityTypeChoices.AADHAAR,
    )
    document = models.FileField(
        verbose_name=_("Document File"),
        upload_to=DOCUMENT_UPLOAD_PATH,
        null=True,
        blank=True,
    )

    # Generic Foreign Key (GFK) to link a identity model on identification
    # TODO: In Documents app create regulatory models like: Aadhar, SocialSecurity, PAN, etc.
    #   install them based on project settings only.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    attribute = GenericForeignKey("content_type", "object_id")

    details = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Customer Identification"
        verbose_name_plural = "Customer Identifications"

    def __str__(self):
        return f"{self.get_type_display()}: ({self.customer})"
