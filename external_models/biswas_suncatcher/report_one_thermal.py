"""
Passive thermal sizing for a 1.45 kW TPU node at 650 km, dawn-dusk SSO.
Radiator: two 2 m^2 panels, Z-93 paint (eps 0.85 EOL), single-sided emitter.
Junction limit 125 C. Standard library only.
"""
import math

SIGMA = 5.670374419e-8
R_E = 6371e3
S0 = 1367.0
Q_IR = 237.0
ALBEDO = 0.30
J_LIMIT = 125.0

N_TPU, P_TPU = 4, 300.0
P_AVIONICS = 150.0
P_PARASITIC = 100.0
AREA = 4.0
EPS = 0.85
H = 650e3


def heat_load():
    compute = N_TPU * P_TPU
    return compute, compute + P_AVIONICS + P_PARASITIC


def radiator_temperature(Q, A, eps=EPS, T0=300.0, tol=1e-2, verbose=False):
    T = T0
    for k in range(1, 50):
        f = Q - eps * SIGMA * A * T ** 4
        fp = -4 * eps * SIGMA * A * T ** 3
        step = f / fp
        T -= step
        if verbose:
            print(f"      iter {k}: T = {T - 273.15:7.3f} C   (step {abs(step):.4f} K)")
        if abs(step) < tol:
            break
    return T - 273.15


def resistance_chain(r_jc=0.150, r_tim=0.040, r_base=0.060, r_pipe=0.080, r_rad=0.020):
    comps = {"junction-to-case": r_jc, "interface (TIM)": r_tim, "cold-plate base": r_base,
             "heat pipe": r_pipe, "radiator": r_rad}
    return sum(comps.values()), comps


def junction_temp(T_rad, P_chip, R_th):
    return T_rad + P_chip * R_th


def view_factor(h=H):
    r = R_E + h
    return 0.5 * (1 - math.sqrt(1 - (R_E / r) ** 2))


def external_loads(alpha_s=0.15, A=AREA, eps=EPS, h=H):
    F = view_factor(h)
    solar = S0 * alpha_s * A
    albedo = S0 * ALBEDO * F * alpha_s * A
    earth_ir = Q_IR * F * eps * A
    return F, solar, albedo, earth_ir


def eclipse_transient(t_s, T0_C, m=54.0, cp=900.0, A=AREA, eps=EPS, d_solar=-100.0):
    # lumped capacitance; Bi << 0.1 so node is isothermal
    T0 = T0_C + 273.15
    h_rad = 4 * eps * SIGMA * T0 ** 3
    tau = m * cp / (h_rad * A)
    dT_ss = d_solar / (h_rad * A)
    T_t = T0 + dT_ss * (1 - math.exp(-t_s / tau))
    return T_t - 273.15, tau, dT_ss, h_rad


def main():
    bar = "=" * 70

    compute, Q = heat_load()
    print("Heat load")
    print(f"  {N_TPU}x{P_TPU:.0f} W compute + {P_AVIONICS:.0f} W avionics + "
          f"{P_PARASITIC:.0f} W parasitic = {Q:.0f} W")

    print("\nRadiator temperature")
    T_rad = radiator_temperature(Q, AREA, verbose=True)
    print(f"  T_rad = {T_rad:.2f} C")

    print("\nResistance chain [K/W]")
    R_before, comps = resistance_chain()
    R_after, _ = resistance_chain(r_tim=0.020, r_pipe=0.050)
    for name, v in comps.items():
        print(f"  {name:18s} {v:.3f}")
    print(f"  total {R_before:.3f}, optimized {R_after:.3f}")

    Tj = junction_temp(T_rad, P_TPU, R_after)
    margin = J_LIMIT - Tj
    print("\nJunction temperature")
    print(f"  T_j = {T_rad:.2f} + {P_TPU:.0f}*{R_after:.3f} = {Tj:.1f} C, margin {margin:.1f} C")

    dR = 0.080 * (8 / 7 - 1)
    Tj_fail = junction_temp(T_rad, P_TPU, R_after + dR)
    print("\nOne heat pipe out (8 -> 7)")
    print(f"  dR = +{dR:.4f}, T_j = {Tj_fail:.1f} C, margin {J_LIMIT - Tj_fail:.1f} C")

    # passive wall: the interface rise P*R_th alone reaches the 125 C budget, so no
    # radiator size can relax it. P_max = J_LIMIT / R_th.
    P_max = J_LIMIT / R_after
    print("\nPassive wall (interface rise alone hits the budget)")
    print(f"  P_max = {J_LIMIT:.0f} / {R_after:.3f} = {P_max:.0f} W  (no radiator size relaxes it)")

    F, solar, albedo, earth_ir = external_loads()
    print("\nExternal loads (alpha_s = 0.15)")
    print(f"  F = {F:.3f}, solar {solar:.0f} W, albedo {albedo:.0f} W, Earth-IR {earth_ir:.0f} W")
    print(f"  Earth-facing worst case ~{albedo + earth_ir:.0f} W; edge-on baseline {P_PARASITIC:.0f} W")

    T_ec, tau, dT_ss, h_rad = eclipse_transient(300.0, T_rad)
    print("\nEclipse transient (t = 300 s)")
    print(f"  h_rad {h_rad:.2f} W/m^2K, tau {tau:.0f} s, dT_ss {dT_ss:.2f} K, T_rad(300s) {T_ec:.2f} C")

    assert abs(T_rad - 21.3) < 0.3
    assert abs(Tj - 111.3) < 0.5
    assert abs(Tj_fail - 114.8) < 0.5
    assert abs(P_max - 417) < 5
    assert abs(F - 0.290) < 0.005
    print(f"\n{bar}\nchecks ok\n{bar}")


if __name__ == "__main__":
    main()
