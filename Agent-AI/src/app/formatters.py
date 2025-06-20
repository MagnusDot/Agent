from typing import Any


def format_bool(param: bool | None) -> str | None:
    if param is None:
        return None
    return str(param).lower()


def format_bool_reversed(param: bool | None) -> str | None:
    if param is True:
        return "false"
    return None


def format_like_param(param: str | None) -> str | None:
    if param is None:
        return None
    if param.startswith("*") and param.endswith("*"):
        return param
    param = param.replace("*", "")
    return f"*{param}*"


def format_in_param(param: list | None) -> str | None:
    return param


def format_value_param(param: Any) -> str | None:
    return str(param)


def format_range_param(param: list | None) -> str | None:
    if isinstance(param, list):
        return ",".join([str(i) for i in param])
    else:
        return param


def format_size_param(param: int | None) -> int:
    return min(param, 50)


def format_param(
    param: str | bool | list | None | int,
    is_like: bool = False,
    is_size: bool = False,
    is_in: bool = False,
    is_range: bool = False,
    is_value: bool = False,
) -> str | None:
    if param is None:
        return None
    if isinstance(param, bool):
        return format_bool(param)
    if is_like:
        return format_like_param(param)
    if is_in:
        return format_in_param(param)
    if is_range:
        return format_range_param(param)
    if is_value:
        return format_value_param(param)
    if isinstance(param, int) and is_size:
        return format_size_param(param)
    return param


def format_params(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}
