"""P3 | Leis físicas -> espaço de estados, para os números da SUA planta."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import sympy as sp
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
i, w, V, Tc, di, dw = sp.symbols("i omega V T_c di domega")
R, L, Kt, Ke, J, B = sp.symbols("R L K_t K_e J B", positive=True)
sol = sp.solve([sp.Eq(L * di, V - R * i - Ke * w),          # Kirchhoff
                sp.Eq(J * dw, Kt * i - B * w - Tc)], [di, dw])  # Newton
f = sp.Matrix([sol[di], sol[dw]])
A_s, B_s = f.jacobian(sp.Matrix([i, w])), f.jacobian(sp.Matrix([V]))
sp.pprint(A_s); sp.pprint(B_s)
num = {R: p.R, L: p.L, Kt: p.Kt, Ke: p.Ke, J: p.J, B: p.B}
A_n = np.array(A_s.subs(num), dtype=float)
A_c, B_c, _, _ = p.matrizes()
print("A =\n", np.round(A_n, 4))
print(f"diferença SymPy x cpslab: {abs(A_n - A_c).max():.1e}")