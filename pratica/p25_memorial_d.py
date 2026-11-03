"""p25 - Memorial de cálculo, item (d): verificação do prazo de segurança.

Rascunho do item (d) do memorial do trabalho (AuroraArm). Complete os TODO com as
fórmulas; o script confere contra o motor u03lab e salva figs/memorial_d_u03.md.

Memorial item (d): "verificar exaustivamente se o prazo é cumprido em TODAS as combinações
de atraso de detecção e perda de ciclo consideradas, ou identificar a combinação que o viola."

Uso:  uv run python pratica/p25_memorial_d.py planta_u03.json
"""
import json
import os
import sys
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L


def carregar(argv):
    if argv and os.path.exists(argv[0]):
        with open(argv[0], encoding="utf-8") as f:
            return json.load(f)
    return L.gerar_cenario(argv[0] if argv else "RA2026999")


def confere(nome, aluno, correto, un="", tol=1e-9):
    ok = aluno is not None and abs(aluno - correto) <= tol
    marca = "✔" if ok else "✘"
    extra = "" if ok else f"   (esperado: {correto} {un})"
    print(f"  [{marca}] {nome}: {aluno} {un}{extra}")
    return ok


def main():
    cen = carregar(sys.argv[1:])
    Ts, prazo, cp, a0 = cen["Ts_ms"], cen["prazo_ms"], cen["ciclos_perdidos"], cen["atraso_projeto"]
    print("=" * 66)
    print(f" p25 · Memorial item (d) · {cen['nome']} (cenário {cen['codigo']})")
    print("=" * 66)
    print(f"Dados: Ts = {Ts} ms | prazo = {prazo} ms | atraso_deteccao_max = {a0} períodos | "
          f"ciclos_perdidos = {cp}\n")

    # ------------------------------------------------------------------ #
    # TODO (d.1): pior caso em períodos, no projeto atual.
    #   dica: períodos de atraso (a0) + 1 confirmação + (1 + ciclos_perdidos) de atuação.
    pior_periodos = a0 + 2 + cp     # atraso de detecção + confirmação + atuação/jitter
    # TODO (d.2): pior caso em ms.
    pior_ms = pior_periodos * Ts
    # TODO (d.3): fronteira (maior atraso_max que ainda cumpre o prazo).
    #   dica: o maior 'a' tal que (a + 2 + cp) * Ts <= prazo.
    fronteira = prazo // Ts - 2 - cp
    # ------------------------------------------------------------------ #

    pc_ref, ncam = L.pior_caso(a0, cp)
    vr = L.varredura(Ts, prazo, cp)
    print("Conferência contra a exploração exaustiva do autômato temporizado:")
    ok1 = confere("pior caso (períodos)", pior_periodos, pc_ref, "períodos")
    ok2 = confere("pior caso (ms)", pior_ms, pc_ref * Ts, "ms")
    ok3 = confere("fronteira (atraso_max)", fronteira, vr["fronteira"], "períodos")
    conforme = pc_ref * Ts <= prazo
    print(f"\n  {ncam} trajetórias exploradas; pior caso {'CUMPRE' if conforme else 'VIOLA'} o prazo "
          f"(folga {prazo - pc_ref * Ts} ms).")

    if not (ok1 and ok2 and ok3):
        print("\nComplete os TODO (d.1)–(d.3) e rode de novo. Nada foi salvo.")
        return

    os.makedirs("figs", exist_ok=True)
    md = f"""# Memorial item (d) — Verificação do prazo de segurança

**Máquina:** {cen['nome']} (cenário {cen['codigo']})
**Parâmetros:** Ts = {Ts} ms · prazo (REQ-SAFE-006 / análogo a REQ-SAFE-AA-001) = {prazo} ms ·
atraso_deteccao_max = {a0} períodos · ciclos_perdidos = {cp}

## Modelo
Watchdog como autômato temporizado de relógio discreto (períodos de Ts). Pior caso =
atraso máximo de detecção ({a0}) + 1 período de confirmação + {1 + cp} períodos de atuação
(incluindo {cp} ciclo(s) perdido(s) por jitter).

## Resultado (verificação exaustiva)
- Trajetórias não determinísticas exploradas: **{ncam}**
- Pior caso: **{pc_ref} períodos = {pc_ref * Ts} ms**
- Prazo: {prazo} ms  ->  **{'CUMPRIDO' if conforme else 'VIOLADO'}** (folga {prazo - pc_ref * Ts} ms)
- Fronteira exata: até atraso_max = **{vr['fronteira']}** ({vr['fronteira_ms']} ms) cumpre;
  a partir de {vr['fronteira'] + 1} ({vr['viola_ms']} ms) viola.

## Conclusão
O prazo de {prazo} ms deixa de ser número no papel e vira restrição de projeto sobre o
filtro do sensor: relaxar o atraso de detecção além de {vr['fronteira']} períodos exige
reverificar o requisito. "Nunca falhou em teste" não substitui esta prova de pior caso.
"""
    with open("figs/memorial_d_u03.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("\n[ok] Tudo conferido. Rascunho salvo em figs/memorial_d_u03.md")
    print("     Leve-o para o repositório do trabalho (memorial item d).")


if __name__ == "__main__":
    main()
