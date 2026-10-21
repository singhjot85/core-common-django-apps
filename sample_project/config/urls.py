from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from core.utils.admin.sites import private_admin_site
from sample_project.apps.views import BackendServerdUIView

urlpatterns = [
    path("admin/", private_admin_site.urls),
    path("", BackendServerdUIView.as_view(), name="dashboard"),
]


urlpatterns += staticfiles_urlpatterns()
