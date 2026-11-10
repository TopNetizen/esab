"""Rhino COM 连接辅助函数。"""

from esab.adapters.hosts import connect_rhino
from esab.adapters.rhino_host import (
    rgb,
    to_flat_variant_i4,
    to_flat_variant_r8,
    to_nested_variant_i4,
    to_nested_variant_r8,
)

__all__ = [
    "get_rhino",
    "to_nested_variant_r8",
    "to_nested_variant_i4",
    "to_flat_variant_r8",
    "to_flat_variant_i4",
    "rgb",
]


def get_rhino():
    result = connect_rhino()
    if not result.ok:
        raise RuntimeError(result.message)
    return result.details.get("value")
