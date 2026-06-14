"""Shared input-domain validators (audit re-review P2-4).

Small helpers used at public boundaries to reject non-finite and out-of-domain
inputs with clear, uniform messages, rather than silently returning NaN or a
coarse result.
"""

import math


def finite(name: str, x: float) -> float:
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite, got {x}")
    return x


def positive(name: str, x: float) -> float:
    finite(name, x)
    if x <= 0.0:
        raise ValueError(f"{name} must be > 0, got {x}")
    return x


def nonneg(name: str, x: float) -> float:
    finite(name, x)
    if x < 0.0:
        raise ValueError(f"{name} must be >= 0, got {x}")
    return x


def in_range(name: str, x: float, lo: float, hi: float) -> float:
    finite(name, x)
    if not (lo <= x <= hi):
        raise ValueError(f"{name} must be in [{lo}, {hi}], got {x}")
    return x


def boolean(name: str, x) -> bool:
    if not isinstance(x, bool):
        raise TypeError(f"{name} must be the boolean True or False, "
                        f"got {type(x).__name__}")
    return x


def positive_int(name: str, x) -> int:
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError(f"{name} must be an int, got {type(x).__name__}")
    if x < 1:
        raise ValueError(f"{name} must be >= 1, got {x}")
    return x
