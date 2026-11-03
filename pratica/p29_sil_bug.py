"""P29 · O SIL pega o bug que a revisão não pega (aula 14).

Um teste que só APROVA não convence ninguém: confira o que o seu verificador REPROVA.
Injetamos um bug plausível — o C saiu com anti-windup desligado (Kaw=0), enquanto o
modelo de referência tem Kaw=100. Nenhuma revisão de código pega (as duas constantes são
razoáveis), mas o SIL diverge por VOLTS, acima do teto do driver, e aponta a amostra exata.

Rode:  uv run python pratica/p29_sil_bug.py controlador.json
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

ok = L.sil(cen, bug=None, fmt="float")
bug = L.sil(cen, bug="antiwindup", fmt="float")
print(f"Referência: Kaw={cen['ganhos']['Kaw']}   ·   Código 'gerado': Kaw=0 (anti-windup desligado)\n")
print(f"  código CORRETO vs modelo : erro {ok['max_abs']:.3e} V  -> {ok['veredito']}")
print(f"  código COM BUG vs modelo : erro {bug['max_abs']:.3f} V  -> {bug['veredito']}")
print(f"  o bug se separa na amostra {bug['amostra_pior']} (quando o comando satura e a integral 'enrola').")
print(f"  teto do driver = {L.NEXABOT['V_max']} V  ->  o erro de {bug['max_abs']:.0f} V passa MUITO do teto.")
print("\nLição: compilar sem aviso não é evidência de equivalência. A comparação numérica\n"
      "é o teste que reprova um bug que a revisão humana aprovaria.")
