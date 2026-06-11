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
