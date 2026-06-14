"""Assertion suite for 'The AI1 Design Point' (Revision 4).
Verifies the DISPLAYED manuscript values (exact convention, one decimal in
Table 3) as well as full-precision intermediates, both area interpretations,
both power bases, both sensitivity branches, the overhead parameterization,
ISS conventions, and dual-basis constellation scaling.
Run: python3 verify_ai1.py  -> expected: All assertions pass.

VERIFICATION SCOPE: this suite verifies radiator-model calculations and
manuscript display values. Externally sourced thermophysical property data
are EXCLUDED from its verification scope: the ammonia critical point
(405.5 K, ~113 bar) and the saturation pressures quoted in the paper
(41.4, 46.8, 63.8, 88.4 bar at the stated radiator-surface temperatures,
used as lower bounds on loop pressure) are reference values from the NIST
Chemistry WebBook (SRD 69; Lemmon, McLinden, and Friend, 'Thermophysical
Properties of Fluid Systems') and are NOT computed or asserted here."""

sigma = 5.670374419184429e-8  # full binary64 SI-derived Stefan-Boltzmann
# constant (matches orbital_thermal.constants.SIGMA_SB); the truncated
# 5.670374419e-8 literal is rejected so this standalone suite independently
# locks the exact-sigma ground rule (audit r6 P3).

# Reported AI1 figures (announcement coverage; Table 1 of the paper)
Q_peak, Q_sust = 150e3, 120e3      # W (compute payload, used as radiative load; f=0)
A_plan         = 110.0             # m^2 ("up to"; double-sided planform reading)
A2             = 220.0             # m^2 emitting under that reading

def T_req(Q, A, eps, Ts):
    return (Q/(eps*sigma*A) + Ts**4)**0.25

def cap_kW(T, eps, Ts, A=220.0):
    return eps*sigma*A*(T**4 - Ts**4)/1e3

# --- B1: exact continuous-peak-hypothetical equilibrium (audit-required) ---
T_pk = T_req(Q_peak, A2, 0.91, 220.0)
assert abs(T_pk - 353.1623423) < 1e-6

# --- B2: capacities at that EXACT temperature (audit-required) ---
assert abs(cap_kW(T_pk, 0.91, 220.0) - 150.0)       < 1e-6
assert abs(cap_kW(T_pk, 0.80, 220.0) - 131.8681319) < 1e-6
assert abs(cap_kW(T_pk, 0.91, 260.0) - 124.7166261) < 1e-6
assert abs(cap_kW(T_pk, 0.80, 260.0) - 109.6409900) < 1e-6

# --- B3: display-rounding policy: Table 3 shows ONE DECIMAL at exact T_pk ---
assert round(cap_kW(T_pk, 0.91, 220.0), 1) == 150.0
assert round(cap_kW(T_pk, 0.80, 220.0), 1) == 131.9
assert round(cap_kW(T_pk, 0.91, 260.0), 1) == 124.7
assert round(cap_kW(T_pk, 0.80, 260.0), 1) == 109.6

# --- B4: headroom accounting (second-pass correction 2) ---
loss = 150.0 - cap_kW(T_pk, 0.80, 260.0)
assert abs(loss - 40.36) < 0.01          # total stress-induced capacity loss, kW
assert abs((150-120) - 30.0) < 1e-9      # advertised peak-to-sustained headroom
assert abs((120.0 - cap_kW(T_pk, 0.80, 260.0)) - 10.36) < 0.01  # deficit below sustained

# --- B5: all four operating points (two readings x two power bases) ---
assert abs(T_req(Q_sust, A2,    0.91, 220.0) - 337.1004) < 1e-3   # sustained, two-sided (primary)
assert abs(T_req(Q_peak, A2,    0.91, 220.0) - 353.1623) < 1e-3   # continuous-peak hypothetical
assert abs(T_req(Q_sust, 110.0, 0.91, 220.0) - 391.4652) < 1e-3   # sustained, one-sided
assert abs(T_req(Q_peak, 110.0, 0.91, 220.0) - 411.8443) < 1e-3   # continuous-peak, one-sided

# --- B6: coolant-class screen, second-pass wording basis ---
T_crit = 405.5
assert T_req(Q_peak, 110.0, 0.91, 220.0) > T_crit        # one-sided continuous-peak: supercritical
gap = T_crit - T_req(Q_sust, 110.0, 0.91, 220.0)
assert 13.9 < gap < 14.1                                  # one-sided sustained: <14 K headroom
                                                          #   (strong disfavor, NOT exclusion)
assert T_crit - T_pk > 50                                 # two-sided readings: >50 K margin
# Lower-bound saturation pressures at radiator-surface temperature (literature values):
P_sat = {353.16: 41.4, 358.91: 46.8, 374.17: 63.8, 391.47: 88.4}   # bar

# --- B7: equilibrium-temperature branch (fixed load, T free to rise) ---
assert abs(T_req(Q_sust, A2, 0.80, 220.0) - 346.21) < 0.01
assert abs(T_req(Q_sust, A2, 0.91, 260.0) - 350.78) < 0.01
assert abs(T_req(Q_sust, A2, 0.80, 260.0) - 358.91) < 0.01        # +21.8 K over nominal
assert abs(T_req(Q_peak, A2, 0.80, 260.0) - 374.17) < 0.01
assert T_req(Q_peak, A2, 0.80, 260.0) < T_crit

# --- B8: non-compute heat overhead parameterization Q_rad = (1+f) P_compute ---
assert abs(T_req(1.10*Q_sust, A2, 0.91, 220.0) - 343.80) < 0.01   # f = 0.10, nominal
assert abs(T_req(1.20*Q_sust, A2, 0.91, 220.0) - 350.12) < 0.01   # f = 0.20, nominal
assert abs(T_req(1.10*Q_sust, A2, 0.80, 260.0) - 365.24) < 0.01   # f = 0.10, stress case
assert abs(T_req(1.20*Q_sust, A2, 0.80, 260.0) - 371.26) < 0.01   # f = 0.20, stress case

# --- B9: illustrative effective-area case ("up to" qualifier) ---
assert abs(T_req(Q_sust, 0.85*A2, 0.91, 220.0) - 348.67) < 0.01

# --- B10: flux decomposition (net vs gross; planform vs emitting) ---
assert abs(Q_peak/A_plan - 1364) < 1                       # planform flux ("~1,400 W/m^2")
assert abs(Q_peak/A2     -  682) < 1                       # net flux per face, continuous peak
assert abs(Q_sust/A2     -  545) < 1                       # net flux per face, sustained
gross = 0.91*sigma*T_pk**4; sink = 0.91*sigma*220.0**4
assert abs(gross - 802.8) < 0.5 and abs(sink - 120.9) < 0.5
assert abs((gross - sink) - Q_peak/A2) < 0.5

# --- B11: ISS comparison; capacity firm, flux ratios PROVISIONAL ---
P_ISS = 70e3                                               # NASA-documented EATCS capacity
assert abs(Q_sust/P_ISS - 1.71) < 0.01
assert abs(Q_peak/P_ISS - 2.14) < 0.01
A_ISS = 422.0           # secondary reporting (SemiAnalysis via coverage); convention UNVERIFIED
assert abs((Q_sust/A2)/(P_ISS/A_ISS) - 3.29) < 0.02        # provisional
assert abs((Q_peak/A2)/(P_ISS/A_ISS) - 4.11) < 0.02        # provisional

# --- B12: constellation scaling, both bases ---
assert abs(1e9/Q_peak - 6667) < 1 and abs(1e9/Q_sust - 8333) < 1
assert abs(6667*A2/1e6 - 1.467) < 0.01                     # km^2 emitting per GW-yr, nameplate
assert abs(8333*A2/1e6 - 1.833) < 0.01                     # km^2 emitting per GW-yr, sustained

# --- B13: specific-power cross-check (array-output composite retired in Rev 4:
#          250 W/m^2 is a stated areal-density assumption, not a rated output) ---
assert abs(150e3/70e3 - 2.143) < 0.005                     # t, peak-normalized specific power
assert abs(120e3/70e3 - 1.714) < 0.005                     # t, sustained-normalized

# --- B14: hot-rejection factor (illustrative 293 K comparison, exact T_pk) ---
assert abs((T_pk**4 - 220**4)/(293**4 - 220**4) - 2.628) < 0.005

print(
    "All radiator-model calculations and manuscript display-rounding "
    "assertions pass. External thermophysical property values are not "
    "computed by this suite."
)
