"""P17 | Memorial de cálculo GENÉRICO, item (d): controle digital da sua planta.

EXERCÍCIO: complete os TODOs com as fórmulas (sem usar os métodos prontos da cpslab).
Use os ganhos do CHEFÃO do jogo (ou deixe os sugeridos). Depois o script confere tudo
com a cpslab e escreve figs/memorial_d.md para você levar ao relatório.
"""
import sys, json, math
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from cpslab import Planta, malha, metricas, margem_fase_digital, ts_critico, desvio_cosim

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "planta.json", encoding="utf-8"))
R, L, Kt, Ke, J, B, V_max, Ts = d["R"], d["L"], d["Kt"], d["Ke"], d["J"], d["B"], d["V_max"], d["Ts"]

# (d0) seus ganhos (chefão do jogo). Sugestão: Kp = 3/G0, Ti = tau_mec/2, Kaw*Ts = 0,5, Ts da planta
G0 = Kt / (R * B + Kt * Ke)  # TODO d1
tau_m = p.taus()[1]  # TODO d2
Kp = 3 / G0  # TODO d3
Ki = Kp / (tau_m / 2)  # TODO d4
Kaw = 0.5 / Ts  # TODO d5
q = R / (R * B + Kt * Ke)
erro_P = (p.w_op + p.T_op * q) / (1 + Kp * G0)  # TODO d6

faltam = [n for n, v in [("d1", G0), ("d2", tau_m), ("d3", Kp), ("d4", Ki), ("d5", Kaw), ("d6", erro_P)] if v is None]
if faltam:
    print("⚠️  Memorial (d) incompleto. Complete os TODOs:", ", ".join(faltam)); sys.exit(1)

carga = [(0, 0.0), (4 * tau_m, p.T_op)]
m = metricas(malha(p, Kp, Ki, Kaw=Kaw, carga=carga, t_final=9 * tau_m), V_max, 4 * tau_m)
mj = metricas(malha(p, Kp, Ki, Kaw=Kaw, carga=carga, t_final=9 * tau_m, atraso=1), V_max, 4 * tau_m)
pm0, wc = margem_fase_digital(p, Kp, Ki)
pm1, _ = margem_fase_digital(p, Kp, Ki, atraso=1)
tc = ts_critico(p, Kp, Ki)
dev2 = desvio_cosim(p, Kp, Ki, Kaw, 2, carga=carga, t_final=8 * tau_m)[1]
ok = lambda c: "ATENDE" if c else "NÃO ATENDE"
L_ = [
    f"## (d) Controle digital · {p.nome} [{p.codigo or p.origem}]",
    f"- Planta: G0 = Kt/(R·B + Kt·Ke) = {G0:.5g} rad/s/V (cpslab: {p.ganho_estatico():.5g}); tau_mec = {1000 * tau_m:.4g} ms",
    f"- Controlador: PI discreto (Tustin), u[k] = Kp·e[k] + I[k], I[k] = I[k-1] + Ki·Ts·(e[k]+e[k-1])/2",
    f"- Ganhos: Kp = {Kp:.4g} V/(rad/s) (Kp·G0 = {Kp * G0:.3g}), Ki = {Ki:.4g} V/rad (Ti = {1000 * Kp / Ki:.4g} ms)",
    f"- Saturação: |u| <= {V_max:g} V; anti-windup por back-calculation, I += Kaw·Ts·(u - v), Kaw = {Kaw:.4g} 1/s",
    f"- Sem a integral, o erro de regime seria (w_op + T·q)/(1 + Kp·G0) = {erro_P:.4g} rad/s: por isso o I é necessário",
    f"- Ts = {1000 * Ts:g} ms -> {tau_m / Ts:.1f} amostras por tau_mec (regra: 10 a 20) | Ts crítico = {1000 * tc:.4g} ms",
    f"- Margem de fase (atraso Ts/2): {pm0:.1f} graus em wc = {wc:.4g} rad/s -> {ok(pm0 >= 45)} (>= 45)",
    f"- Perdendo 1 ciclo (jitter): {pm1:.1f} graus -> {ok(pm1 >= 30 and not mj['instavel'])} (>= 30 e estável)",
    f"- Ensaio com carga {p.T_op:g} N·m: erro final {m['erro_pct']:.3f} % ({ok(abs(m['erro_pct']) <= 1)}), sobressinal {m['sobressinal']:.2f} % ({ok(m['sobressinal'] <= 10)}),",
    f"  acomodação {1000 * m['t_acomodacao']:.0f} ms, ciclos saturados {m['ciclos_sat']} (no fim: {m['sat_final']})",
    f"- Co-simulação com H = 2·Ts: desvio {dev2:.3f} % do alvo",
]
print("\n".join(L_))
Path("figs").mkdir(exist_ok=True); Path("figs/memorial_d.md").write_text("\n".join(L_) + "\n", encoding="utf-8")
print("\nSalvo em figs/memorial_d.md")
