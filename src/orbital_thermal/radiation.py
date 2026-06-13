"""Gray-body radiator identities (Level A results of the theory preprint).

Model scope: gray-body, diffuse, isothermal radiator rejecting heat by
far-field radiation to a lumped effective sink at temperature ``T_sink``
(the papers' T_s^eff = F^(1/4) * T_s). See Lemma 1 and Corollaries 1.1-1.2
of "Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in
Orbital Data Centers" (doi:10.5281/zenodo.20650893).

Units: SI throughout. Temperatures in kelvin, power in watts, area in
square meters. Areas are *emitting* areas; a two-sided planform panel has
emitting area equal to twice its planform area.
"""

from .constants import SIGMA_SB


def _check(emissivity: float, T: float, T_sink: float) -> None:
    """Reject non-physical inputs early, with messages that say why."""
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if T_sink < 0.0:
        raise ValueError(f"sink temperature must be >= 0 K, got {T_sink}")
    if T <= T_sink:
        raise ValueError(
            f"radiator temperature ({T} K) must exceed the effective sink "
            f"temperature ({T_sink} K) for net heat rejection"
        )


def net_flux(T: float, emissivity: float, T_sink: float = 0.0) -> float:
    """Net radiated flux of a gray surface, in W/m^2.

    q = emissivity * sigma * (T^4 - T_sink^4)
    """
    _check(emissivity, T, T_sink)
    return emissivity * SIGMA_SB * (T**4 - T_sink**4)


def required_area(
    Q: float, T: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Emitting area (m^2) required to reject ``Q`` watts at temperature ``T``.

    Lemma 1 (area law):  A = Q / (emissivity * sigma * (T^4 - T_sink^4))

    Worked anchor (Corollary 1.2): 1 MW at 293 K with emissivity 0.91 and
    zero sink requires 2,630 m^2 of emitting area (1,315 m^2 of two-sided
    planform).
    """
    if Q <= 0.0:
        raise ValueError(f"heat load Q must be positive, got {Q}")
    return Q / net_flux(T, emissivity, T_sink)


def area_ratio(T1: float, T2: float, T_sink: float = 0.0) -> float:
    """Exact area ratio A(T1) / A(T2) at equal duty (Corollary 1.1).

    R = (T2^4 - T_sink^4) / (T1^4 - T_sink^4)

    Raising the rejection temperature from T1 to T2 divides the required
    area by R. Worked anchor: 293 K -> 600 K with T_sink = 220 K gives
    exactly 6697760000/264604779 (about 25.312); the zero-sink estimate
    17.585 is 30.5% below it.

    Emissivity cancels at equal duty, so it does not appear here.
    """
    _check(1.0, T1, T_sink)
    _check(1.0, T2, T_sink)
    return (T2**4 - T_sink**4) / (T1**4 - T_sink**4)


def effective_sink_temperature(view_factor: float, T_sink: float) -> float:
    """Lumped view-factor-weighted effective sink: T_s^eff = F^(1/4) * T_s.

    ``view_factor`` is the radiator's view factor to the warm environment
    (0 = sees only deep space, 1 = sees only the environment at T_sink).
    This is the one-number environment summary whose validity domain the
    simulation program exists to quantify.
    """
    if not 0.0 <= view_factor <= 1.0:
        raise ValueError(f"view factor must be in [0, 1], got {view_factor}")
    if T_sink < 0.0:
        raise ValueError(f"sink temperature must be >= 0 K, got {T_sink}")
    return view_factor**0.25 * T_sink
