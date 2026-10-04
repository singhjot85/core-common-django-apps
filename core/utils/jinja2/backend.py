from django.template.backends.jinja2 import Jinja2


class Jinja2Backend(Jinja2):
    """
    Custom Jinja2 template backend that scans `<app>/templates/` directories
    when `APP_DIRS=True`, matching standard Django app layout while leveraging Jinja2.
    """

    app_dirname = "templates"
