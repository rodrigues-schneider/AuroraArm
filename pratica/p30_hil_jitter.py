"""P30 · Hardware-in-the-Loop: os 5 ms de verdade (aula 15).

Fecha a malha com o alvo loopback (planta simulada no host, PID no 'alvo') e mede o
JITTER: o laço deveria rodar a cada Ts, mas cada ciclo leva um tempo diferente. Duas
medidas importam: o jitter médio e o jitter de PIOR CASO (a cauda da direita).

Observação: o jitter real depende do sistema operacional e da carga da máquina no
momento do ensaio — isso tem que constar no relatório. Aqui usamos o perfil determinístico
do seu RA para você poder conferir os números; p30b mede o relógio de verdade.

Rode:  uv run python pratica/p30_hil_jitter.py controlador.json
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

tr = L.malha_hil(cen)
print(f"HIL {cen['nome']} · Ts={cen['Ts_ms']} ms · ref={cen['ref']} rad/s")
print(f"  controle convergiu? {'sim' if tr['convergiu'] else 'não'} (w final = {tr['w'][-1]:.1f} rad/s)\n")

jit = L.jitter_sim(cen)
print(f"Temporização medida ({jit['n']} ciclos):")
print(f"  período nominal : {jit['nominal_ms']:.3f} ms")
print(f"  período médio   : {jit['medio_ms']:.3f} ms   (jitter médio {jit['jitter_medio_ms']:.3f} ms)")
print(f"  PIOR caso       : {jit['max_ms']:.3f} ms   (jitter de pior caso {jit['jitter_max_ms']:.3f} ms)")
print(f"  desvio padrão   : {jit['desvio_padrao_ms']:.3f} ms")
print("\nSe o período MÉDIO ficasse muito acima do nominal, não seria jitter: seria o laço não\n"
      "cabendo no período (problema de projeto). Aqui o médio fica perto do nominal — é jitter.")

os.makedirs("figs", exist_ok=True)
with open("figs/jitter_u04.txt", "w", encoding="utf-8") as f:
    f.write("duracao_ms\n" + "\n".join(f"{d:.4f}" for d in jit["durs"]))
print("\n[ok] durações salvas em figs/jitter_u04.txt (histograma para o relatório).")
