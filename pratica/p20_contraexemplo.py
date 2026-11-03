"""p20 - O contraexemplo: o bug que passou em toda revisão manual.

Uma inversão de prioridade dentro do estado MOVENDO (avaliar o comando do operador
antes do obstáculo) habilita torque com obstáculo presente. A BFS acha a falha e
entrega o caminho mínimo que a reproduz — a saída mais valiosa da verificação.

Uso:  uv run python pratica/p20_contraexemplo.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def main():
    print("=" * 66)
    print(" p20 · O contraexemplo de duas transições")
    print("=" * 66)

    correto = L.explorar(bug=None)
    bug = L.explorar(bug="prioridade")
    print("Mesmos estados e mesmas transições nas duas versões:")
    print(f"  correto: {correto['n_estados']} estados, {correto['n_transicoes']} transições, "
          f"{correto['n_violacoes']} violações de REQ-SAFE-001")
    print(f"  com bug: {bug['n_estados']} estados, {bug['n_transicoes']} transições, "
          f"{bug['n_violacoes']} violações de REQ-SAFE-001  <-- o bug muda SÓ o resultado\n")

    ce = L.contraexemplo(bug="prioridade")
    print(f"Contraexemplo mínimo ({len(ce)} transições):")
    for linha in L.fmt_contraexemplo(ce):
        print("   " + linha)
    s, e, ns = ce[-1]
    print(f"\n   Na transição final o supervisor fica em {L.ESTADOS[ns]} com torque habilitado")
    print("   E obstáculo presente ao mesmo tempo — exatamente o que REQ-SAFE-001 proíbe.\n")

    print("A correção cabe em uma ideia: avaliar o obstáculo ANTES do comando de partida.")
    print("Em um supervisor de segurança, a condição que protege pessoas precede a que")
    print("atende conveniência de operação. Ordem de avaliação, em máquina de estados, é")
    print("SEMÂNTICA — não é estilo.\n")

    print("Segurança: nenhum teste manual comum aplica 'comando de partida' E 'obstáculo'")
    print("ao mesmo tempo. Um atacante que conheça a inversão de prioridade sabe exatamente")
    print("qual par de entradas segurar para manter o torque ligado diante de uma pessoa.")


if __name__ == "__main__":
    main()
