"""P12 | P, I, PI e o windup: o integrador que não sabia parar (a06)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from cpslab import Planta, malha, metricas

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m = p.ganho_estatico(), p.taus()[1]
# 1) cada ação sozinha e juntas (sem carga, alvo w_op)
casos = {"só P": (2 / G0, 0.0), "só I": (0.0, 2 / G0 / tau_m), "PI": (2 / G0, 2 / G0 / tau_m)}
print("1) Ações do controlador (alvo w_op, sem carga)")
for nome, (Kp, Ki) in casos.items():
    m = metricas(malha(p, Kp, Ki, Kaw=0.5 / p.Ts, t_final=10 * tau_m), p.V_max)
    print(f"   {nome:<5} Kp={Kp:<9.4g} Ki={Ki:<9.4g} erro={m['erro_pct']:8.3f}%  sobressinal={m['sobressinal']:6.2f}%")
# 2) windup: alvo alto (60% do máximo físico) com PI agressivo
ref = 0.6 * G0 * p.V_max
Kp, Ki = 6 / G0, 6 / G0 / (tau_m / 4)
print(f"\n2) Windup | alvo {ref:.2f} rad/s | Kp={Kp:.4g} Ki={Ki:.4g} | V_max={p.V_max:g} V")
print(f"{'Kaw*Ts':>7}{'Kaw [1/s]':>11}{'sobressinal [%]':>17}{'ciclos no teto':>16}{'acomodação [ms]':>17}")
plt.figure(figsize=(8, 4))
for kts in (0, 0.05, 0.1, 0.25, 0.5, 1.0):        # TODO 4: qual o MENOR Kaw*Ts com sobressinal <= 5%?
    r = malha(p, Kp, Ki, Kaw=kts / p.Ts, ref=ref, t_final=6 * tau_m)
    m = metricas(r, p.V_max)
    print(f"{kts:>7g}{kts / p.Ts:>11.4g}{m['sobressinal']:>17.2f}{m['ciclos_sat']:>16d}{1000 * m['t_acomodacao']:>17.1f}")
    plt.plot(r["t"], r["w"], label=f"Kaw*Ts={kts:g}")
plt.axhline(ref, ls="--", color="gray"); plt.xlabel("tempo [s]"); plt.ylabel("omega [rad/s]"); plt.grid(True); plt.legend()
Path("figs").mkdir(exist_ok=True); plt.savefig("figs/p12_windup.png", dpi=120)
print("O problema que aparece DEPOIS do teto foi acumulado DURANTE o teto.")
