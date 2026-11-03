"""p22 - Autômato temporizado do watchdog e a varredura do atraso de detecção.

REQ-SAFE-001 é uma abstração de tempo zero. No robô físico, entre o obstáculo aparecer
e o torque chegar a zero existem atrasos reais (filtro do sensor, varredura do laço,
ciclo perdido por jitter). Aqui verificamos o PIOR CASO por enumeração exaustiva do
tempo discreto e achamos a fronteira exata do prazo da SUA máquina (gerada pelo RA).

Uso:  uv run python pratica/p22_timed.py planta_u03.json
"""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def carregar(argv):
    if argv and os.path.exists(argv[0]):
        with open(argv[0], encoding="utf-8") as f:
            return json.load(f)
    ra = argv[0] if argv else "RA2026999"
    return L.gerar_cenario(ra)


def main():
    cen = carregar(sys.argv[1:])
    Ts, prazo, cp = cen["Ts_ms"], cen["prazo_ms"], cen["ciclos_perdidos"]
    a0 = cen["atraso_projeto"]
    print("=" * 66)
    print(f" p22 · Watchdog do {cen['nome']}  (cenário {cen['codigo']})")
    print("=" * 66)
    print(f"Ts = {Ts} ms | prazo REQ-SAFE-006 = {prazo} ms ({prazo // Ts} períodos) | "
          f"{cp} ciclo(s) de atuação podem se perder\n")

    pc, ncam = L.pior_caso(a0, cp)
    print(f"Projeto atual (atraso_deteccao_max = {a0} períodos = {a0 * Ts} ms):")
    print(f"  o ambiente tem {ncam} trajetórias não determinísticas (2·{a0}+2)")
    print(f"  PIOR CASO = {pc} períodos = {pc * Ts} ms  ->  folga de {prazo - pc * Ts} ms "
          f"({'CONFORME' if pc * Ts <= prazo else 'VIOLA'})\n")

    vr = L.varredura(Ts, prazo, cp)
    print("Varredura do atraso de detecção (pior caso cresce 1 período por passo):")
    f = vr["fronteira"]
    amostra = [l for l in vr["linhas"] if l["atraso_max"] in (a0, f - 1, f, f + 1)]
    print(f"  {'atraso_max':>11} {'pior (per)':>11} {'pior (ms)':>10} {'caminhos':>9}  status")
    for l in amostra:
        print(f"  {l['atraso_max']:>11} {l['periodos']:>11} {l['ms']:>9} {l['caminhos']:>9}  "
              f"{'ok' if l['ok'] else 'VIOLA'}")
    print(f"\nFRONTEIRA EXATA: até atraso_max = {f} ({vr['fronteira_ms']} ms) o prazo é cumprido;")
    print(f"a partir de {f + 1} ({vr['viola_ms']} ms) é violado. Isso transforma '{prazo} ms' de")
    print("número no papel em restrição de projeto verificada sobre o filtro do sensor.\n")

    os.makedirs("figs", exist_ok=True)
    with open("figs/varredura_u03.txt", "w", encoding="utf-8") as fp:
        fp.write(f"Varredura do atraso de detecção · {cen['nome']} (cenário {cen['codigo']})\n")
        fp.write(f"Ts={Ts} ms prazo={prazo} ms ciclos_perdidos={cp}\n\n")
        for l in vr["linhas"]:
            fp.write(f"atraso_max={l['atraso_max']:>3} pior={l['periodos']:>3}per={l['ms']:>4}ms "
                     f"caminhos={l['caminhos']:>3} {'ok' if l['ok'] else 'VIOLA'}\n")
    print("[ok] tabela completa salva em figs/varredura_u03.txt")

    print("\nSegurança: 'nunca ultrapassou o prazo em teste' fala do caso típico. O pior caso")
    print("exige o atraso máximo E o ciclo perdido ao mesmo tempo — combinação rara por")
    print("construção. Um atacante que force jitter (DoS no RTOS) empurra o sistema justo")
    print("para esse pior caso que a bancada quase nunca amostra.")


if __name__ == "__main__":
    main()
