from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError


def standard_response(success: bool, message: str, data=None, errors=None, status_code=200):
    """
    Standard response formatter.
    """
    response_data = {
        "success": success,
        "message": message,
        "data": data if data is not None else None,
        "errors": errors if errors is not None else None
    }
    return Response(response_data, status=status_code)


def get_user_or_404(user_model, **kwargs):
    """
    Retrieve a user or raise a 404 error if not found.
    """
    return get_object_or_404(user_model, **kwargs)


def get_object_or_raise_error(model, error_message="Object not found", **kwargs):
    """
    Retrieve an object or raise a DRF NotFound exception with a custom error message.
    """
    obj = model.objects.filter(**kwargs).first()
    if not obj:
        raise NotFound(detail=error_message)
    return obj


def validate_required_fields(data, required_fields):
    """
    Ensure required fields are present in the data. Raise ValidationError if any field is missing.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError({field: "This field is required." for field in missing_fields})


def safe_getattr(obj, attr, default=None):
    """
    Safely get an attribute from an object. Return the default value if the attribute does not exist.
    """
    return getattr(obj, attr, default)


def get_object_or_404_with_custom_message(model, error_message="Object not found", **kwargs):
    """
    Retrieve an object or raise a 404 error with a custom message if not found.
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        raise NotFound(detail=error_message)

