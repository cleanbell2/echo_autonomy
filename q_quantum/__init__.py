# q_quantum/__init__.py
"""
q_quantum package init
- keep: from q_quantum import EBreakCalculator
- avoid: eager imports that cause runpy/circular warnings
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, TYPE_CHECKING

__all__ = [
    "EBreachEngine",
    "EBreakEngine",
    "von_neumann_entropy",
    "EBreakCalculator",
]

if TYPE_CHECKING:
    # 타입체커 전용(런타임 import 아님)
    from .e_break_engine import EBreachEngine, EBreakEngine, von_neumann_entropy
    from .ebreak_calculator import EBreakCalculator

_LAZY = {
    "EBreachEngine": (".e_break_engine", "EBreachEngine"),
    "EBreakEngine": (".e_break_engine", "EBreakEngine"),
    "von_neumann_entropy": (".e_break_engine", "von_neumann_entropy"),
    "EBreakCalculator": (".ebreak_calculator", "EBreakCalculator"),
}

def __getattr__(name: str) -> Any:
    if name in _LAZY:
        mod_name, sym = _LAZY[name]
        mod = import_module(mod_name, __name__)
        val = getattr(mod, sym)
        globals()[name] = val  # 캐시
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")



