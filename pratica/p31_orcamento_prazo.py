"""P31 · O jitter cabe no orçamento? (aula 15, ligando com a aula 11).

Na U03 você provou o pior caso CONTANDO ciclos. Mas se cada ciclo durar mais que Ts, a
quantidade de milissegundos muda. Aqui a pergunta é: com o jitter medido agora, o prazo
ainda é respeitado?  O cenário é conservador de propósito (supõe TODO ciclo no pior tempo)
— e isso precisa estar explícito no relatório.  REQ-SAFE-006.

Rode:  uv run python pratica/p31_orcamento_prazo.py controlador.json
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

jit = L.jitter_sim(cen)
orc = L.orcamento_prazo(cen, jit["jitter_max_ms"])
print(f"Pior caso herdado da U03: {orc['periodos']} períodos")
print(f"Limite do requisito      : {orc['limite_ms']} ms\n")
print(f"  prazo NOMINAL   (todo ciclo = {cen['Ts_ms']} ms)        : {orc['nominal_ms']:.1f} ms  "
      f"-> folga {orc['folga_nominal_ms']:.1f} ms")
print(f"  prazo PESSIMISTA(todo ciclo = {cen['Ts_ms']+jit['jitter_max_ms']:.3f} ms): {orc['pessimista_ms']:.1f} ms  "
      f"-> folga {orc['folga_pessimista_ms']:.1f} ms")
print(f"\n  VEREDITO (pior caso): {'PASSA' if orc['passa_pessimista'] else 'VIOLA o prazo'}")
if not orc["passa_pessimista"]:
    print("  -> decisões de projeto (nenhuma é 'aceitar assim mesmo'):\n"
          "     reduzir o jitter · reduzir o período de amostragem · renegociar o prazo.")
print("\nNota para o relatório: o cenário supõe que TODOS os ciclos ocorrem no pior tempo já\n"
      "observado — o que na prática não acontece. É pessimista por construção; diga isso.")
