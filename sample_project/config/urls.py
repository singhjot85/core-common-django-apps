from django.urls import path

from core.utils.admin.sites import private_admin_site
from sample_project.apps.views import CoreSampleTemplateView

urlpatterns = [
    path("admin/", private_admin_site.urls),
    path("", CoreSampleTemplateView.as_view(), name="dashboard"),
]
