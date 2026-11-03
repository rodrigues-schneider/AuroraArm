"""P8 | Observabilidade como detector de mentira: replay no sensor de velocidade."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import control as ct
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
A, B, C, _ = p.matrizes(); pr, _ = p.polos(); te, tm = p.taus()
Lo = ct.place(A.T, C.T, [1.8 * pr, 2.0 * pr]).T     # observador mais rápido que a planta
T_ATAQUE = 4 * tm                                   # TODO 8: teste 9*tm (já em regime) e 1*tm
t_mud = 6 * tm                                      # a rotina muda a tensão aqui
def V(t): return 0.5 * p.V_max if t < t_mud else 0.75 * p.V_max
dt = te / 20
t, i_real, w_real = p.simular(V, t_final=12 * tm, dt=dt)
w_enc = w_real.copy(); k = np.searchsorted(t, T_ATAQUE); w_enc[k:] = w_real[k]   # leitura congelada
xh = np.zeros(2); i_est = np.zeros_like(t)
for n in range(t.size - 1):
    xh = xh + dt * (A @ xh + B[:, 0] * V(t[n]) + Lo[:, 0] * (w_enc[n] - xh[1]))
    i_est[n + 1] = xh[0]
lim = 0.1 * p.I_max
res = np.abs(i_est - i_real); ok = t > 0.5 * tm
al = np.argmax((res > lim) & ok)
print(f"ataque em t = {1000*T_ATAQUE:.1f} ms | mudança de tensão em t = {1000*t_mud:.1f} ms | limiar {lim:.2f} A")
print(f"ALARME em t = {1000*t[al]:.1f} ms" if al else "Nenhum alarme: o ataque passou despercebido!")