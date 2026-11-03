"""p24 - Teste baseado em propriedades com Hypothesis e redução (shrinking).

Teste baseado em propriedades declara uma condição que deve valer para QUALQUER entrada
de um domínio; a ferramenta gera sequências tentando ativamente violá-la e, ao achar uma
falha, REDUZ (shrinking) até a menor sequência que ainda a reproduz. No supervisor correto
nenhuma sequência viola; no supervisor com bug, a redução converge para o mesmo
contraexemplo mínimo de 2 passos que a exploração exaustiva (p20) encontrou.

Requer:  uv add hypothesis
Uso:     uv run python pratica/p24_hypothesis.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L

try:
    from hypothesis import given, settings, strategies as st
except ImportError:
    raise SystemExit("Instale a biblioteca:  uv add hypothesis")

ENTRADA = st.integers(min_value=0, max_value=127)
SEQ = st.lists(ENTRADA, min_size=1, max_size=10)


def roda_sequencia(seq, bug):
    """Aplica a sequência de entradas passo a passo e devolve a 1ª transição que viola
    REQ-SAFE-001, ou None se nenhuma violar."""
    s = L.OCIOSO
    for n in seq:
        e = {L.CAMPOS[i]: bool((n >> i) & 1) for i in range(7)}
        ns = L.transicao(s, e, bug)
        if not L.invariante_req001(s, e, ns):
            return (s, e, ns)
        s = ns
    return None


def propriedade(seq, bug, falhas):
    viol = roda_sequencia(seq, bug)
    if viol is not None:
        falhas.append(list(seq))
    assert viol is None, "REQ-SAFE-001 violado pela sequência"


def menor(falhas):
    return min(falhas, key=lambda s: (len(s), s)) if falhas else None


def main():
    print("=" * 66)
    print(" p24 · Teste baseado em propriedades (Hypothesis) + redução")
    print("=" * 66)
    cfg = settings(max_examples=2000, deadline=None, derandomize=True)

    # 1) supervisor CORRETO: a propriedade vale para toda sequência
    falhas_ok = []

    @cfg
    @given(SEQ)
    def teste_correto(seq):
        propriedade(seq, None, falhas_ok)

    try:
        teste_correto()
        print("Supervisor CORRETO: 2000 sequências geradas, NENHUMA viola REQ-SAFE-001. ✔")
    except AssertionError:
        print("Supervisor CORRETO: inesperado — uma sequência violou (revise o modelo).")

    # 2) supervisor com BUG: Hypothesis acha e reduz
    falhas_bug = []

    @cfg
    @given(SEQ)
    def teste_bug(seq):
        propriedade(seq, "prioridade", falhas_bug)

    achou = False
    try:
        teste_bug()
    except AssertionError:
        achou = True

    print()
    if achou and falhas_bug:
        m = menor(falhas_bug)
        print(f"Supervisor com BUG: Hypothesis encontrou {len(falhas_bug)} sequências falhas.")
        print(f"  menor sequência reproduzida: {m}  ({len(m)} passos)")
        print("  traduzida:")
        s = L.OCIOSO
        for n in m:
            e = {L.CAMPOS[i]: bool((n >> i) & 1) for i in range(7)}
            ns = L.transicao(s, e, "prioridade")
            print(f"    {L.ESTADOS[s]:>16} --{{{', '.join(L.ativos(e)) or 'ø'}}}--> {L.ESTADOS[ns]}")
            s = ns
    else:
        print("Supervisor com BUG: Hypothesis não achou (aumente max_examples).")

    ce = L.contraexemplo(bug="prioridade")
    print(f"\nExploração exaustiva (p20) achou o contraexemplo mínimo em {len(ce)} passos.")
    print("Duas técnicas diferentes — property-based (dirigido por heurística) e exploração")
    print("exaustiva — convergem para a MESMA sequência mínima, porque ela é, estruturalmente,")
    print("o menor caminho que viola o requisito.\n")
    print("Segurança: o shrinking entrega o relatório de incidente pronto — a menor receita")
    print("que reproduz a falha. É o que você quer em mãos antes que um atacante a descubra.")


if __name__ == "__main__":
    main()
