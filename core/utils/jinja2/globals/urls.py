from django.templatetags.static import static
from django.urls import reverse

CORE_URL_GLOBALS = {
    "static": static,
    "url": reverse,
}
