from typing import Annotated

from pydantic import AfterValidator
from pydantic.functional_serializers import PlainSerializer
from pydantic_core import PydanticOmit

from .formatters import (
    format_bool,
    format_bool_reversed,
    format_in_param,
    format_like_param,
    format_range_param,
    format_size_param,
)


def isTrueValidator(value: bool | None) -> str:
    """
    This validator checks that the input value is True.
    If it is, it returns the string "true". Otherwise, it raises a PydanticOmit exception. This allows to omit "False" and None values from the serialized output.
    The more common alternative would be to use a serializer (like the ones used in other fields), but this is not possible in this case because of this issue: https://github.com/pydantic/pydantic/issues/6969
    Basically using a serializer that converts False->None, if the serializer returns None the field would NOT be omitted.
    Using a validator instead allows to raise PydanticOmit exception, which will omit the field from the serialized output.
    Args:
        value (bool | None): The value to check.
    Returns:
        str: The string "true" if the value is True.
    Raises:
        PydanticOmit: If the value is not True.
    """
    if value is True:
        return str(value).lower()
    raise PydanticOmit


LikeStr = Annotated[str, PlainSerializer(format_like_param, return_type=str, when_used="json")]

RangeList = Annotated[
    list[int], PlainSerializer(format_range_param, return_type=list[int], when_used="json")
]

InList = Annotated[
    list[str], PlainSerializer(format_in_param, return_type=list[str], when_used="json")
]

SizeInt = Annotated[int, PlainSerializer(format_size_param, return_type=int, when_used="json")]

BoolStr = Annotated[bool, PlainSerializer(format_bool, return_type=str, when_used="json")]

BoolStrReversed = Annotated[
    bool, PlainSerializer(format_bool_reversed, return_type=str, when_used="json")
]

BoolNullFalseStr = Annotated[bool, AfterValidator(isTrueValidator)]
