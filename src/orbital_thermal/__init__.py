"""orbital_thermal: executable reference implementation of the
orbital-thermal-bounds radiator model.

Theory preprint:  doi:10.5281/zenodo.20650893
AI1 companion:    doi:10.5281/zenodo.20670771

Note: the top-level ``effective_sink_temperature`` (from :mod:`radiation`) is the
generic lumped view-factor sink T_s^eff = F^(1/4) T_s. The orbit-resolved,
attitude-aware sink is :func:`orbital_thermal.sink.orbital_effective_sink_temperature`
(``sink.effective_sink_temperature`` remains as a deprecated alias). They have
different signatures and contracts; see audit re-review P2-9.
"""

from .bounds import (
    carnot_cop_cooling,
    conversion_area_penalty,
    fixed_work_area_per_watt,
    heat_pump_area_ratio,
    heat_pump_overhead,
    heating_cop,
    nonzero_sink_optimum,
    optimal_cold_fraction,
    quintic_residual,
    recirculation_amplification,
)
from .constants import SIGMA_SB, ZERO_CELSIUS
from .equilibrium import equilibrium_temperature, radiative_capacity
from .radiation import (
    area_ratio,
    effective_sink_temperature,
    net_flux,
    required_area,
)

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("orbital-thermal")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = [
    "SIGMA_SB",
    "ZERO_CELSIUS",
    "area_ratio",
    "carnot_cop_cooling",
    "conversion_area_penalty",
    "effective_sink_temperature",
    "equilibrium_temperature",
    "fixed_work_area_per_watt",
    "heat_pump_area_ratio",
    "heat_pump_overhead",
    "heating_cop",
    "net_flux",
    "nonzero_sink_optimum",
    "optimal_cold_fraction",
    "quintic_residual",
    "radiative_capacity",
    "recirculation_amplification",
    "required_area",
]
