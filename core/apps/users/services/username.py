import secrets

from django.utils.text import slugify


def generate_unique_username(
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    phone_number: str = "",
) -> str:
    """
    Generate a clean, unique username from provided user attributes
    combined with a cryptographic random suffix.
    """
    from core.apps.users import get_user_model

    base_parts = []
    if first_name and first_name.strip():
        base_parts.append(slugify(first_name.strip()).replace("-", "_"))
    if last_name and last_name.strip():
        base_parts.append(slugify(last_name.strip()).replace("-", "_"))

    if base_parts:
        base_slug = "_".join(base_parts)
    elif email and "@" in email:
        local_part = email.split("@")[0].strip().replace(".", "_")
        base_slug = slugify(local_part).replace("-", "_") or "user"
    elif phone_number:
        clean_digits = "".join(filter(str.isdigit, phone_number))
        base_slug = f"user_{clean_digits[-6:]}" if len(clean_digits) >= 6 else "user"
    else:
        base_slug = "user"

    base_slug = base_slug[:30].strip("_") or "user"

    User = get_user_model()
    # Try with short hex suffix, loop until unique
    for _ in range(100):
        suffix = secrets.token_hex(2)
        candidate = f"{base_slug}_{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate

    # Fallback to longer token if heavily saturated
    return f"{base_slug}_{secrets.token_hex(4)}"
