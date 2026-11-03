"""P7 | Controlabilidade, observabilidade e o teto do driver."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
rc, ro = p.postos()
print(f"posto ctrb = {rc}/2 | posto obsv (só velocidade) = {ro}/2")
rc0, ro0 = replace(p, Kt=0.0).postos()          # TODO 6: por que Kt = 0 derruba os dois?
print(f"com Kt = 0: ctrb {rc0}/2 | obsv {ro0}/2")
_, pl = p.polos()
print(f"\nIr de 0 a {p.w_op:g} rad/s com polo duplo p (limite do driver: {p.V_max:g} V)")
for k in range(1, 15):                           # TODO 7: ache o polo exato do limite
    pol = k * pl
    u0 = p.u0_polo_duplo(pol)
    print(f"p = {pol:9.2f} ({k:2d}x o polo mecânico) | u(0) = {u0:8.2f} V | {'cabe' if u0 <= p.V_max else 'SATURA'}")