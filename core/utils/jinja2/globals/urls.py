"""
Jinja2 URL and static asset resolution globals.
"""

from django.templatetags.static import static
from django.urls import reverse

CORE_URL_GLOBALS = {
    "static": static,
    "url": reverse,
}
