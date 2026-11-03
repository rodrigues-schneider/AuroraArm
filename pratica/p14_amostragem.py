"""P14 | Quanto dá para espaçar as fotografias? Ts, margem de fase e instabilidade (a07)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from cpslab import Planta, malha, metricas, ts_critico, margem_fase_digital

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m = p.ganho_estatico(), p.taus()[1]
Kp, Ki = 6 / G0, 6 / G0 / tau_m                    # PI "esperto" da M5 do jogo
print(f"tau_mec = {1000 * tau_m:.4g} ms | regra de bolso (10 a 20 amostras): Ts entre {1000 * tau_m / 20:.4g} e {1000 * tau_m / 10:.4g} ms")
print(f"{'Ts [ms]':>9}{'fs [Hz]':>10}{'amostras/tau':>14}{'margem [graus]':>16}  estado")
for frac in (1 / 40, 1 / 20, 1 / 10, 1 / 5, 1 / 3, 1 / 2):   # TODO 6: inclua o Ts da sua planta (p.Ts)
    Ts = frac * tau_m
    pm, _ = margem_fase_digital(p, Kp, Ki, Ts)
    m = metricas(malha(replace(p, Ts=Ts), Kp, Ki, Kaw=0.5 / Ts, t_final=9 * tau_m), p.V_max)
    est = "INSTÁVEL" if m["instavel"] else ("oscilando" if m["oscilacao"] > 0.01 * p.w_op else "estável")
    print(f"{1000 * Ts:>9.3f}{1 / Ts:>10.1f}{tau_m / Ts:>14.1f}{pm:>16.1f}  {est}")
tc = ts_critico(p, Kp, Ki)
print(f"\nTs crítico (malha discreta fica instável): {1000 * tc:.4g} ms")
print(f"Margem de fase no Ts da planta ({1000 * p.Ts:g} ms): {margem_fase_digital(p, Kp, Ki)[0]:.2f} graus")
print("Por que Ts/2? O comando calculado em k*Ts fica congelado até (k+1)*Ts: chega, em média, meio período atrasado.")
