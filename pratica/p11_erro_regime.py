"""P11 | Erro em regime do P: previsão teórica x simulação (a05)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cpslab import Planta, malha, metricas

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m, q = p.ganho_estatico(), p.taus()[1], p.queda_por_torque()
t_c, r, T = 4 * tau_m, p.w_op, p.T_op
print(f"G0 = {G0:.5g} rad/s por V | queda por carga q = {q:.5g} rad/s por N.m | r = {r:g} rad/s, T = {T:g} N.m")
print(f"{'Kp*G0':>6}{'Kp':>12}{'erro previsto':>15}{'erro simulado':>15}{'oscilação':>11}")
for KL in (1, 2, 4, 8, 16):                        # TODO 3: acrescente 32. O que acontece?
    Kp = KL / G0
    previsto = (r + T * q) / (1 + KL)              # e = (r + T.q) / (1 + Kp.G0)
    m = metricas(malha(p, Kp, carga=[(0, 0.0), (t_c, T)], t_final=9 * tau_m), p.V_max, t_c)
    sim = "instável" if m["instavel"] else f"{m['erro_final']:.3f}"
    osc = "-" if m["instavel"] else f"{m['oscilacao']:.3g}"
    print(f"{KL:>6}{Kp:>12.4g}{previsto:>15.3f}{sim:>15}{osc:>11}")
print("Dobrar Kp corta o erro quase pela metade, mas ele NUNCA zera: o P precisa de erro para gerar tensão.")
print("Quando cálculo e simulação independentes concordam, temos evidência de que entendemos o modelo.")
