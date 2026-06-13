"""Physical constants used throughout the orbital_thermal package.

All values are SI. SIGMA_SB is the binary64 (IEEE-754 double) value of the
Stefan-Boltzmann constant derived from the exact 2019-SI defining constants
k_B, h, c via sigma = 2*pi^5*k_B^4 / (15*h^3*c^2). It is therefore NOT the
truncated 5.670374419e-8 printed in CODATA tables -- that differs by ~3.3e-11
relative. The published verification suites (verify_suite.py and
companion/verify_ai1.py) used the truncated printed form; that difference is
part of any replication tolerance budget and is nanokelvin-level at the AI1
operating range (four-root sensitivity dT/T = d(sigma)/4 sigma). The external
McCalip JavaScript model uses 5.67e-8, a larger ~6.6e-5 difference.
"""

#: Stefan-Boltzmann constant, W m^-2 K^-4: binary64 of the SI-derived value
#: 2*pi^5*k_B^4 / (15*h^3*c^2) (see module docstring; not the truncated CODATA print).
SIGMA_SB: float = 5.670374419184429e-8

#: 0 degrees Celsius expressed in kelvin
ZERO_CELSIUS: float = 273.15
