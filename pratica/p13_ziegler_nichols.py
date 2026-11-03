"""P13 | Ganho crítico, Ziegler-Nichols e o derivativo filtrado (a06)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from cpslab import Planta, malha, metricas, ganho_critico, ziegler_nichols

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m = p.ganho_estatico(), p.taus()[1]
Ku, Pu = ganho_critico(p)
print(f"Ganho crítico Ku = {Ku:.4g} V/(rad/s)  (Ku*G0 = {Ku * G0:.4g}) | Pu = {1000 * Pu:.4g} ms = {Pu / p.Ts:.3g} amostras")
print("Na planta contínua esse limite não existe: quem cria o Ku é a amostragem (atraso de Ts/2).")
carga = [(0, 0.0), (4 * tau_m, p.T_op)]
for tipo in ("P", "PI", "PID"):
    g = ziegler_nichols(Ku, Pu, tipo)
    m = metricas(malha(p, g["Kp"], g["Ki"], g["Kd"], Kaw=0.5 / p.Ts, carga=carga, t_final=9 * tau_m), p.V_max, 4 * tau_m)
    est = "instável" if m["instavel"] else f"erro={m['erro_pct']:7.3f}%  sobressinal={m['sobressinal']:6.2f}%"
    print(f"ZN {tipo:<3} Kp={g['Kp']:<9.4g} Ki={g['Ki']:<9.4g} Kd={g['Kd']:<9.4g} {est}")
Kp, Ki = 2 / G0, 2 / G0 / (tau_m / 2)              # TODO 5: compare com a sua sintonia do jogo (M2)
m = metricas(malha(p, Kp, Ki, Kaw=0.5 / p.Ts, carga=carga, t_final=9 * tau_m), p.V_max, 4 * tau_m)
print(f"manual Kp={Kp:<9.4g} Ki={Ki:<9.4g}              erro={m['erro_pct']:7.3f}%  sobressinal={m['sobressinal']:6.2f}%")
# derivativo puro x filtrado: o mesmo sinal medido com ruído de 0,3% de w_op
g = ziegler_nichols(Ku, Pu, "PID")
y = np.array(malha(p, g["Kp"], g["Ki"], g["Kd"], Kaw=0.5 / p.Ts, ruido=0.003, t_final=9 * tau_m)["y"])
D_puro = -g["Kd"] * np.diff(y) / p.Ts               # derivada "crua": diferença de amostras / Ts
Tf = 2 * p.Ts                                        # TODO 6: teste Tf = Ts/2 e Tf = 5*Ts
a, D_filt, Df = Tf / (Tf + p.Ts), [], 0.0
for dk in D_puro:
    Df = a * Df + (1 - a) * dk; D_filt.append(Df)   # filtro de 1ª ordem (mesma fórmula do PIDDiscreto)
meio = len(D_puro) // 2
print(f"termo D puro    : desvio-padrão em regime = {np.std(D_puro[meio:]):.4g} V")
print(f"termo D filtrado: desvio-padrão em regime = {np.std(D_filt[meio:]):.4g} V  (Tf = {1000 * Tf:g} ms)")
print("O derivativo puro transforma ruído do sensor em picos de tensão; o filtro reduz esses picos.")
