"""Equilibrium temperature and fixed-temperature capacity.

These two functions mirror the ``T_req`` and ``cap`` definitions asserted
block-by-block in ``companion/verify_ai1.py`` for "The AI1 Design Point"
(doi:10.5281/zenodo.20670772). They are each other's inverses, and the
smoke tests assert that round trip explicitly.

Units: SI throughout. ``area`` is emitting area in m^2.
"""

import math

from .constants import SIGMA_SB
from .radiation import _check
from . import _validate as _v


def equilibrium_temperature(
    Q: float, area: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Steady radiator temperature that rejects ``Q`` watts through ``area``.

    T = (Q / (emissivity * sigma * area) + T_sink^4)^(1/4)

    Worked anchor (AI1 primary operating point): 120 kW through 220 m^2 at
    emissivity 0.91 with T_s^eff = 220 K gives 337.1 K.
    """
    if not (math.isfinite(Q) and Q > 0.0):
        raise ValueError(f"heat load Q must be finite and > 0, got {Q}")
    if not (math.isfinite(area) and area > 0.0):
        raise ValueError(f"area must be finite and > 0, got {area}")
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not (math.isfinite(T_sink) and T_sink >= 0.0):
        raise ValueError(f"sink temperature must be finite and >= 0 K, got {T_sink}")
    return (Q / (emissivity * SIGMA_SB * area) + T_sink**4) ** 0.25


def radiative_capacity(
    T: float, area: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Heat rejection capacity (W) of ``area`` m^2 held at temperature ``T``.

    Q = emissivity * sigma * area * (T^4 - T_sink^4)

    Inverse of :func:`equilibrium_temperature` at fixed area, emissivity,
    and sink.
    """
    _v.positive("area", area)
    _check(emissivity, T, T_sink)
    return emissivity * SIGMA_SB * area * (T**4 - T_sink**4)
