"""Example 4: the full Stage-1 chip-to-radiator path at one representative point.

Builds a rank-eligible case (ammonia coolant, aluminium solid path) under the Stage-1 common
envelope, solves the B4 coupled model, and prints the coupled temperatures, the pump energy, the
**modeled component mass (incomplete Stage-1 accounting)**, and the B5/B6-style feasibility
classification with a traceable identifier.

This example does **not** run a new trade study or introduce new physics/assumptions: the six
Pareto figures come from the committed B6 data (`scripts/generate_trade_study.py` ->
`scripts/plot_trade_study.py`). It only walks the single-point path end to end.

Requires CoolProp (the coupled loop evaluates real coolant properties). Install with
``pip install "orbital-thermal[fluids]"``. Run from the repository root::

    python examples/04_chip_to_radiator.py
"""

import sys

try:
    import CoolProp  # noqa: F401
except ImportError:
    print("Example 4 needs CoolProp (pip install 'orbital-thermal[fluids]'); skipping.")
    sys.exit(0)

from orbital_thermal import architecture_cases as ac

COOLANT, MATERIAL = "ammonia", "aluminum"  # a rank-eligible reference case


def main() -> None:
    env = ac.Stage1Envelope()  # the declared Stage-1 common operating point (design variables)
    result = ac.evaluate_case(env, COOLANT, MATERIAL)  # classify + coupled solve + modeled mass

    trace = (f"{COOLANT}-{MATERIAL}|Q={env.q_compute_W:g}|mdot={env.mass_flow_kg_s:g}"
             f"|A={env.radiator_area_m2:g}|Plo={env.low_side_pressure_Pa:g}")
    print(f"case (traceability id): {trace}")
    print(f"classification: {result.classification.value}  "
          f"rank_eligible={result.rank_eligible}")
    print(f"reason(s): {', '.join(r.name for r in result.reason_codes)}")

    if result.coupled is None:  # a rejected/nonconverged point carries no coupled solution
        print(f"not solved (failed gates: {result.failed_gates})")
        return

    c = result.coupled
    print("\ncoupled steady state (temperatures/area are solved outputs, not a subtraction):")
    margin = env.t_junction_max_K - c.T_j_K
    print(f"  junction  T_j   = {c.T_j_K:7.2f} K   (margin to limit {margin:5.2f} K)")
    print(f"  wall      T_w   = {c.T_w_K:7.2f} K")
    print(f"  loop      T1/T2 = {c.T1_K:7.2f} / {c.T2_K:.2f} K")
    print(f"  radiator  T_rad = {c.T_rad_K:7.2f} K   (emitting area {c.A_emit_m2:.3f} m^2)")
    print(f"  rejected  Q_rad = {c.Q_rad_W:7.1f} W   "
          f"(chip {c.Q_chip_W:.0f} W + pump {c.Q_pump_fluid_W:.2f} W)")
    print(f"  pump      P_elec= {c.pump.electrical_power_W:7.2f} W   "
          f"(Re={c.reynolds:.0f}, dP={c.pressure_drop_Pa/1e3:.1f} kPa)")

    m = result.mass
    print(f"\n{m.label}:")
    for comp in m.components:
        mass = f"{comp.mass_kg:.4f} kg" if comp.mass_kg is not None else "excluded"
        print(f"  {comp.name:34s} {mass:>12s}  [{comp.completeness}]")
    print(f"  {'TOTAL (modeled, incomplete)':34s} {m.total_modeled_kg:.4f} kg")
    print(f"  excluded (not modeled): {', '.join(m.excluded_components)}")

    print("\nNote: this is one point. The six Pareto trade fronts are built + plotted from the "
          "committed B6 data, not from this example.")


if __name__ == "__main__":
    main()
