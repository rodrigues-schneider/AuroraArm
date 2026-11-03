"""p21 - LTL, CTL, alcançabilidade e vivacidade.

LTL descreve propriedades sobre UMA trajetória (G, F, X, U). CTL descreve propriedades
sobre a ÁRVORE de trajetórias (AG, EF, AF, EG). Aqui usamos duas delas no supervisor:
alcançabilidade (EF) e vivacidade (de todo estado volta-se a OCIOSO), e vemos um bug
que trava a vivacidade sem violar nenhum invariante de estado.

Uso:  uv run python pratica/p21_ltl_ctl.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def main():
    print("=" * 66)
    print(" p21 · LTL / CTL: alcançabilidade e vivacidade")
    print("=" * 66)
    print("LTL (trajetória):  G globalmente | F eventualmente | X próximo | U até")
    print("CTL (árvore)    : AG p/todo-sempre | EF existe-eventual | AF p/todo-eventual | EG existe-sempre\n")
    print("No vocabulário do supervisor:")
    print("  REQ-SAFE-001  ->  AG ¬(torque_habilitado ∧ obstaculo)   (invariante)")
    print("  REQ-SAFE-003  ->  EF (estado = MOVENDO)                  (alcançabilidade)")
    print("  REQ-SAFE-005  ->  a partir de FALHA, EF(estado = OCIOSO)  (vivacidade: sempre dá para rearmar)\n")

    # EF(MOVENDO)
    de_onde = L.alcanca(L.MOVENDO)
    print(f"EF(MOVENDO): alcançável a partir de {len(de_onde)} estados "
          f"-> {sorted(L.ESTADOS[s] for s in de_onde)}")
    print("  (a partir de EMERGENCIA, absorvente, não se alcança MOVENDO — e está correto.)\n")

    print("EMERGENCIA é estado seguro ABSORVENTE por projeto (exige reset físico, fora do")
    print("modelo). A vivacidade olha os estados OPERACIONAIS: a partir de FALHA sempre")
    print("deve existir rearme de volta a OCIOSO.\n")

    # Vivacidade no supervisor correto
    ok, presos = L.vivacidade_rearme()
    print(f"REQ-SAFE-005 no supervisor correto: {'SATISFEITO' if ok else 'VIOLADO'} "
          f"(estados operacionais presos: {[L.ESTADOS[s] for s in presos] or 'nenhum'})")

    # Bug de vivacidade: FALHA sem rearme vira sumidouro
    ok_b, presos_b = L.vivacidade_rearme(bug="sem_rearme")
    print(f"Com o bug 'sem_rearme'          : {'SATISFEITO' if ok_b else 'VIOLADO'} "
          f"(estados operacionais presos: {[L.ESTADOS[s] for s in presos_b]})\n")

    # Repare: o bug de vivacidade NÃO viola nenhum invariante de estado
    inv_bug = L.explorar(bug="sem_rearme", inv=L.invariante_req001)["n_violacoes"]
    print(f"Atenção: com 'sem_rearme', REQ-SAFE-001 (invariante) ainda tem {inv_bug} violações.")
    print("Um sistema pode satisfazer todos os invariantes de segurança e mesmo assim")
    print("ficar PRESO para sempre — safety não captura liveness. Por isso precisamos das duas.\n")

    print("Segurança: um ataque de negação de serviço pode não violar nenhum invariante e")
    print("ainda assim 'prender' o sistema num estado degradado do qual ele nunca sai.")
    print("Vivacidade é a propriedade que flagra esse tipo de travamento.")


if __name__ == "__main__":
    main()
