from django.utils.translation import gettext_lazy as _
from enum import Enum


class GenderEnum(Enum):
    MALE = "M"
    FEMALE = "F"

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]