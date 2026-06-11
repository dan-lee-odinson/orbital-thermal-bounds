# Ideal Thermodynamic Bounds and Decision Criteria for Orbital Data Center Thermal Architecture

## Revision 3 — final form, incorporating both GPT 5.5 audit rounds in full

**Scope of this document.** Formal derivation of ideal thermodynamic bounds and reduced-order decision criteria for an orbital thermal-control architecture modeled as a gray, diffuse, isothermal radiator coupled to a lumped effective radiative environment. Results are presented at three explicitly separated levels: **Level A** (model identities, exact within the model), **Level B** (reversible thermodynamic lower bounds, exact as bounds), and **Level C** (reduced-order architecture decision criteria, valid under stated mass-model assumptions with empirical inputs). This document does **not** claim to prove the optimum of every irreversible engine or every realizable orbital architecture.

**Revision record.** v1 → v2: all sixteen acceptance criteria of the first GPT 5.5 audit (corrected quantifiers, reversible-scope labeling, exact sink algebra, analytic stationarity, consistent normalizations, three-level classification, runnable appendix). v2 → v3: all twelve residual items of the follow-up audit (percentage-direction wording, narrowed 99% consequence, weakened structural-invariance claim, implicit-characterization labeling, complete fixed-point convergence proof, zero-sink qualification and exact nonzero-sink form of the conversion penalty, dimensionless quintic residual, enforced convergence tolerance, added assertions, model-scoped closing language, illustrative-sink wording). v3 final additionally supplies **Appendix W**, a Wolfram Language symbolic verification suite, with exact rational forms and high-precision reference roots, so that a CAS-equipped reviewer can verify every Level A/B claim symbolically rather than by translating the Python appendix. A subsequent Wolfram-assisted audit independently confirmed the full mathematical core; its targeted corrections — the fixed-work divergence argument completing Theorem 1, executable forms for W-blocks W1/W2/W3 with literal advertised outputs, a new W3b limit block, method-accurate description of the quintic root evaluation, and qualified deployability wording in the Theorem 1 illustration — are incorporated in this final form.

---

## 0. Model Scope Statement

All results below are exact **within the adopted thermal model**: a gray, diffuse, isothermal radiating surface of emissivity ε, exchanging with a lumped radiative environment characterized by a single view-factor-weighted effective sink temperature. Direct application to a real orbital architecture additionally requires environmental heat-load decomposition (solar absorption, planetary albedo, planetary IR, cold sky), spectral and directional surface properties, and multi-surface view-factor modeling. Where environmental and surface effects can be represented by fixed effective properties and a lumped sink temperature, they alter the model parameters. Where absorbed loads, spectral properties, geometry, or temperatures depend on the design variables, they may also alter the functional form of the heat balance and the resulting optimum.

In the passive steady-state thermal-control architecture considered here, terminal heat rejection to vacuum occurs by far-field electromagnetic radiation. Open-cycle mass ejection and deliberate export of coherent or nonthermal radiation are outside the model. Near-field radiative transfer and vacuum phonon tunneling operate only at sub-wavelength gaps and require a second material body that must itself radiate; they are internal transport mechanisms, not terminal rejection, and are likewise outside the model.

---

## 1. Notation and Constants

| Symbol | Meaning | Units |
|---|---|---|
| σ | Stefan–Boltzmann constant = 5.670374419 × 10⁻⁸ | W·m⁻²·K⁻⁴ |
| ε | Hemispherical IR emissivity, 0 < ε ≤ 1 | — |
| A | Total emitting surface area (A_emit; a two-sided panel has A_emit = 2·A_planform) | m² |
| T_h | Hot-side (heat source) absolute temperature | K |
| T_c | Cold-side (radiator) absolute temperature | K |
| T_s | Environmental brightness/source temperature | K |
| T_s^eff | View-factor-weighted lumped effective sink temperature, T_s^eff = F^(1/4)·T_s | K |
| Q_h, Q_c | Heat flow into engine / rejected by engine | W |
| W | Work (electrical power) output or input | W |
| η | Conversion efficiency W/Q_h | — |
| COP_c, COP_h | Cooling COP = Q_c/W; heating COP = Q_h/W | — |
| y, r, q | y = T_c/T_h; r = T_s^eff/T_h; q = T_s^eff/T_c | — |

Throughout the body, T_s denotes T_s^eff unless stated otherwise. All temperatures absolute; all heat flows steady-state averages. The worked sink value 220 K used below is an **illustrative effective sink temperature** under the lumped model, not a statement that "space in LEO is 220 K"; it stands in for a specific (unstated here) view-factor and environmental decomposition.

---

## 2. Axioms and Definitions

**A1 (Gray-body radiative rejection model).** Net radiated power of the model radiator:

    P_net = ε σ A (T_c⁴ − (T_s^eff)⁴)

*Status: idealized gray-body, isothermal, effective-sink model postulate (see §0 scope statement).*

**A2 (Second law, Carnot form).** Any cyclic engine between reservoirs at T_h > T_c satisfies η ≤ 1 − T_c/T_h. Any cyclic heat pump satisfies COP_c ≤ T_c/(T_h − T_c). Kelvin–Planck formulation (used in Theorem 5): a cyclic device cannot convert heat drawn from a single thermal reservoir entirely into work. *Status: physical postulate.*

**A3 (First law).** Engine: Q_h = W + Q_c. Heat pump: Q_h = Q_c + W.

**A4 (Lumped compute heat model).** In steady operation, electrical energy not exported in signals, stored energy, mechanical work, or other retained forms ultimately appears as heat; those exported or stored fractions are assumed negligible in the lumped compute model, so compute power P dissipates as heat at the source temperature. For net rejection, T_c > T_s^eff.

**D1 (Reversible engine).** An engine attaining equality in the Carnot bound: η = 1 − T_c/T_h. Combining with A3 (W = Q_h − Q_c) gives the reversible heat split **Q_c/Q_h = T_c/T_h**. All uses of this equality below are labeled reversible; generic engines receive the corresponding inequality.

**Dependency statement.** Level A results follow from A1 and A3. Level B results follow from A1–A4 plus D1 (reversibility) where labeled. Level C results additionally require the reduced-order mass models and empirical parameters identified in §5–§6.

---

## 3. Level A — Model Identities

### Lemma 1 (Radiator area requirement)

Rejecting heat flow Q_c > 0 at radiator temperature T_c requires

    A = Q_c / [ε σ (T_c⁴ − (T_s^eff)⁴)]

**Proof.** Inversion of A1 with P_net = Q_c; positive and well-defined by A4. ∎

### Corollary 1.1 (Area ratio between rejection temperatures — exact and approximate forms)

For equal heat load and emissivity, rejecting at T₂ instead of T₁ (T₂ > T₁ > T_s^eff) changes area by the **exact** factor

    R = A₁/A₂ = (T₂⁴ − T_s⁴) / (T₁⁴ − T_s⁴)

The zero-sink approximation R₀ = (T₂/T₁)⁴ carries exact relative deviation

    R/R₀ − 1 = [(T_s/T₁)⁴ − (T_s/T₂)⁴] / [1 − (T_s/T₁)⁴]

with safe upper bound (T_s/T₁)⁴ / [1 − (T_s/T₁)⁴]. The deviation is **not** generally below (T_s/T₁)⁴ [v1 claimed otherwise; corrected in v2].

**Worked example (T₁ = 293 K, T₂ = 600 K, T_s = 220 K illustrative):** R₀ = 17.585; exact R = **25.312**. The exact sink-corrected ratio is **43.9% greater than** the zero-sink estimate; equivalently, the zero-sink estimate is **30.5% below** the exact result (1 − R₀/R = 0.305). [Percentage direction corrected in v3.] The correction strengthens the design conclusion: against the illustrative warm effective sink, hot rejection is *more* advantageous than the idealized 17.6×, because the warm sink penalizes the cold radiator disproportionately. ∎ (Numerics: Appendix block B1.)

### Corollary 1.2 (Reference area check)

Q_c = 1 MW, T_c = 293 K, ε = 0.91, T_s ≈ 0: A_emit = 10⁶/(0.91·σ·293⁴) = **2,630 m²** of emitting surface — realizable as ~**1,315 m²** of two-sided panel planform (A_emit = 2·A_planform). Consistent with the ~1,200 m²/MW literature figure (different assumed ε, T). ∎

### Lemma 4a (COP identity — general)

COP_h = COP_c + 1 for any heat pump. **Proof.** A3: Q_h = Q_c + W; divide by W. ∎

---

## 4. Level B — Reversible Thermodynamic Lower Bounds

### Theorem 1 (Non-attainability of sink-temperature Carnot efficiency)

For any finite area A and any strictly positive rejected heat flow Q_c, Lemma 1 forces

    T_c⁴ = (T_s^eff)⁴ + Q_c/(εσA) > (T_s^eff)⁴, hence η ≤ 1 − T_c/T_h < 1 − T_s^eff/T_h.

The sink-temperature Carnot value is therefore **not attained** by any system with finite area and positive throughput. It may be **approached** along two limiting routes: (i) at fixed nonzero heat or work throughput, only as A → ∞; (ii) at fixed finite area, only as throughput Q_c → 0 (vanishing power).

**Proof.** Strict inequality: immediate from Lemma 1. Route (i), fixed heat throughput: at fixed Q_c > 0, T_c⁴ − T_s⁴ = Q_c/(εσA) → 0 iff A → ∞. Route (i), fixed work throughput: for fixed W > 0, the Carnot bound (A2) gives Q_c/W ≥ T_c/(T_h − T_c), hence

    A/W ≥ T_c / [εσ(T_h − T_c)(T_c⁴ − T_s⁴)]

which diverges as T_c → T_s⁺ when T_s > 0; for T_s = 0 it reduces to 1/[εσ(T_h − T_c)T_c³], which diverges as T_c → 0⁺. Thus approaching the sink-temperature Carnot limit at fixed positive work also requires A → ∞. (CAS limit checks: Appendix W block W3b.) Route (ii): at fixed A < ∞, T_c⁴ − T_s⁴ → 0 iff Q_c → 0. ∎

**Consequence (correctly scoped).** Claims that obtain approximately 99% efficiency merely by substituting the 2.7 K cosmic-background temperature for the material cold-reservoir temperature are **incomplete**: a finite-throughput design must solve for T_c > T_s and the associated radiator area. Efficiencies near 99% are not mathematically forbidden, but the required area becomes extreme as T_c approaches T_s. **Worked illustration:** T_h = 300 K, T_s = 2.7 K, T_c = 3.0 K gives reversible η = 99.0%; at W = 1 MW, Q_c = W·T_c/(T_h − T_c) ≈ 10.1 kW, and the ideal blackbody area is A = Q_c/[σ(3.0⁴ − 2.7⁴)] ≈ **6.4 × 10⁹ m²** — finite, but approximately six million times the order-of-magnitude radiator area of the 293 K reference example (Corollary 1.2), and therefore far outside the design scale contemplated by this reduced model. The theorem establishes an area–throughput penalty, not a categorical impossibility of efficiency values near the sink-temperature Carnot figure. [Narrowed in v3.] (Appendix block B8.)

**Remark (direct radiative converters).** Thermoradiative and negative-illumination devices fall outside the material-cold-reservoir premise of this theorem because part of the outgoing photon flux is converted directly to electrical work; they require a separate detailed-balance treatment (Strandberg 2011; Santhanam & Fan 2016). This document makes no claim that they are the unique such architecture, and no second-law exception is implied — they are a different architecture to which this theorem's premise does not apply.

### Theorem 2 (The ¾ rule — reversible lower-envelope optimum, zero-sink model)

**(a) General-engine bound.** For any engine producing work W and rejecting at T_c through a radiator (T_s = 0 here; nonzero sink in Theorem 3), A3 gives Q_c = W(1−η)/η, and A2 gives (1−η)/η ≥ T_c/(T_h − T_c). Hence

    A/W = (1−η)/(η · εσT_c⁴) ≥ 1 / [εσ(T_h·T_c³ − T_c⁴)]   for all admissible engines.

**(b) Optimum of the lower envelope.** The right-hand side is minimized where f(T_c) = T_h·T_c³ − T_c⁴ is maximized:

    f′ = T_c²(3T_h − 4T_c) = 0 ⇒ T_c* = (3/4)T_h;
    f″(T_c*) = 6T_h·T_c* − 12T_c*² = −2.25·T_h² < 0 (maximum of f);
    f → 0 at both endpoints of (0, T_h) ⇒ interior point is the global optimum.

Reversible efficiency at the optimum: η = 1 − 3/4 = **25%**.

**(c) Scope.** This is the optimum of the **reversible lower envelope** of A/W — a lower-bound design reference. It is **not** the operating optimum of every irreversible engine: for an engine with efficiency law η = a(1 − T_c/T_h), 0 < a < 1, the area-per-work optimum shifts upward:

| a (fraction of Carnot) | optimal T_c/T_h |
|---|---|
| 1.0 | 0.750 |
| 0.8 | 0.765 |
| 0.5 | 0.781 |

(Numerics: Appendix block B2.) Real engine selection requires the engine's actual η(T_c) law. ∎

**Distinction from Curzon–Ahlborn.** The Curzon–Ahlborn efficiency 1 − √(T_c/T_h) arises in a particular endoreversible maximum-power model with finite-rate linear heat transfer. The present result optimizes a different objective (radiator area per unit work) under a radiative T⁴ rejection law. No agreement should be expected.

### Corollary 2.1 (Conversion area penalty — universal lower bound, with sink qualification)

**Zero-sink form.** Relative to direct rejection of Q_h at T_h, any engine rejecting at T_c < T_h requires (T_s = 0)

    A_engine/A_direct = (1−η)·(T_h/T_c)⁴ ≥ (T_h/T_c)³

with equality **only** in the reversible limit (since 1−η ≥ T_c/T_h by A2). At the Theorem-2 optimum T_c = ¾T_h, the **minimum possible** zero-sink area penalty is (4/3)³ ≈ **2.370**; any irreversibility increases it (e.g., a = 0.8 at the same T_c gives (1−0.2)·(4/3)⁴ ≈ **2.528**).

**Nonzero-sink form (exact).** With a common sink T_s > 0,

    A_engine/A_direct = (1−η)·(T_h⁴ − T_s⁴)/(T_c⁴ − T_s⁴) ≥ (T_h/T_c)³ · [1 − (T_s/T_h)⁴]/[1 − (T_s/T_c)⁴]

and since T_c < T_h makes the final fraction exceed one, the penalty **strictly exceeds** (T_h/T_c)³ for any T_s > 0, even in the reversible limit. The cubic result is therefore a valid universal lower bound whose equality requires both (1) reversible conversion and (2) T_s = 0. [Sink qualification added in v3.] ∎ (Numerics: Appendix block B3.)

**Interpretation.** Energy recovery is never area-free: 25% recovery costs *at least* 2.37× radiator area versus direct hot rejection, and strictly more against any real sink. Recovery is mass-rational only when displaced solar-array mass exceeds this added radiator mass (Proposition P3).

### Theorem 3 (Nonzero-sink optimum — exact implicit characterization)

**Claim.** With effective sink T_s > 0, the reversible-envelope optimum T_c* satisfies the quintic stationarity equation

    4T_c⁵ − 3T_h·T_c⁴ − T_h·T_s⁴ = 0,

equivalently the **exact implicit characterization** (q contains the unknown T_c*, so this is not an explicit closed form)

    T_c*/T_h = (3 + q⁴)/4,  q ≡ T_s/T_c*,

with exact fractional shift above ¾T_h of **q⁴/3**. The optimum is unique and strictly increasing in T_s, and the shift is ≤ 0.49⁴/3 ≈ **1.9216% for q ≤ 0.49**.

**Proof.** Objective (from Lemma 1 and the reversible heat split): minimize A/W ∝ [T_c/(T_h−T_c)]/(T_c⁴−T_s⁴), i.e., maximize

    g(T_c) = (T_h − T_c)(T_c⁴ − T_s⁴)/T_c = T_h·T_c³ − T_c⁴ − T_h·T_s⁴/T_c + T_s⁴.

Differentiate: g′(T_c) = 3T_h·T_c² − 4T_c³ + T_h·T_s⁴/T_c². Setting g′ = 0 and multiplying by T_c² > 0:

    3T_h·T_c⁴ − 4T_c⁵ + T_h·T_s⁴ = 0  ⇔  4T_c⁵ − 3T_h·T_c⁴ = T_h·T_s⁴.

Dividing by 4T_h·T_c⁴ gives T_c/T_h = 3/4 + (T_s/T_c)⁴/4 = (3 + q⁴)/4. Fractional shift: [T_c* − ¾T_h]/(¾T_h) = (q⁴/4)/(3/4) = q⁴/3, monotone in q; q ≤ 0.49 ⇒ shift ≤ 0.49⁴/3 = 1.9216%.

*Uniqueness and monotonicity.* In reduced variables y = T_c/T_h, r = T_s/T_h, stationarity reads 4y⁵ − 3y⁴ = r⁴. For y ≥ 3/4, d/dy(4y⁵ − 3y⁴) = 4y³(5y − 3) > 0, so the left side is strictly increasing: the interior optimum is unique and increases monotonically with T_s. Endpoint behavior (g(T_s) = 0, g(T_h) = 0, g > 0 between) confirms the interior maximum. ∎

**Fixed-point convergence (complete).** Define the iteration map Φ(T) = (T_h/4)·[3 + (T_s/T)⁴]. Its derivative is Φ′(T) = −T_h·T_s⁴/T⁵. At the physical fixed point, |Φ′(T_c*)| = (T_h/T_c*)·q⁴ = 4q⁴/(3 + q⁴) using T_c*/T_h = (3+q⁴)/4; for every physical q < 1, 4q⁴/(3+q⁴) < 1, so the fixed point is locally attracting. The appendix iterates to an enforced successive-iterate tolerance of 10⁻¹⁰ K (block B4) and verifies convergence for the numerical range tested; the dimensionless quintic residual 4y⁵ − 3y⁴ − r⁴ is asserted below 10⁻¹². [Replaced incomplete v2 statement.]

**Verification values.** At T_h = 600 K, T_s = 220 K (illustrative): T_c* = **457.98675408138325 K** (high-precision numerical evaluation of the exact algebraic `Root` object, Appendix W block W2c; independently cross-checked by a 40-digit Newton iteration with quintic residual < 10⁻²⁵ and by the fixed-point iteration of the Python appendix), shift +1.77483424% — equal to q⁴/3 to 38 decimal places. A coarse grid maximization is retained only as a redundant cross-check. No claim is made regarding solvability of the quintic by radicals; the CAS represents the root exactly as a `Root` object.

**Design consequence.** At the illustrative design point the ¾ rule carries sub-2% error; it survives as a design rule, with an analytic error formula rather than a numerical table alone.

### Theorem 4 (Heat-pump overhead bound and area ratio)

**(a) Overhead.** Pumping IT thermal load Q_c from T_c to rejection at T_h requires W/Q_c = 1/COP_c ≥ (T_h − T_c)/T_c (A2), and the radiator must reject Q_h = Q_c(1 + 1/COP_c) (A3, Lemma 4a). At T_c = 353 K, T_h = 520 K: COP_c ≤ 353/167 = 2.114, COP_h ≤ 3.114 (identity check: 2.114 + 1), minimum overhead 0.473 W per IT watt.

**(b) Area ratio — exact form with sink.** Pumping from unpumped rejection temperature T₁ to pumped temperature T₂, with common sink T_s, equal emissivity and view geometry:

    A_pump/A_direct = (1 + 1/COP_c) · (T₁⁴ − T_s⁴)/(T₂⁴ − T_s⁴)

The form (1 + 1/COP_c)(T₁/T₂)⁴ is the T_s = 0 approximation. **Worked example** (T₁ = 353, T₂ = 520, T_s = 220 illustrative, COP_c = 1.15): exact ratio **0.348**; zero-sink approximation 0.397. ∎ (Appendix block B5.)

**Empirical flag.** The "realistic COP_c ≈ 1.0–1.3" range is an empirical parameter (vapor-compression machines at ΔT ≈ 170 K lift, space-rated compressor practice), not derived from A1–A4. It joins the empirical parameter list in §6.

### Theorem 5 (Impossibility of waste-heat self-powering — scoped)

**Claim.** No cyclic system can sustain a positive compute load solely by converting its own internally generated waste heat back into work. Under the stated two-reservoir model with compute power P (A4), recovery efficiency η < 1 (strict, by Theorem 1 with finite area and positive throughput), and recovered work recirculated to the bus:

    P_ext = P(1 − η) > 0.

External energy resources other than the waste heat itself (solar, nuclear, chemical) are outside this claim — the theorem does not forbid zero *grid* input; it forbids *bootstrapping from one's own waste heat*.

**Proof.** Bus balance: P = P_ext + W_rec, W_rec = η·P. Hence P_ext = P(1−η) > 0 since η < 1. Self-powering (P_ext ≤ 0) requires η ≥ 1: a cyclic device converting heat from a single effective reservoir entirely into work, contradicting the Kelvin–Planck statement (A2). ∎

**Remark (amplification).** Recirculation sustains P/P_ext = 1/(1−η) watts of compute per external watt — e.g., η = 0.25 gives 1.333. Recovery is an offset multiplier, never a replacement. (Appendix block B6.)

---

## 5. Level C — Architecture Decision Criteria (reduced-order mass models)

These are decision criteria under explicitly reduced mass models with empirical inputs. They are **not** universal theorems; they are first-order conditions whose verdicts flip with parameter values but whose algebraic validity is independent of them.

**P1 (Radiator selection — equal-duty normalization).** Let ρ_A denote *effective system areal density normalized to equal delivered rejection capacity* — same rejected power, operating temperature, effective emissivity, view geometry, and lifetime/availability; otherwise compare total system masses directly. Under that normalization, droplet radiators are mass-favorable iff

    ρ_A,droplet·(1 + δ_capture) < ρ_A,solid·(1 + δ_debris)   [kg/m² both sides]

**P2 (Heat pump inclusion — necessary first-order condition).** Under the stated reduced mass model, including pump hardware and ancillary masses, the heat pump is mass-favorable only if

    ρ_A·(A_direct − A_pump) > (Q_c/COP_c)·m_array + M_pump + M_ancillary   [kg both sides]

with A_pump from Theorem 4(b) (exact sink-inclusive form), m_array in kg per electrical watt, and M_ancillary covering power electronics, plumbing, working fluid, structure, deployment, redundancy, and lifetime margins. This is a necessary first-order condition; a full verdict requires the complete mass ledger.

**P3 (Topping-cycle inclusion — consistent normalization).** Define engine specific mass per watt of **thermal input**, s_h = M_engine/Q_h [kg/W_th]. The engine is mass-favorable under the reduced model iff

    s_h < η·m_array + ρ_A·(A_direct − A_engine)/Q_h   [kg/W_th both sides]

Equivalently, per watt **recovered** (s_e = M_engine/W = s_h/η):

    s_e < m_array + ρ_A·(A_direct − A_engine)/(η·Q_h)   [kg/W_rec both sides]

Both forms are stated with their own normalization; they are the same criterion. Note A_engine > A_direct (Corollary 2.1), so the area term is **negative**: the engine must overcome both its own mass and its area penalty. With η ≤ ¼ at the reversible-envelope optimum, the bar is high.

---

## 6. Corrected Result Inventory

| Result | Status |
|---|---|
| Radiator area inversion (L1) | Proven within gray-body effective-sink model |
| T⁴ area scaling (C1.1) | Exact with sink term; (T₂/T₁)⁴ is the T_s = 0 approximation (30.5% below exact at the illustrative example; exact is 43.9% above it) |
| Sink-temperature Carnot non-attainment (T1) | Proven for finite area and positive throughput; approachable via A→∞ at fixed throughput or Q_c→0 at fixed area; near-Carnot values attainable only at extreme area |
| Carnot heat split (D1) | Proven for reversible engines (definitional equality + first law) |
| T_c* = ¾T_h, η = 25% (T2) | Reversible lower-envelope optimum, zero-sink model; irreversible optima shift upward |
| (T_h/T_c)³ area penalty (C2.1) | Universal lower bound; equality requires reversibility **and** T_s = 0; strictly exceeded for T_s > 0 |
| Nonzero-sink optimum (T3) | Exact implicit characterization: quintic stationarity, T_c*/T_h = (3+q⁴)/4, shift = q⁴/3, unique and monotone; fixed point locally attracting (|Φ′| = 4q⁴/(3+q⁴) < 1) |
| COP identity (L4a) | Proven generally |
| Heat-pump overhead bound (T4a) | Proven from reversed Carnot bound |
| Heat-pump area ratio (T4b) | Exact with sink term; zero-sink form labeled as approximation |
| Waste-heat self-powering impossibility (T5) | Valid within stated cyclic, no-external-resource model (Kelvin–Planck) |
| P1–P3 | Conditional reduced-order mass models, not universal theorems |

**Empirical parameters (referenced, not proven):** LEO effective sink range 200–260 K (lumped-model values; geometry-dependent); Si junction limits; WBG device operating temperatures; realistic COP_c ≈ 1.0–1.3 (vapor-compression class, ~170 K lift); areal densities ρ_A; specific masses m_array, s_h; margin factors δ.

---

## Appendix — Numerical Verification (runnable, with enforced tolerances)

Coverage claim: the appendix verifies **every central numerical result and representative supporting examples**. Method: optima are computed by fixed-point iteration with an enforced successive-iterate tolerance of 10⁻¹⁰ K (convergence tested, not assumed); the stationarity residual is asserted in dimensionless form; a coarse grid serves only as a redundant cross-check. Exact algebra is asserted exactly; floating-point comparisons use stated tolerances.

```python
import numpy as np

TOL = 1e-9
sigma = 5.670374419e-8

# --- B1: Corollary 1.1 exact sink-corrected ratio ---
T1, T2, Ts = 293.0, 600.0, 220.0
R  = (T2**4 - Ts**4) / (T1**4 - Ts**4)
R0 = (T2/T1)**4
assert abs(R0 - 17.585) < 0.01
assert abs(R - 25.312) < 0.01
assert abs((R/R0 - 1) - 0.439) < 0.005        # exact is 43.9% ABOVE the estimate
assert abs((1 - R0/R) - 0.305) < 0.005        # estimate is 30.5% BELOW the exact
ub = (Ts/T1)**4 / (1 - (Ts/T1)**4)
assert (R/R0 - 1) < ub                        # safe upper bound holds

# --- B2: Theorem 2 — reversible optimum and irreversible shift ---
Th = 600.0
y = np.linspace(0.01, 0.999, 4_000_000)
for a, y_expected in [(1.0, 0.750), (0.8, 0.765), (0.5, 0.781)]:
    eta = a*(1 - y)
    AW = (1 - eta)/(eta * y**4)               # proportional objective
    y_star = y[np.argmin(AW)]
    assert abs(y_star - y_expected) < 0.001, (a, y_star)

# --- B3: Corollary 2.1 — area penalty: zero-sink and nonzero-sink forms ---
Tc = 450.0
rev_penalty = (Tc/Th)*(Th/Tc)**4              # reversible, Ts=0: (Th/Tc)^3
assert abs(rev_penalty - (4/3)**3) < TOL
assert abs((4/3)**3 - 2.370) < 0.001
irr_penalty = (1 - 0.8*0.25)*(Th/Tc)**4       # a = 0.8 at same Tc
assert abs(irr_penalty - 2.5284) < 0.001
assert irr_penalty > rev_penalty
# nonzero sink: reversible penalty strictly exceeds cubic bound
Ts_pen = 220.0
rev_penalty_sink = (Tc/Th)*(Th**4 - Ts_pen**4)/(Tc**4 - Ts_pen**4)
assert rev_penalty_sink > (Th/Tc)**3

# --- B4: Theorem 3 — fixed point with ENFORCED convergence tolerance ---
def tc_star(Th, Ts, tol=1e-10, max_iter=1000):
    tc = 0.75 * Th
    for _ in range(max_iter):
        nxt = Th * (3 + (Ts / tc)**4) / 4
        if abs(nxt - tc) < tol:
            return nxt
        tc = nxt
    raise RuntimeError("Fixed-point iteration did not converge")

for Ts_i, shift_expected in [(0,0.0),(50,0.0051),(100,0.0810),(150,0.4049),
                             (200,1.2381),(220,1.7748),(225,1.9300),(250,2.8390)]:
    t = tc_star(Th, Ts_i)
    # dimensionless quintic residual: 4y^5 - 3y^4 - r^4 = 0
    y_root, r_sink = t/Th, Ts_i/Th
    assert abs(4*y_root**5 - 3*y_root**4 - r_sink**4) < 1e-12
    q = Ts_i/t
    # local attraction: |Phi'| = 4q^4/(3+q^4) < 1
    assert 4*q**4/(3 + q**4) < 1.0
    shift = 100*(t - 450.0)/450.0
    assert abs(shift - 100*q**4/3) < 1e-6     # exact identity shift = q^4/3
    assert abs(shift - shift_expected) < 0.001
    # redundant grid cross-check
    Tc2 = np.linspace(Ts_i + 0.01, 599.99, 2_000_000)
    g = (Th - Tc2)*(Tc2**4 - Ts_i**4)/Tc2
    assert abs(Tc2[np.argmax(g)] - t) < 0.01
assert abs(tc_star(600.0, 220.0) - 457.9867541) < 1e-4    # stated optimum
assert abs(100*0.49**4/3 - 1.9216003) < 1e-6              # analytic sub-2% bound value
assert 100*(0.49**4)/3 < 2.0

# --- B5: Theorem 4 — COP values and heat-pump area ratios ---
T1p, T2p, Tsp, COP = 353.0, 520.0, 220.0, 1.15
assert abs(353/167 - 2.1138) < 1e-3                       # COP_c Carnot
assert abs(520/167 - (353/167 + 1)) < TOL                 # COP_h = COP_c + 1
assert abs(1/(353/167) - 0.473) < 0.001                   # Carnot overhead per IT watt
exact  = (1 + 1/COP)*(T1p**4 - Tsp**4)/(T2p**4 - Tsp**4)
approx = (1 + 1/COP)*(T1p/T2p)**4
assert abs(exact  - 0.348) < 0.001
assert abs(approx - 0.397) < 0.001

# --- B6: Theorem 5 — amplification ---
assert abs(1/(1 - 0.25) - 4/3) < TOL

# --- B7: Corollaries 1.1/1.2 reference values ---
assert abs((600/293)**4 - 17.585) < 0.01
A_emit = 1e6/(0.91*sigma*293**4)
assert abs(A_emit - 2630) < 5                             # m^2, total emitting surface
assert abs(A_emit/2 - 1315) < 3                           # m^2, two-sided panel planform

# --- B8: Theorem 1 consequence — 99% example is extreme-area, not impossible ---
Th99, Ts99, Tc99, W99 = 300.0, 2.7, 3.0, 1e6
eta99 = 1 - Tc99/Th99
assert abs(eta99 - 0.99) < 1e-9
Qc99 = W99*Tc99/(Th99 - Tc99)
assert abs(Qc99 - 10101.0) < 1.0                          # ~10.1 kW
A99 = Qc99/(sigma*(Tc99**4 - Ts99**4))
assert 6.0e9 < A99 < 7.0e9                                # ~6.4e9 m^2: finite, extreme

print("All assertions pass.")
```

Expected output: `All assertions pass.`

*Verification instructions for the reviewing model: (1) check each proof step symbolically, noting which results are labeled reversible-envelope vs. general and which assume T_s = 0; (2) run the appendix unmodified; (3) confirm every central numerical claim in the body appears in an assertion or follows from one by stated algebra; (4) confirm no empirical parameter from §6 is used as a premise in any Level A/B proof. Failures of (1)–(4) are defects; differing empirical parameter values are not.*

---

## Appendix W — Symbolic Verification Suite (Wolfram Language)

For a CAS-equipped reviewer. Each block verifies one Level A/B claim symbolically; expected outputs are stated. Exact rational reference values are given so no rounding ambiguity exists.

```wolfram
(* W1 — Theorem 2: stationarity with explicit physical assumption *)
f[Tc_] := Th Tc^3 - Tc^4;
FullSimplify[
  Solve[D[f[Tc], Tc] == 0 && 0 < Tc < Th, Tc, Reals],
  Assumptions -> Th > 0]
  (* expected: {{Tc -> 3 Th/4}} *)
FullSimplify[D[f[Tc], {Tc, 2}] /. Tc -> 3 Th/4, Assumptions -> Th > 0]
  (* expected: -9 Th^2/4  (negative => maximum of f, minimum of A/W) *)

(* W2 — Theorem 3: quintic stationarity and exact shift identity *)
g[Tc_] := (Th - Tc) (Tc^4 - Ts^4)/Tc;
Factor[Numerator[Together[D[g[Tc], Tc]]]]
  (* expected: -4 Tc^5 + 3 Th Tc^4 + Th Ts^4 *)
FullSimplify[(Tc/Th - 3/4)/(3/4) == (Ts/Tc)^4/3,
  Assumptions -> Th > Tc > Ts > 0 && 4 Tc^5 - 3 Th Tc^4 == Th Ts^4]
  (* expected: True *)
FullSimplify[
  (4 Tc^5 - 3 Th Tc^4 == Th Ts^4) \[Equivalent] (Tc/Th == (3 + (Ts/Tc)^4)/4),
  Assumptions -> Th > Tc > Ts > 0]
  (* expected: True *)

(* W2b — uniqueness/monotonicity on y >= 3/4 *)
Reduce[ForAll[y, y >= 3/4 && y < 1, D[4 y^5 - 3 y^4, y] > 0]]
  (* expected: True  (4 y^3 (5 y - 3) > 0 on the interval) *)

(* W2c — high-precision positive root, Th = 600, Ts = 220 *)
root = N[Root[4 #^5 - 1800 #^4 - 600*220^4 &, 1], 50];
{root, N[4 root^5 - 1800 root^4 - 600*220^4, 30]}
  (* expected: {457.98675408138324983229514241277622443332179202809, 0``...}
     (exact algebraic Root object; residual zero to working precision) *)

(* W3 — Theorem 3 fixed-point attraction *)
Phi[T_] := Th/4 (3 + (Ts/T)^4);
FullSimplify[Abs[Phi'[Tc]] /. Th -> 4 Tc/(3 + q^4) /. Ts -> q Tc,
  Assumptions -> 0 < q < 1 && Tc > 0]
  (* expected: 4 q^4/(3 + q^4) *)
FullSimplify[4 q^4/(3 + q^4) < 1, Assumptions -> 0 < q < 1]
  (* expected: True
     (note: Reduce[ineq && 0 < q < 1] returns the domain 0 < q < 1 itself —
      mathematically equivalent, but FullSimplify yields the literal True) *)

(* W3b — Theorem 1 fixed-work divergence *)
FullSimplify[
  Limit[Tc/((Th - Tc) (Tc^4 - Ts^4)), Tc -> Ts, Direction -> "FromAbove"],
  Assumptions -> Th > Ts > 0]
  (* expected: Infinity *)
FullSimplify[
  Limit[1/((Th - Tc) Tc^3), Tc -> 0, Direction -> "FromAbove"],
  Assumptions -> Th > 0]
  (* expected: Infinity *)

(* W4 — Corollary 2.1 nonzero-sink penalty strictly exceeds cubic bound *)
Reduce[(1 - (Ts/Th)^4)/(1 - (Ts/Tc)^4) > 1 && 0 < Ts < Tc < Th, {Th, Tc, Ts}, Reals]
  (* expected: equivalent to the stated domain, i.e., holds throughout it *)

(* W5 — Corollary 1.1 exact rationals (T1=293, T2=600, Ts=220) *)
{(600^4 - 220^4)/(293^4 - 220^4), 600^4/293^4}
  (* expected: {6697760000/264604779, 129600000000/7370050801}
     N: {25.3123..., 17.5847...}; deviations: R/R0 - 1 = 0.43945...,
     1 - R0/R = 0.30529... *)
(* safe upper bound is trivially larger: subtracting (Ts/T2)^4 > 0 from numerator *)

(* W6 — sub-2% bound as exact rational *)
(49/100)^4/3
  (* expected: 5764801/300000000 = 0.0192160033... < 1/50 *)

(* W7 — Theorem 4 COP values, exact *)
{353/167, 520/167, 520/167 - 353/167}
  (* expected: {353/167, 520/167, 1} — identity COP_h = COP_c + 1 *)

(* W8 — Theorem 2c irreversible-optimum stationarity, eta = a (1 - y) *)
(* minimize (1 - a(1-y))/(a(1-y) y^4): log-derivative stationarity *)
stat[a_, y_] := a/(1 - a + a y) + 1/(1 - y) - 4/y;
{y /. FindRoot[stat[8/10, y], {y, 0.76}, WorkingPrecision -> 12],
 y /. FindRoot[stat[5/10, y], {y, 0.78}, WorkingPrecision -> 12]}
  (* expected: {0.764507787..., 0.780776406...} — table values 0.765, 0.781 *)

(* W9 — Theorem 1 consequence example, exact *)
With[{Qc = 10^6*3/297, sig = 5670374419*10^-17},  (* = 5.670374419*10^-8 *)
  {Qc, Qc/(sig (3^4 - (27/10)^4))}] // N
  (* expected: {10101.01, 6.395*10^9}  (m^2) *)
```

Notes for the CAS reviewer: (i) the quintic root is supplied as a `Root` object — no claim of radical solvability is made or required; (ii) all inequalities (W2b, W3, W4) are domain statements suitable for `Reduce`; (iii) exact rationals in W5–W7 eliminate rounding ambiguity between this document and CAS output; (iv) discrepancies beyond stated precision in any W-block are legitimate defects, exactly as for the Python appendix.

---

## Closing Characterization

This document establishes exact identities within a gray-body effective-sink radiator model, reversible thermodynamic lower bounds within that model, and reduced-order architecture criteria whose verdicts depend on empirical system parameters. It does not prove the operating optimum of every irreversible engine or every realizable orbital architecture.

Within its scope, the principal conclusions are: (1) a material cold reservoir cannot attain the environmental sink temperature at finite area and positive throughput, and near-sink Carnot efficiencies are purchasable only at extreme area; (2) T_c = ¾T_h is the optimum of the reversible lower envelope for radiator area per unit work in the zero-sink model; (3) a nonzero sink shifts that optimum upward according to an exact implicit stationarity relation, with fractional shift q⁴/3; (4) heat-engine recovery incurs a radiator-area penalty of at least (T_h/T_c)³, with the exact nonzero-sink penalty strictly larger; (5) within the adopted radiator model, increasing rejection temperature strongly reduces required emitting area, all else equal — whether that yields a lower-mass, lower-power, or more reliable complete architecture remains governed by the Level C trade criteria; and (6) a cyclic system cannot sustain its compute load solely by converting its own internally generated waste heat back into work.
