"""P32 · O watchdog e o comando seguro (aula 15).

O cenário que nenhum teste de software pega de dentro: o alvo travou (o código também
travou, então não se detecta a si mesmo). O watchdog vive FORA do laço: impõe o prazo e,
se o alvo não responde a tempo, devolve o comando seguro (torque zero) e DERRUBA o alvo
(um alvo que estourou o prazo pode nunca responder). Ele não tenta descobrir a causa —
essa ignorância deliberada é o que o torna confiável contra falhas não previstas.

Rode:  uv run python pratica/p32_watchdog.py controlador.json
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

prazo = cen["prazo_wd_ms"]
# atrasos crescentes (ms): abaixo do prazo respondem; acima, o watchdog age
atrasos = [prazo * 0.3, prazo * 0.7, prazo * 0.95, prazo * 1.3, prazo * 2.0]
wd = L.watchdog(cen, atrasos)
print(f"Prazo do watchdog (HAL-006): {wd['prazo_wd_ms']} ms = {wd['prazo_wd_ciclos']:.1f} ciclos de {cen['Ts_ms']} ms\n")
print(f"{'atraso(ms)':>11}{'ciclos':>9}  comando")
for l in wd["linhas"]:
    cic = "-" if l["ciclos"] is None else f"{l['ciclos']:.1f}"
    print(f"{l['atraso_ms']:>11.1f}{cic:>9}  {l['comando']}")
print("\nDepois do estouro o objeto alvo não responde mais (foi derrubado). Para refazer o\n"
      "ensaio das células anteriores é preciso criar um alvo novo — isso é de propósito.")
print("\nFronteira segurança x disponibilidade: torque zero reduz o risco físico mas interrompe\n"
      "a missão. O robô ficou seguro e indisponível. Em fábrica, parar é aceitável; num avião\n"
      "em voo, parar significa cair. A escolha vem da análise de perigos, não do watchdog sozinho.")
