"""Physical constants used throughout the orbital_thermal package.

All values are SI. SIGMA_SB matches the value used in the published
verification suites (verify_suite.py, companion/verify_ai1.py): the exact
CODATA 2018 derived value. Do not truncate it; some external models (e.g.
the McCalip JavaScript model) use 5.67e-8, and that difference is part of
any replication tolerance budget.
"""

#: Stefan-Boltzmann constant, W m^-2 K^-4 (exact, CODATA 2018 derived value)
SIGMA_SB: float = 5.670374419e-8

#: 0 degrees Celsius expressed in kelvin
ZERO_CELSIUS: float = 273.15
