"""p19 - Model checking por busca em largura: o espaço de estados do supervisor.

Enumera exaustivamente as transições e verifica invariantes. Diferente de um teste
aleatório, a BFS garante por construção que nenhuma transição alcançável fica de fora.

Uso:  uv run python pratica/p19_explora_estados.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def main():
    ex = L.explorar()
    print("=" * 66)
    print(" p19 · Exploração exaustiva do supervisor (sistema de transições)")
    print("=" * 66)
    print(f"estados alcançáveis : {ex['n_estados']}   {[L.ESTADOS[s] for s in ex['estados']]}")
    print(f"transições exploradas: {ex['n_transicoes']}  = {ex['n_estados']} estados x 128 entradas")
    print(f"arestas distintas   : {ex['n_arestas']} de {len(L.ESTADOS)**2} pares possíveis (6x6)\n")

    # REQ-SAFE-001 e REQ-SAFE-002 como invariantes
    v1 = L.explorar(inv=L.invariante_req001)["n_violacoes"]
    v2 = L.explorar(inv=L.invariante_req002)["n_violacoes"]
    print(f"REQ-SAFE-001 (torque x obstáculo): {v1} violações  ->  {'SATISFEITO' if v1 == 0 else 'VIOLADO'}")
    print(f"REQ-SAFE-002 (torque em EMERGENCIA): {v2} violações  ->  {'SATISFEITO' if v2 == 0 else 'VIOLADO'}\n")

    # matriz de arestas
    arestas = set(tuple(map(int, a.split('-'))) if isinstance(a, str) else a for a in ex["arestas"])
    print("Matriz de arestas (• = existe transição direta):")
    print("            " + " ".join(f"{L.ESTADOS[j][:4]:>5}" for j in range(6)))
    for i in range(6):
        linha = " ".join(f"{'  •  ' if (i, j) in arestas else '  ·  '}" for j in range(6))
        print(f"{L.ESTADOS[i]:>11} {linha}")
    falta = [(i, j) for i in range(6) for j in range(6) if (i, j) not in arestas]
    print(f"\nPares SEM transição direta: {len(falta)} (ex.: OCIOSO->DESACELERANDO nunca acontece —")
    print("o robô sempre passa por MOVENDO antes de desacelerar).\n")

    print("Segurança: a BFS é exaustiva. Um atacante que confie em 'nunca vi falhar em")
    print("teste' aposta que a combinação ruim não foi amostrada. O verificador aplica TODAS")
    print("as 128 entradas a cada estado — a combinação que falha não tem como escapar.")


if __name__ == "__main__":
    main()
