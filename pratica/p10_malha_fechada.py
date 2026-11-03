"""P10 | Malha aberta x P x PI sob carga: medir, comparar e corrigir (a05)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from cpslab import Planta, malha, metricas

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m = p.ganho_estatico(), p.taus()[1]
t_c = 4 * tau_m                                   # a carga nominal entra em 4 tau_mec
carga = [(0, 0.0), (t_c, p.T_op)]                 # TODO 1: teste o dobro de p.T_op
Kp_P = 4 / G0                                     # TODO 2: dobre e veja o erro do P cair pela metade
Kp, Ki = 2 / G0, 2 / G0 / (tau_m / 2)             # PI: Ki = Kp / Ti, com Ti = tau_mec/2
ensaios = {
    "malha aberta": malha(p, None, carga=carga, t_final=9 * tau_m),
    "P": malha(p, Kp_P, carga=carga, t_final=9 * tau_m),
    "PI": malha(p, Kp, Ki, Kaw=0.5 / p.Ts, carga=carga, t_final=9 * tau_m),
}
print(f"{p.nome} | alvo {p.w_op:g} rad/s | carga {p.T_op:g} N.m em {1000*t_c:.0f} ms | Ts = {1000*p.Ts:g} ms")
print(f"Kp_P = {Kp_P:.4g} | PI: Kp = {Kp:.4g} V/(rad/s), Ki = {Ki:.4g} V/rad")
print(f"{'ensaio':<14}{'w_final [rad/s]':>17}{'erro [%]':>11}{'sobressinal [%]':>17}{'ciclos sat.':>13}")
for nome, r in ensaios.items():
    m = metricas(r, p.V_max, t_c)
    print(f"{nome:<14}{m['w_final']:>17.2f}{m['erro_pct']:>11.3f}{m['sobressinal']:>17.2f}{m['ciclos_sat']:>13d}")
print("A malha aberta não sabe que a carga entrou. O P reage, mas guarda erro. O PI volta ao alvo.")
fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
for nome, r in ensaios.items():
    ax[0].plot(r["t"], r["w"], label=nome); ax[1].step(r["t"], r["u"], where="post", label=nome)
ax[0].axhline(p.w_op, ls="--", color="gray"); ax[1].axhline(p.V_max, ls=":", color="red")
for a in ax: a.axvline(t_c, color="orange", ls=":"); a.grid(True); a.legend()
ax[0].set_ylabel("omega [rad/s]"); ax[1].set_ylabel("tensão aplicada [V]"); ax[1].set_xlabel("tempo [s]")
Path("figs").mkdir(exist_ok=True); plt.savefig("figs/p10_malha_fechada.png", dpi=120)
