"""P9 | Memorial de cálculo GENÉRICO: itens (a), (b), (c) para qualquer planta.json.

EXERCÍCIO: complete os TODOs escrevendo as fórmulas (sem usar os métodos prontos
da cpslab). Enquanto houver TODO em aberto, o script avisa o que falta.
Depois compare com:  uv run python cpslab.py relatorio planta.json
"""
import sys, json
import numpy as np

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "planta.json", encoding="utf-8"))
R, L, Kt, Ke, J, B = d["R"], d["L"], d["Kt"], d["Ke"], d["J"], d["B"]
V_max, I_max, Ts, w, T = d["V_max"], d["I_max"], d["Ts"], d["w_op"], d["T_op"]

# (a) modelo em espaço de estados, polos e constantes de tempo
A = np.array([[-R / L, -Ke / L], [Kt / J, -B / J]])  # TODO a1
polos = np.linalg.eigvals(A).real
tau_e = 1 / abs(polos.min())  # TODO a2
tau_m = 1 / abs(polos.max())  # TODO a3
# (b) ponto de operação, com as derivadas iguais a zero:  Kt*i = B*w + T   e   V = R*i + Ke*w
i_ss = (B * w + T) / Kt  # TODO b1
V_ss = R * i_ss + Ke * w  # TODO b2
# (c) amostragem
amostras = tau_m / Ts  # TODO c1

faltam = [nome for nome, v in [("a1 (A)", A), ("a2 (tau_e)", tau_e), ("a3 (tau_m)", tau_m),
                               ("b1 (i_ss)", i_ss), ("b2 (V_ss)", V_ss), ("c1 (amostras)", amostras)] if v is None]
if faltam:
    print("⚠️  Memorial incompleto. Complete os TODOs:", ", ".join(faltam))
    sys.exit(1)

polos = np.sort(np.linalg.eigvals(A).real)
print(f"(a) A = {np.round(A, 4).tolist()}")
print(f"    polos = {polos[0]:.4g} e {polos[1]:.4g} rad/s | tau_e = {1000*tau_e:.4g} ms | tau_m = {1000*tau_m:.4g} ms")
print(f"(b) i_ss = {i_ss:.4g} A ({100*i_ss/I_max:.0f}% de I_max) | V_ss = {V_ss:.4g} V | folga = {V_max - V_ss:.4g} V")
print(f"(c) amostras por tau_m = {amostras:.3g}")
