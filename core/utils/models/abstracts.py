from django.db import models


class AbstractParty(models.Model):
    """Abstract Helper to give common party related attributes to a model

    Provide Attributes:
        suffix (CharField): Suffix for Name
        first_name (CharField): First name attribute.
        middle_name (CharField): Middle name attribute.
        last_name (CharField): Last name attribute.
        business_name (CharField): Business name attribute.
    """

    suffix = models.CharField(null=True, blank=True, default=None)
    first_name = models.CharField(null=True, blank=True, default=None)
    middle_name = models.CharField(null=True, blank=True, default=None)
    last_name = models.CharField(null=True, blank=True, default=None)
    business_name = models.CharField(null=True, blank=True, default=None)

    class Meta:
        abstract = True

    @property
    def full_name(self) -> str:
        """Return the combined full name or business_name."""
        name_parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(part for part in name_parts if part).strip()
        if name:
            if self.suffix:
                return f"{name} {self.suffix}".strip()
            return name
        return self.business_name or ""


class AbstractAddress(models.Model):
    """Abstract Helper to give common address attributes to a model.

    Provides Attributes:
        address_line_1 (CharField): Primary street address or building details.
        address_line_2 (CharField): Secondary street address / suite / apt.
        landmark (CharField): Nearby landmark.
        city (CharField): City or locality.
        state (CharField): State, province, or region.
        postal_code (CharField): Postal / PIN / Zip code.
        country (CharField): Country name or ISO country code (default 'IN').
    """

    address_line_1 = models.CharField(max_length=255, null=True, blank=True)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=128, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    state = models.CharField(max_length=128, null=True, blank=True)
    postal_code = models.CharField(max_length=32, null=True, blank=True)
    country = models.CharField(max_length=64, default="IN", null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def full_address(self) -> str:
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.landmark,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(p for p in parts if p)
