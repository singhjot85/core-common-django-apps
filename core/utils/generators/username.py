import secrets
import typing

from django.contrib.auth import get_user_model
from django.utils.text import slugify


class UsernameGenerator:
    """
    Generator service for creating clean, unique usernames from user attributes.

    This class inspects available user identity attributes (first name, last name,
    email address, phone number) in priority order, normalizes them into a URL/username
    safe slug, and appends cryptographically generated pseudorandom suffixes to ensure
    uniqueness against the active user database.

    Attributes:
        first_name (str): User's first name.
        last_name (str): User's last name.
        email (str): User's email address.
        phone_number (str): User's phone number.
        max_base_length (int): Maximum character length of the base slug prefix before suffix.

    Example:
        >>> generator = UsernameGenerator(first_name="Jane", last_name="Doe")
        >>> username = generator.generate()
        >>> username.startswith("jane_doe_")
        True
    """

    def __init__(
        self,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone_number: str = "",
        max_base_length: int = 30,
    ) -> None:
        """
        Initialize the UsernameGenerator with candidate user identity attributes.

        Args:
            first_name (str, optional): User's first name. Defaults to "".
            last_name (str, optional): User's last name. Defaults to "".
            email (str, optional): User's email address. Defaults to "".
            phone_number (str, optional): User's phone number. Defaults to "".
            max_base_length (int, optional): Max length of the base slug prefix. Defaults to 30.
        """
        self.first_name = (first_name or "").strip()
        self.last_name = (last_name or "").strip()
        self.email = (email or "").strip()
        self.phone_number = (
            phone_number.as_e164
            if hasattr(phone_number, "as_e164")
            else str(phone_number or "").strip()
        )
        self.max_base_length = max_base_length

    def build_base_slug(self) -> str:
        """
        Derive a normalized base slug prefix from the configured attributes.

        Priority order:
        1. Name: Combination of slugified `first_name` and `last_name`.
        2. Email: Local part before `@` if available.
        3. Phone Number: Trailing 6 digits if available.
        4. Fallback: Generic `"user"`.

        Returns:
            str: Normalized base slug suitable for appending unique suffixes.
        """
        base_parts: list[str] = []
        if self.first_name:
            base_parts.append(slugify(self.first_name).replace("-", "_"))
        if self.last_name:
            base_parts.append(slugify(self.last_name).replace("-", "_"))

        if base_parts:
            base_slug = "_".join(filter(None, base_parts))
        elif self.email and "@" in self.email:
            local_part = self.email.split("@")[0].strip().replace(".", "_")
            base_slug = slugify(local_part).replace("-", "_") or "user"
        elif self.phone_number:
            clean_digits = "".join(filter(str.isdigit, self.phone_number))
            base_slug = (
                f"user_{clean_digits[-6:]}" if len(clean_digits) >= 6 else "user"
            )
        else:
            base_slug = "user"

        base_slug = base_slug[: self.max_base_length].strip("_")
        return base_slug or "user"

    def generate(
        self,
        user_model: typing.Optional[typing.Any] = None,
        max_attempts: int = 100,
    ) -> str:
        """
        Generate a confirmed unique username against the target user model database table.

        Args:
            user_model (Model class, optional): The Django User model to query for uniqueness.
                If None, defaults to `django.contrib.auth.get_user_model()`.
            max_attempts (int, optional): Number of attempts to generate with a 4-hex-char suffix
                before escalating to an 8-hex-char suffix. Defaults to 100.

        Returns:
            str: A guaranteed unique username string.
        """
        if user_model is None:
            user_model = get_user_model()

        base_slug = self.build_base_slug()

        # Try short 4-character hex suffix (16^4 = 65,536 combinations per base slug)
        for _ in range(max_attempts):
            suffix = secrets.token_hex(2)
            candidate = f"{base_slug}_{suffix}"
            if not user_model.objects.filter(username=candidate).exists():
                return candidate

        # Fallback to longer 8-character hex suffix if namespace is heavily saturated
        return f"{base_slug}_{secrets.token_hex(4)}"


def generate_unique_username(
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    phone_number: str = "",
    user_model: typing.Optional[typing.Any] = None,
) -> str:
    """
    Convenience functional wrapper around UsernameGenerator.

    Args:
        first_name (str, optional): User's first name. Defaults to "".
        last_name (str, optional): User's last name. Defaults to "".
        email (str, optional): User's email address. Defaults to "".
        phone_number (str, optional): User's phone number. Defaults to "".
        user_model (Model class, optional): User model to check uniqueness against.

    Returns:
        str: Guaranteed unique username string.
    """
    generator = UsernameGenerator(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
    )
    return generator.generate(user_model=user_model)
