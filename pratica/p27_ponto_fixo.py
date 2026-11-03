"""P27 · Ponto flutuante x ponto fixo (aula 13).

Mostra o degrau e a faixa do SEU formato Q(m.n), compara dois integradores (float x
ponto fixo) somando o mesmo erro por N ciclos e reproduz os três modos de falha:
  (1) incremento que arredonda para ZERO -> a integral para de integrar;
  (2) troca precisão x faixa (mais fração = menos alcance);
  (3) estouro de 32 bits -> lixo no atuador.

Rode:  uv run python pratica/p27_ponto_fixo.py controlador.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import u04lab as L

cam = sys.argv[1] if len(sys.argv) > 1 else "controlador.json"
cen = json.load(open(cam, encoding="utf-8")) if os.path.exists(cam) else L.gerar_cenario("RA2026999")
from u04_aurora import configurar_planta
configurar_planta(L, cen)
n = cen["qn"]
qi = L.q_info(cen["qm"], cen["qn"])

print(f"Formato Q{qi['m']}.{qi['n']}  ({qi['bits']} bits)")
print(f"  menor degrau representável : {qi['degrau']:.3e}")
print(f"  faixa                      : [{qi['min']:.0f}, {qi['max']:.0f}]")

Ki, Ts = cen["ganhos"]["Ki"], cen["Ts_ms"] / 1000.0
acc = L.acumulador(cen["erro_ciclo"], cen["ciclos"], Ki, Ts, n)
print(f"\nAcumulador: {cen['ciclos']} ciclos somando erro {cen['erro_ciclo']} por ciclo")
print(f"  float : {acc['acc_float']:.6f}")
print(f"  Q{qi['m']}.{qi['n']}: {acc['acc_q']:.6f}")
print(f"  desvio: {acc['desvio']:.3e} = {acc['degraus']:.1f} degraus de quantização")

print("\n--- modo de falha 1: incremento vira zero ---")
for e in (cen["erro_ciclo"], cen["erro_ciclo"] / 50):
    inc_q = L.to_q(Ki * Ts * e, n)
    print(f"  erro/ciclo={e:.6f} -> incremento em Q = {inc_q}" + ("   <-- VIROU ZERO: integral congela!" if inc_q == 0 else ""))

print("\n--- modo de falha 2: precisão x faixa ---")
for (m, nn) in ((8, 24), (16, 16), (24, 8)):
    q = L.q_info(m, nn)
    print(f"  Q{m}.{nn}: degrau={q['degrau']:.2e}  faixa=±{q['max']:.0f}")

print("\n--- modo de falha 3: estouro de 32 bits ---")
for v in (qi["max"] * 0.9, qi["max"] * 1.5):
    print(f"  guardar {v:.1f}: {'cabe' if L.cabe_32(v, n) else 'NAO CABE -> resultado vira lixo no atuador'}")
