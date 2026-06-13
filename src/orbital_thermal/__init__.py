"""orbital_thermal: executable reference implementation of the
orbital-thermal-bounds radiator model.

Theory preprint:  doi:10.5281/zenodo.20650893
AI1 companion:    doi:10.5281/zenodo.20670772
"""

from .constants import SIGMA_SB, ZERO_CELSIUS
from .equilibrium import equilibrium_temperature, radiative_capacity
from .radiation import (
    area_ratio,
    effective_sink_temperature,
    net_flux,
    required_area,
)

__version__ = "0.1.0"

__all__ = [
    "SIGMA_SB",
    "ZERO_CELSIUS",
    "area_ratio",
    "effective_sink_temperature",
    "equilibrium_temperature",
    "net_flux",
    "radiative_capacity",
    "required_area",
]
