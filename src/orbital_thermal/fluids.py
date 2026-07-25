"""Executable thermophysical-property checks for the AI1 coolant screen.

Computes the ammonia properties that the companion paper ("The AI1 Design
Point", doi:10.5281/zenodo.20670771) quotes as NIST Chemistry WebBook
reference values: critical point, saturation pressures at the modeled
radiator-surface temperatures, and phase state. With this module the
properties are CALCULATED rather than transcribed, upgrading the paper's
verification scope (its Option B exclusion) to executable form.

Backend: CoolProp HEOS (Helmholtz-energy equation of state). Use
:func:`provenance` to record the exact CoolProp version and the underlying
EOS citation next to any generated table; property values are only
reproducible against a pinned version.

This module is intentionally NOT imported by ``orbital_thermal/__init__``:
CoolProp is an optional dependency, and importing the core package must not
require it. Import explicitly::

    from orbital_thermal import fluids

Scope limit (companion paper, Phase 3 plan): property calculations verify
thermodynamic consistency only. They establish nothing about component
pressure ratings, pump feasibility, seal compatibility, or reliability.

Units: SI (kelvin, pascal, kg/m^3). ``PA_PER_BAR`` converts for display.
"""

try:
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI, get_BibTeXKey
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "orbital_thermal.fluids requires CoolProp. "
        'Install it with: pip install "orbital-thermal[fluids]" '
        "or: pip install CoolProp"
    ) from exc

import re
from dataclasses import dataclass
from pathlib import Path

from . import _validate as _v
from .registry.two_phase import COOLPROP_PIN as _COOLPROP_PIN
from .registry.two_phase import TWO_PHASE_PROPERTIES as _TWO_PHASE_PROPERTIES

#: Pascals per bar.
PA_PER_BAR: float = 1e5

#: Default working fluid for the AI1 coolant screen.
DEFAULT_FLUID: str = "Ammonia"


def critical_temperature(fluid: str = DEFAULT_FLUID) -> float:
    """Critical temperature, K. Paper's NIST anchor for ammonia: 405.5 K."""
    return PropsSI("Tcrit", fluid)


def critical_pressure(fluid: str = DEFAULT_FLUID) -> float:
    """Critical pressure, Pa. Paper's NIST anchor for ammonia: ~113 bar."""
    return PropsSI("pcrit", fluid)


def saturation_pressure(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Saturation (vapor) pressure at temperature ``T``, in Pa.

    This is the lower bound on loop pressure for keeping the coolant
    liquid at the radiator-surface temperature -- the quantity behind the
    paper's 41.4 / 46.8 / 63.8 / 88.4 bar ladder.

    Raises ValueError above the critical temperature, where a saturation
    curve no longer exists.
    """
    _v.positive("T", T)
    T_crit = critical_temperature(fluid)
    if T >= T_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of "
            f"{fluid} ({T_crit:.2f} K); no saturation pressure exists"
        )
    return PropsSI("P", "T", T, "Q", 0.0, fluid)


def phase_state(T: float, P: float, fluid: str = DEFAULT_FLUID) -> str:
    """CoolProp phase label at (``T`` K, ``P`` Pa).

    Typical labels: 'liquid', 'gas', 'supercritical', 'supercritical_gas',
    'supercritical_liquid', 'twophase'.
    """
    _v.positive("T", T)
    _v.positive("P", P)
    return PhaseSI("T", T, "P", P, fluid)


def critical_margin(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Temperature headroom to the critical point: T_crit - T, in K.

    Positive means a subcritical liquid loop is possible at sufficient
    pressure; negative means no liquid phase exists at any pressure. The
    paper's screen: >50 K margin for the two-sided readings, <14 K for
    one-sided sustained, negative for one-sided continuous-peak.
    """
    _v.finite("T", T)
    return critical_temperature(fluid) - T


def saturated_densities(
    T: float, fluid: str = DEFAULT_FLUID
) -> tuple[float, float]:
    """(liquid, vapor) densities on the saturation curve at ``T``, kg/m^3.

    Raises ValueError for non-finite/non-positive ``T`` and at or above the
    critical temperature, where the saturation curve no longer exists (audit r8 P3)."""
    _v.positive("T", T)
    T_crit = critical_temperature(fluid)
    if T >= T_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of "
            f"{fluid} ({T_crit:.2f} K); no saturation densities exist"
        )
    rho_liq = PropsSI("D", "T", T, "Q", 0.0, fluid)
    rho_vap = PropsSI("D", "T", T, "Q", 1.0, fluid)
    return rho_liq, rho_vap


# --- S2 two-phase saturation backend (Stage 2, milestone S2) --------------------
# The saturation properties the flow-boiling evaporator needs, evaluated on the
# pinned CoolProp HEOS backend named by ``registry.two_phase.COOLPROP_PIN``.
#
# Every call is guarded twice:
#
# 1. against the **declared** validity domain of the corresponding
#    ``TWO_PHASE_PROPERTIES`` registry entry (ammonia 195.5-405.4 K, water
#    273.16-647.1 K), so a two-phase call cannot silently leave the registered
#    domain; and
# 2. against the **actual** backend triple/critical bounds, so no call can be
#    evaluated at or above the critical point even where the declared domain
#    nominally permits it (the declared water upper bound 647.1 K sits a few
#    millikelvin above the CoolProp critical temperature 647.096 K).
#
# A coolant with no ``TWO_PHASE_PROPERTIES`` entry is **source-gated** and raises:
# S0 Section 9.1 admits ammonia (reference) and water (secondary) only, and an
# unregistered coolant has no sourced saturation domain to evaluate against.

#: Declared two-phase saturation domains, keyed by lowercased fluid name. Read from
#: the registry rather than restated, so the domain has exactly one definition.
_SAT_T_DOMAIN_K: dict[str, tuple[float, float]] = {
    e.material.lower(): e.domain.ranges["T_K"]
    for e in _TWO_PHASE_PROPERTIES
    if "T_K" in e.domain.ranges
}


# --- OTB-G001 F-10: the pinned backend is enforced, not merely recorded -----------


class BackendPinMismatchError(RuntimeError):
    """Raised when the installed CoolProp version differs from ``COOLPROP_PIN``.

    Before this fix the pin was metadata: ``registry.two_phase.COOLPROP_PIN`` recorded
    7.2.0, the test asserted that the *literal* said 7.2.0, and ``fluids`` imported
    whatever CoolProp happened to be installed. An environment resolved without the
    pin could shift every saturation value while the results were still presented as
    pinned. Saturation evaluation now fails instead.
    """


#: An explicitly reviewed override of the backend pin, or ``None``.
#:
#: Set only through :func:`override_backend_pin`, which requires a review-record
#: reference. The migration path for a version change is therefore explicit and
#: separately reviewed, rather than an environment variable that silently disables the
#: guard -- advancing the pin needs the property-drift re-verification named in
#: ``COOLPROP_PIN.migration_requires``.
_BACKEND_PIN_OVERRIDE: tuple[str, str] | None = None


#: Where a review record cited by :func:`override_backend_pin` must live, and the
#: naming already in use there (``YYYY-MM-DD-<slug>.md``).
REVIEW_RECORDS_DIR = "verification/review-records"
_REVIEW_RECORD_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[A-Za-z0-9._-]+\.md$")


def _resolve_review_record(review_record: str) -> Path:
    """Resolve ``review_record`` to a real file, or raise saying why it did not.

    OTB-G001-FIXES F-05: requiring only a non-blank string accepted ``'x'``, ``'...'``,
    ``'TODO'`` and ``'no such record exists'``. An override whose justification cannot
    be located is the silent version shift the pin guard exists to stop, so the
    reference must resolve to a file that is actually present.
    """
    name = Path(review_record.strip()).name
    if not _REVIEW_RECORD_PATTERN.match(name):
        raise ValueError(
            f"review_record {review_record!r} does not name a review record: expected "
            f"a file under {REVIEW_RECORDS_DIR}/ following the naming already in use "
            "there, YYYY-MM-DD-<slug>.md"
        )

    root = Path(__file__).resolve().parents[2]
    candidate = root / REVIEW_RECORDS_DIR / name
    if not candidate.is_file():
        available = sorted(p.name for p in (root / REVIEW_RECORDS_DIR).glob("*.md"))
        raise ValueError(
            f"review_record {review_record!r} does not resolve: no file "
            f"{REVIEW_RECORDS_DIR}/{name}. Advancing the backend pin needs a real "
            f"record of the property-drift re-verification "
            f"({_COOLPROP_PIN.migration_requires}). Records present: "
            f"{', '.join(available) if available else '(none)'}"
        )
    return candidate


def override_backend_pin(version: str, *, review_record: str) -> None:
    """Accept ``version`` instead of the pinned one, citing the review that allows it.

    ``review_record`` must **resolve to a real file** under
    ``verification/review-records/`` -- not merely be a non-empty string. See
    :func:`_resolve_review_record`.
    """
    global _BACKEND_PIN_OVERRIDE
    if not version.strip():
        raise ValueError("override_backend_pin requires a non-empty version")
    if not review_record.strip():
        raise ValueError(
            "override_backend_pin requires a review_record: advancing the backend pin "
            "needs the property-drift re-verification recorded in "
            f"COOLPROP_PIN.migration_requires ({_COOLPROP_PIN.migration_requires})"
        )
    resolved = _resolve_review_record(review_record)
    _BACKEND_PIN_OVERRIDE = (version.strip(), str(resolved))


def clear_backend_pin_override() -> None:
    """Drop any override and restore strict pin enforcement."""
    global _BACKEND_PIN_OVERRIDE
    _BACKEND_PIN_OVERRIDE = None


def backend_version() -> str:
    """The installed CoolProp version string."""
    return CoolProp.__version__


def assert_backend_pin() -> None:
    """Raise unless the installed CoolProp matches the pin (or a reviewed override).

    Called by every saturation evaluation, so a pinned-property claim cannot be made
    against an unpinned backend.
    """
    installed = backend_version()
    if installed == _COOLPROP_PIN.pinned_version:
        return
    if _BACKEND_PIN_OVERRIDE is not None and installed == _BACKEND_PIN_OVERRIDE[0]:
        return
    raise BackendPinMismatchError(
        f"installed CoolProp {installed} does not match the pinned "
        f"{_COOLPROP_PIN.backend} {_COOLPROP_PIN.pinned_version}. Saturation values "
        "from a different backend version are not the pinned values and must not be "
        f"reported as such. To advance the pin: {_COOLPROP_PIN.migration_requires} "
        "Then record the review and call override_backend_pin(version, "
        "review_record=...)."
    )


class SourceGatedFluidError(ValueError):
    """Raised for a two-phase saturation call on a coolant with no registry entry.

    Not an invented default: S0 Section 9.1 admits ammonia (reference) and water
    (secondary); every other coolant is source-gated until a registry entry with a
    sourced validity domain exists.
    """


def two_phase_domain_K(fluid: str = DEFAULT_FLUID) -> tuple[float, float]:
    """Declared two-phase saturation temperature domain ``(T_min, T_max)`` in K.

    Raises :class:`SourceGatedFluidError` for a coolant with no registry entry.
    """
    key = fluid.strip().lower()
    if key not in _SAT_T_DOMAIN_K:
        allowed = ", ".join(sorted(_SAT_T_DOMAIN_K))
        raise SourceGatedFluidError(
            f"two-phase saturation properties for '{fluid}' are source-gated: no "
            f"registry entry declares a validity domain for it. Registered "
            f"two-phase coolants: {allowed}. Add a sourced "
            "TWO_PHASE_PROPERTIES entry before evaluating it (no-invention policy)."
        )
    return _SAT_T_DOMAIN_K[key]


def assert_two_phase_domain(T: float, fluid: str = DEFAULT_FLUID) -> None:
    """Raise unless ``T`` is inside both the declared domain and the real
    triple/critical bounds of ``fluid``. Never silently extrapolated."""
    _v.positive("T", T)
    lo, hi = two_phase_domain_K(fluid)
    if not (lo <= T <= hi):
        raise ValueError(
            f"T = {T} K is outside the declared two-phase domain of {fluid} "
            f"[{lo}, {hi}] K; the case is out of domain, not extrapolated"
        )
    t_crit = critical_temperature(fluid)
    t_triple = triple_temperature(fluid)
    if T >= t_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of {fluid} "
            f"({t_crit:.3f} K); no saturation state exists (no blanket "
            "supercritical treatment)"
        )
    if T < t_triple:
        raise ValueError(
            f"T = {T} K is below the triple-point temperature of {fluid} "
            f"({t_triple:.3f} K); no saturation state exists"
        )


def triple_pressure(fluid: str = DEFAULT_FLUID) -> float:
    """Triple-point pressure, Pa (lower bound of the saturation curve)."""
    return PropsSI("p_triple", fluid)


def saturation_temperature(P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Saturation temperature at pressure ``P`` [Pa], in K.

    The inverse of :func:`saturation_pressure`. Enforces the S0 Section 3 loop-state
    bound ``P_triple < P < P_crit``: outside it there is no saturation state and the
    call raises rather than returning a supercritical or sub-triple value.
    """
    assert_backend_pin()
    _v.positive("P", P)
    p_crit = critical_pressure(fluid)
    p_triple = triple_pressure(fluid)
    if P >= p_crit:
        raise ValueError(
            f"P = {P} Pa is at or above the critical pressure of {fluid} "
            f"({p_crit:.4g} Pa); no saturation temperature exists (no blanket "
            "supercritical treatment)"
        )
    if P <= p_triple:
        raise ValueError(
            f"P = {P} Pa is at or below the triple-point pressure of {fluid} "
            f"({p_triple:.4g} Pa); no saturation temperature exists"
        )
    T_sat = PropsSI("T", "P", P, "Q", 0.0, fluid)
    assert_two_phase_domain(T_sat, fluid)
    return T_sat


def saturation_enthalpies(
    P: float, fluid: str = DEFAULT_FLUID
) -> tuple[float, float, float]:
    """Saturated ``(h_f, h_g, h_fg)`` at pressure ``P`` [Pa], in J/kg.

    ``h_f`` is the saturated-liquid enthalpy, ``h_g`` the saturated-vapour enthalpy,
    and ``h_fg = h_g - h_f`` the latent heat of vaporisation. These are the terms
    behind the vapour quality ``x = (h - h_f) / h_fg`` (S0 Section 3).
    """
    T_sat = saturation_temperature(P, fluid)  # validates P and the domain
    h_f = PropsSI("H", "T", T_sat, "Q", 0.0, fluid)
    h_g = PropsSI("H", "T", T_sat, "Q", 1.0, fluid)
    return h_f, h_g, h_g - h_f


def surface_tension(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Liquid-vapour surface tension at saturation temperature ``T`` [K], in N/m."""
    assert_backend_pin()
    assert_two_phase_domain(T, fluid)
    return PropsSI("I", "T", T, "Q", 0.0, fluid)


@dataclass(frozen=True)
class SaturationState:
    """An immutable saturation state, bound to the fluid, pressure and backend that
    produced it (OTB-G001 F-05).

    Before this fix the evaporator took an untagged ``dict`` of properties alongside a
    separate ``fluid`` string and a separate ``LoopState``. Nothing tied the three
    together, so ammonia properties could be passed with ``fluid="Water"`` and return a
    finite coefficient with the fluid-applicability flag flipped, or properties
    evaluated at 0.3 MPa could be checked against a 1.0 MPa guard. The types could not
    establish that the guarded domain was the domain actually evaluated.

    Carrying fluid, pressure and backend version *inside* the value closes that: a
    consumer can assert the state it is about to evaluate is the state it just checked.
    """

    fluid: str
    pressure_Pa: float
    backend: str
    backend_version: str
    T_sat_K: float
    h_f_J_kg: float
    h_g_J_kg: float
    h_fg_J_kg: float
    rho_f_kg_m3: float
    rho_g_kg_m3: float
    mu_f_Pa_s: float
    mu_g_Pa_s: float
    k_f_W_mK: float
    cp_f_J_kgK: float
    sigma_N_m: float
    p_reduced: float
    molar_mass_kg_mol: float

    @property
    def molar_mass_g_mol(self) -> float:
        """Molar mass in g/mol, the convention the dimensional Cooper term requires."""
        return self.molar_mass_kg_mol * 1000.0

    def liquid_reynolds(
        self, *, mass_flux_kg_m2s: float, quality: float, diameter_m: float
    ) -> float:
        """Liquid-fraction Reynolds number ``Re_L = G(1-x)D/mu_f`` for this state.

        Lives here because it is a property of the state plus the channel, and the
        regime guard must be computed from the same state that will be evaluated.
        """
        return mass_flux_kg_m2s * (1.0 - quality) * diameter_m / self.mu_f_Pa_s

    def matches(self, *, fluid: str, pressure_Pa: float, rel_tol: float = 1e-9) -> bool:
        """Whether this state is labelled for ``fluid`` at ``pressure_Pa``.

        A **label** check only. It cannot detect a state whose properties belong to a
        different fluid, because it never looks at the properties -- use
        :meth:`verify_is` for that. Callers on the ranking path must not rely on this
        alone: OTB-G001-FIXES F-03 was exactly a guard that called
        ``matches(fluid=state.fluid, ...)``, comparing the field to itself.
        """
        if fluid.strip().lower() != self.fluid.strip().lower():
            return False
        return abs(self.pressure_Pa - pressure_Pa) <= rel_tol * max(
            abs(self.pressure_Pa), abs(pressure_Pa), 1.0
        )

    #: Every physical property carried on the state, compared by :meth:`verify_is`.
    #: Listed explicitly so a field added later is a visible decision rather than a
    #: silent gap in the check.
    _VERIFIED_PROPERTIES = (
        "T_sat_K",
        "h_f_J_kg",
        "h_g_J_kg",
        "h_fg_J_kg",
        "rho_f_kg_m3",
        "rho_g_kg_m3",
        "mu_f_Pa_s",
        "mu_g_Pa_s",
        "k_f_W_mK",
        "cp_f_J_kgK",
        "sigma_N_m",
        "p_reduced",
        "molar_mass_kg_mol",
    )

    def verify_is(self, declared_fluid: str, *, rel_tol: float = 1e-9) -> None:
        """Raise unless this state really is ``declared_fluid`` at its own pressure.

        **Re-derives the state from the backend and compares every property.** A label
        comparison cannot be trusted here: a state carrying ammonia properties and the
        string ``"Water"`` is indistinguishable from a real water state by any check
        that only reads the label. Recomputing is the only test that a relabelling
        cannot pass, which is what OTB-G001-FIXES F-03 requires.

        The backend and its version are compared too, so a state produced under a
        different pinned backend cannot be replayed against this one.
        """
        label = declared_fluid.strip().lower()
        if label != self.fluid.strip().lower():
            raise ValueError(
                f"saturation state is labelled '{self.fluid}' but the case declares "
                f"'{declared_fluid}'; the state and the case must agree on the fluid"
            )

        truth = saturation_state(self.pressure_Pa, declared_fluid)

        if (self.backend, self.backend_version) != (truth.backend, truth.backend_version):
            raise ValueError(
                f"saturation state was produced by {self.backend} "
                f"{self.backend_version}, but the current backend is {truth.backend} "
                f"{truth.backend_version}; pinned values are not comparable across "
                "backend versions"
            )

        mismatched = []
        for name in self._VERIFIED_PROPERTIES:
            mine, theirs = getattr(self, name), getattr(truth, name)
            if abs(mine - theirs) > rel_tol * max(abs(mine), abs(theirs), 1.0):
                mismatched.append(f"{name}: state {mine!r} vs {declared_fluid} {theirs!r}")
        if mismatched:
            raise ValueError(
                f"saturation state is labelled '{declared_fluid}' but its properties "
                f"are not {declared_fluid}'s at {self.pressure_Pa:.6g} Pa -- "
                f"{len(mismatched)} of {len(self._VERIFIED_PROPERTIES)} properties "
                f"differ: {'; '.join(mismatched[:4])}"
            )


def saturation_state(P: float, fluid: str = DEFAULT_FLUID) -> SaturationState:
    """Every saturation property the S2 evaporator needs, bound to its own identity.

    One guarded trip to the pinned backend, returning a value that carries the fluid,
    the pressure and the backend version it was evaluated at.
    """
    assert_backend_pin()
    T_sat = saturation_temperature(P, fluid)
    h_f, h_g, h_fg = saturation_enthalpies(P, fluid)
    rho_f, rho_g = saturated_densities(T_sat, fluid)
    return SaturationState(
        fluid=fluid,
        pressure_Pa=P,
        backend=_COOLPROP_PIN.backend,
        backend_version=backend_version(),
        T_sat_K=T_sat,
        h_f_J_kg=h_f,
        h_g_J_kg=h_g,
        h_fg_J_kg=h_fg,
        rho_f_kg_m3=rho_f,
        rho_g_kg_m3=rho_g,
        mu_f_Pa_s=PropsSI("V", "T", T_sat, "Q", 0.0, fluid),
        mu_g_Pa_s=PropsSI("V", "T", T_sat, "Q", 1.0, fluid),
        k_f_W_mK=PropsSI("L", "T", T_sat, "Q", 0.0, fluid),
        cp_f_J_kgK=PropsSI("C", "T", T_sat, "Q", 0.0, fluid),
        sigma_N_m=surface_tension(T_sat, fluid),
        p_reduced=P / critical_pressure(fluid),
        molar_mass_kg_mol=PropsSI("M", fluid),
    )


def provenance(fluid: str = DEFAULT_FLUID) -> dict[str, str]:
    """Version and equation-of-state citation for reproducibility records.

    Include this next to every generated property table: values are only
    comparable against the same CoolProp version and EOS.
    """
    return {
        "package": "CoolProp",
        "version": CoolProp.__version__,
        "backend": "HEOS",
        "fluid": fluid,
        "eos_bibtex_key": get_BibTeXKey(fluid, "EOS"),
    }


# --- per-state transport properties (fulfils the B1 property_backend; used by B3) ---


def density(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Density at (T [K], P [Pa]), kg/m^3."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("D", "T", T, "P", P, fluid)


def specific_heat(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Isobaric specific heat cp at (T, P), J/kg/K."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("C", "T", T, "P", P, fluid)


def thermal_conductivity(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Thermal conductivity at (T, P), W/m/K."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("L", "T", T, "P", P, fluid)


def dynamic_viscosity(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Dynamic viscosity at (T, P), Pa*s."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("V", "T", T, "P", P, fluid)


def prandtl(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Prandtl number Pr = cp * mu / k at (T, P) [-]."""
    return (
        specific_heat(T, P, fluid)
        * dynamic_viscosity(T, P, fluid)
        / thermal_conductivity(T, P, fluid)
    )


def triple_temperature(fluid: str = DEFAULT_FLUID) -> float:
    """Triple-point temperature, K (lower bound for the liquid; a freeze proxy)."""
    return PropsSI("T_triple", fluid)


def transport_properties(T: float, P: float, fluid: str = DEFAULT_FLUID) -> dict[str, float]:
    """All per-state properties the pumped-loop model needs, at (T, P)."""
    return {
        "density": density(T, P, fluid),
        "specific_heat": specific_heat(T, P, fluid),
        "thermal_conductivity": thermal_conductivity(T, P, fluid),
        "dynamic_viscosity": dynamic_viscosity(T, P, fluid),
        "prandtl": prandtl(T, P, fluid),
    }


def single_phase_liquid_margins(T: float, P: float, fluid: str = DEFAULT_FLUID) -> dict[str, float]:
    """Margins that keep a coolant a subcooled single-phase liquid at (T, P).

    - ``subcooling_Pa`` = P - P_sat(T) (must be > 0: loop pressure exceeds saturation);
    - ``freeze_margin_K`` = T - T_triple;
    - ``critical_margin_K`` = T_crit - T.

    ``ok`` is True iff all three are positive. Above the critical temperature the
    saturation curve does not exist and ``subcooling_Pa`` is ``-inf``.
    """
    _v.positive("T", T)
    _v.positive("P", P)
    t_crit = critical_temperature(fluid)
    crit = t_crit - T
    freeze = T - triple_temperature(fluid)
    subcool = float("-inf") if T >= t_crit else P - saturation_pressure(T, fluid)
    return {
        "subcooling_Pa": subcool,
        "freeze_margin_K": freeze,
        "critical_margin_K": crit,
        "ok": bool(subcool > 0 and freeze > 0 and crit > 0),
    }
