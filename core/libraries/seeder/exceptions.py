import typing

if typing.TYPE_CHECKING:
    from django.db import models


class SeederDataLoaderException(Exception):
    """ """

    def __init__(self, loader_type: str, message: str, *args):
        message = f"Exception loading data from: {loader_type}, {message}"
        super().__init__(*args)


class SeederException(Exception):
    """ """

    pass


class InvalidFieldError(Exception):
    """ """

    def __init__(self, field_name, model_kls: type["models.Model"], *args):
        """ """
        message = f"{field_name}, is an Invalid field for model: {model_kls.__name__}"
        super().__init__(message, *args)


class FieldException(Exception):
    """ """

    def __init__(self, field_name, model_kls, message, *args):
        """ """
        message = f"Error in {field_name} of {model_kls.__name__}: {message}"
        super().__init__(message, *args)
