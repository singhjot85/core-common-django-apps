import re


def camel_to_snake_case(class_name):
    """
    Convert CamelCase string to snake_case.
    Handle consecutive uppercase letters (acronyms) "HTTPResponse" -> "http_response"

    Args:
        class_name (str): String in CamelCase format (e.g., "SomeClassName")

    Returns:
        str: String in snake_case format (e.g., "some_class_name")


    NOTE: Doesn't handle cases when consecutive uppercases occur b/w string
    Example:

        >>> camel_to_snake_case("SomeClassNameNOclasURL")
        >>> 'some_class_name_n_oclas_url'

    """
    pattern = r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"
    snake = re.sub(pattern, "_", class_name)
    return snake.lower()
