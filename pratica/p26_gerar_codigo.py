"""P26 · Da modelagem ao código (aula 13).

Gera o passo do PID em C a partir do controlador (artefato derivado) e imprime a
assinatura de rastreabilidade. Demonstra que a geração é determinística e que mexer
num ganho na 3a casa decimal muda a assinatura COMPLETAMENTE.

REQ-CODE-001 (código é artefato derivado) · REQ-CODE-003 (assinatura liga código à origem).
Rode da pasta lab_cps:  uv run python pratica/p26_gerar_codigo.py controlador.json
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

ctrl = L.ctrl_de_cenario(cen)
header, src = L.gerar_c(ctrl, "float")
os.makedirs("figs", exist_ok=True)
with open("figs/pid_gen.h", "w", encoding="utf-8") as f:
    f.write(header)
with open("figs/pid_gen.c", "w", encoding="utf-8") as f:
    f.write(src)

print(f"Controlador do {cen['nome']} (cenário {cen['codigo']})")
print("  arquivos gerados: figs/pid_gen.h, figs/pid_gen.c")
print("  ganhos no código:", {k: getattr(ctrl, k) for k in ("Kp", "Ki", "Kd", "Kaw")})
print("  período (contrato): Ts =", cen["Ts_ms"], "ms")
print("  assinatura:", L.assinatura(ctrl, "float"))

# determinismo: gerar de novo -> MESMA assinatura
print("\nGerar duas vezes com os mesmos parâmetros:")
print("  1a:", L.assinatura(L.ctrl_de_cenario(cen), "float")[:24], "...")
print("  2a:", L.assinatura(L.ctrl_de_cenario(cen), "float")[:24], "...  (idênticas => determinístico)")

# mudar 1 ganho na 3a casa -> assinatura totalmente diferente
cen2 = json.loads(json.dumps(cen))
cen2["ganhos"]["Kp"] = round(cen["ganhos"]["Kp"] + 0.001, 3)
a1 = L.assinatura(L.ctrl_de_cenario(cen), "float")
a2 = L.assinatura(L.ctrl_de_cenario(cen2), "float")
iguais = sum(1 for x, y in zip(a1, a2) if x == y)
print(f"\nMudando Kp de {cen['ganhos']['Kp']} para {cen2['ganhos']['Kp']} (3a casa):")
print("  antiga :", a1[:24], "...")
print("  nova   :", a2[:24], "...")
print(f"  caracteres iguais entre as duas: {iguais}/64  (muda quase tudo — é por isso que compara por IGUAL)")
