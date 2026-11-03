"""P1 | Primeira simulação de QUALQUER planta: degrau de tensão."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
V = p.V_max / 2  # TODO 1: troque para p.V_max e compare o pico de corrente
t, i, w = p.simular(V)

k63 = np.argmax(w >= 0.632 * w[-1])
print(f"{p.nome} | degrau de {V:g} V")
print(f"Velocidade final simulada : {w[-1]:10.2f} rad/s")
print(f"Regime teórico (G0 x V)   : {p.ganho_estatico() * V:10.2f} rad/s")
print(
    f"Pico de corrente          : {i.max():10.2f} A   (limite do driver: {p.I_max:g} A)"
)
print(f"Tempo até 63,2%           : {1000 * t[k63]:10.1f} ms")

fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 5))
ax[0].plot(t, w)
ax[0].set_ylabel("omega [rad/s]")
ax[0].grid(True)
ax[1].plot(t, i, color="tab:red")
ax[1].axhline(p.I_max, ls="--", color="gray")
ax[1].set_ylabel("corrente [A]")
ax[1].set_xlabel("tempo [s]")
ax[1].grid(True)
fig.suptitle(f"{p.nome} - degrau de {V:g} V")
Path("figs").mkdir(exist_ok=True)
fig.savefig("figs/p1_degrau.png", dpi=120)
