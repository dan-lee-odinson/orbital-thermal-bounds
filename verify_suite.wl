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
