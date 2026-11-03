"""p23 - Teste baseado em modelo: cobertura e a ilusão dos 100%.

Uma suíte por percurso do grafo (a árvore geradora da BFS) cobre 100% dos estados com
pouquíssimos testes — mas deixa a maioria das arestas de fora. Cobertura de estados,
de transições e de condições de guarda respondem perguntas diferentes.

Uso:  uv run python pratica/p23_cobertura.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def main():
    cob = L.cobertura()
    print("=" * 66)
    print(" p23 · Cobertura: 100% de estados não é 100% de transições")
    print("=" * 66)
    print(f"Grafo do supervisor: {cob['n_estados']} estados, {cob['n_arestas']} arestas distintas.\n")

    print("Três critérios, em ordem crescente de exigência:")
    print("  1. cobertura de ESTADOS           (visitar cada estado)")
    print("  2. cobertura de TRANSIÇÕES         (percorrer cada aresta origem->destino)")
    print("  3. cobertura de CONDIÇÕES DE GUARDA (exercitar cada combinação que habilita a aresta)\n")

    print(f"Suíte mínima por percurso do grafo: {cob['testes_suite']} testes")
    print("  (a árvore geradora da BFS: uma transição que revela cada estado pela 1ª vez)")
    for s, e, ns in cob["suite"]:
        print(f"    {L.ESTADOS[s]:>16} --{{{', '.join(L.ativos(e)) or 'ø'}}}--> {L.ESTADOS[ns]}")
    print()
    print(f"  cobertura de estados   : {cob['cob_estados_pct']:.0f}%  ({cob['testes_suite']} testes)")
    print(f"  cobertura de transições: {cob['cob_arestas_pct']}%  "
          f"({cob['arestas_cobertas']} de {cob['n_arestas']} arestas)")
    print(f"  cobrir as {cob['n_arestas']} arestas exigiria no mínimo {cob['n_arestas']} casos.\n")

    print("Por que 100% de cobertura de LINHA não é evidência de correção: o bug de prioridade")
    print("(p20) convive com 100% de cobertura de linha, porque cada ramo do if roda em algum")
    print("teste isolado — nenhum precisa encadear os DOIS passos exatos que expõem a falha.")
    print("Cobertura de linha mede CÓDIGO EXECUTADO, não COMBINAÇÃO de estados e entradas.\n")

    print("Segurança: relatório de auditoria que só mostra '100% de cobertura' pode esconder")
    print("exatamente a sequência de ataque. Exija o CRITÉRIO (estados? transições? guarda?)")
    print("junto do número — e prefira testes gerados do modelo, não da intuição de quem escreve.")


if __name__ == "__main__":
    main()
