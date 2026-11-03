"""P2 | Malha aberta sob carga... e sob ataque (vale para qualquer planta)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
tau_m = p.taus()[1]
V_cmd = p.w_op / p.ganho_estatico()  # tensão calculada UMA vez, sem carga
T_carga = p.T_op  # TODO 2: teste metade e o dobro de p.T_op
ataque = 0.10  # TODO 3: invasor reduz o comando em 10%
t_c, t_a = 10 * tau_m, 20 * tau_m  # carga e ataque: 10 tau de intervalo = regime


def V(t):
    return V_cmd * (1 - ataque) if t >= t_a else V_cmd


def T(t):
    return T_carga if t >= t_c else 0.0


t, i, w = p.simular(V, T, t_final=30 * tau_m)


def w_em(ts):
    return w[np.searchsorted(t, ts) - 1]


print(f"Referência: {p.w_op:g} rad/s | comando calculado: {V_cmd:.3f} V")
print(f"antes da carga        : {w_em(t_c):9.2f} rad/s")
print(
    f"com carga ({T_carga:g} N.m) : {w_em(t_a):9.2f} rad/s  (queda {100 * (1 - w_em(t_a) / p.w_op):.1f}%)"
)
print(
    f"carga + ataque        : {w[-1]:9.2f} rad/s  (queda {100 * (1 - w[-1] / p.w_op):.1f}%)"
)
queda = p.queda_por_torque()  # rad/s perdidos por N.m de carga
print(
    f"regime teórico com carga  : {p.w_op - T_carga * queda:9.2f} rad/s  (w_op - T*R/(R*B + Kt*Ke))"
)
print(
    f"regime teórico com ataque : {(1 - ataque) * p.w_op - T_carga * queda:9.2f} rad/s"
)
print("O controlador percebeu? NÃO: em malha aberta ninguém mede a saída.")
plt.figure(figsize=(8, 4))
plt.plot(t, w)
plt.axhline(p.w_op, ls="--", color="gray")
plt.axvline(t_c, color="orange", ls=":")
plt.axvline(t_a, color="red", ls=":")
plt.xlabel("tempo [s]")
plt.ylabel("omega [rad/s]")
plt.grid(True)
Path("figs").mkdir(exist_ok=True)
plt.savefig("figs/p2_malha_aberta.png", dpi=120)
