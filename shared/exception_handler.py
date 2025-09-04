from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    ParseError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    UnsupportedMediaType,
    Throttled,
)
from rest_framework import status
from shared.utils import standard_response
from shared.custom_exceptions import CustomException
import logging

# Set up logging to capture unhandled exceptions
logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Enhanced custom exception handler to provide standardized responses.
    Extracts 'detail' or 'message' dynamically from exceptions.
    """
    # Call the default exception handler
    response = exception_handler(exc, context)

    # Dynamically get the message (priority: detail > message > fallback)
    message = getattr(exc, "detail", None) or getattr(exc, "message", "An error occurred.")

    # Explicit handling for ValidationError
    if isinstance(exc, ValidationError):
        return standard_response(
            success=False,
            message=message,
            errors=response.data,  # Validation errors are in response.data
            status_code=response.status_code
        )
    
    # Handle JWT token errors
    elif response is not None and response.status_code == status.HTTP_401_UNAUTHORIZED:
        if isinstance(exc.detail, dict) and exc.detail.get('code') == 'token_not_valid':
            return standard_response(
                success=False,
                message="Your access token has expired",
                errors=exc.detail,
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        else:
            return standard_response(
                success=False,
                message=message,
                errors=str(exc),
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    # Explicit handling for CustomException
    elif isinstance(exc, CustomException):
        return standard_response(
            success=False,
            message=message,
            errors=exc.errors,
            status_code=exc.status_code,
        )

    # Explicit handling for ParseError
    elif isinstance(exc, ParseError):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Explicit handling for AuthenticationFailed
    elif isinstance(exc, AuthenticationFailed):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Explicit handling for NotAuthenticated
    elif isinstance(exc, NotAuthenticated):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Explicit handling for PermissionDenied
    elif isinstance(exc, PermissionDenied):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Explicit handling for NotFound
    elif isinstance(exc, NotFound):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Explicit handling for MethodNotAllowed
    elif isinstance(exc, MethodNotAllowed):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # Explicit handling for UnsupportedMediaType
    elif isinstance(exc, UnsupportedMediaType):
        return standard_response(
            success=False,
            message=message,
            errors=str(exc),
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    # Explicit handling for Throttled
    elif isinstance(exc, Throttled):
        return standard_response(
            success=False,
            message=message,
            errors={"wait_time": exc.wait},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # For DRF-handled errors not explicitly caught above
    if response is not None:
        return standard_response(
            success=False,
            message=message,
            errors=response.data,
            status_code=response.status_code,
        )

    # Log and handle completely unhandled exceptions
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return standard_response(
        success=False,
        message="An internal server error occurred.",
        errors=str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
