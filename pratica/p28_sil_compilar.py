"""P28 · Software-in-the-Loop: compilar e comparar (aula 14).

Compila o C de verdade (gcc/clang, -O2) e carrega via ctypes; se não houver compilador,
usa o equivalente em Python. Alimenta a MESMA sequência no modelo e no código e mede a
divergência em épsilons de máquina.  REQ-CODE-002 (equivalência modelo x código).

Rode:  uv run python pratica/p28_sil_compilar.py controlador.json
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

cc = L.compilador_disponivel()
print("Compilador C:", cc or "NÃO encontrado (usando equivalente em Python)")
print(f"Épsilon de máquina (double, 64 bits): {L.EPS:.3e}\n")

rel = L.sil(cen, bug=None, fmt="float")
print(f"[{rel['modo']}] modelo x código (double):")
print(f"  erro máx = {rel['max_abs']:.3e}  ({rel['epsilons']:.1f} épsilons)")
print(f"  veredito : {rel['veredito']}")
print("  -> em double, a MESMA sequência de operações dá erro exatamente zero; com -O2 o\n"
      "     compilador pode reordenar as contas e aparecer uns poucos épsilons. Ambos são equivalentes.")

print("\nAgora a variante em ponto fixo (o degrau NÃO some na comparação):")
relfx = L.sil(cen, bug=None, fmt="q%d" % cen["qn"], qn=cen["qn"])
print(f"  erro máx = {relfx['max_abs']:.3e}  = {relfx['max_abs']*(1<<cen['qn']):.0f} degraus")
print(f"  veredito : {relfx['veredito']}")
print("  (fisicamente irrelevante no atuador, mas tem que constar no relatório — a integral acumula.)")
