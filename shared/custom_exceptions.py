from typing import Any, Union
from rest_framework.views import exception_handler
from rest_framework import status
from shared.utils import standard_response
import logging

# Set up logging
logger = logging.getLogger(__name__)


class CustomException(Exception):
    """
    Base class for all custom exceptions with status_code, message, and errors.
    """
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: Union[int, str] = "A custom exception occurred.",
        errors: Any = None,
    ):
        self.status_code = status_code
        self.message = message
        if not isinstance(errors, (list, tuple, set)):
            errors = [errors]
        self.errors = errors
