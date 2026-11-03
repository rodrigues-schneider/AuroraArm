"""P33 · O que o pipeline prova e o que não prova + memorial item (e) (aula 16).

Varre o projeto e monta a matriz de rastreabilidade DERIVADA do código (ela não mente:
quando um artefato some, a coluna esvazia). Lista o que o pipeline produz e o que NÃO
produz (qualificação DO-330, MC/DC, MISRA, certificação) e aplica as 3 perguntas de
qualificação a cada ferramenta. Salva figs/memorial_e_u04.md para o memorial do trabalho.

Rode da pasta lab_cps:  uv run python pratica/p33_rastreabilidade.py controlador.json
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

mr = L.matriz_rastreabilidade(".")
print(f"Matriz de rastreabilidade — {mr['n_arquivos']} arquivos varridos, "
      f"{mr['n_com_req']} com marcador de requisito\n")
print(f"{'REQ':<16}{'modelo':>7}{'código':>8}{'teste':>7}  descrição")
for l in mr["tabela"]:
    flag = "  <-- SEM TESTE (justifique)" if l["vazio_teste"] else ""
    print(f"{l['req']:<16}{l['modelo']:>7}{l['codigo']:>8}{l['teste']:>7}  {l['desc'][:38]}{flag}")

print("\n== O que este pipeline PRODUZ ==")
for e in L.EVIDENCIAS_PRODUZ:
    print("  [x]", e)
print("\n== O que este pipeline NÃO produz ==")
for e in L.EVIDENCIAS_NAO:
    print("  [ ]", e)

print("\n== Qualificação de ferramenta (DO-330: 3 perguntas, nenhuma sobre preço/licença) ==")
for q in L.qualificar_ferramenta():
    print(f"  {q['ferramenta']:<26} introduz erro? {'sim' if q['introduz_erro'] else 'não'} · "
          f"deixa pular verificação? {'sim' if q['permite_pular'] else 'não'} · "
          f"-> {'EXIGE qualificação' if q['exige_qualificacao'] else 'dispensa'}")

os.makedirs("figs", exist_ok=True)
linhas = ["# Memorial — item (e): rastreabilidade e limites da evidência",
          f"\nControlador: {cen['nome']} (cenário {cen['codigo']})\n",
          "## Matriz de rastreabilidade\n",
          "| REQ | modelo | código | teste | descrição |", "|---|---|---|---|---|"]
for l in mr["tabela"]:
    linhas.append(f"| {l['req']} | {l['modelo']} | {l['codigo']} | {l['teste']} | {l['desc']} |")
linhas += ["\n## O que o pipeline prova", ""] + [f"- {e}" for e in L.EVIDENCIAS_PRODUZ]
linhas += ["\n## O que o pipeline NÃO prova (limites)", ""] + [f"- {e}" for e in L.EVIDENCIAS_NAO]
linhas += [
    "\n## Aplicação ao AuroraArm — limites observados",
    "",
    "- O cenário e o PI vieram de `controlador.json`; os parâmetros da planta e o limite de 48 V foram aplicados em memória pelo adaptador `pratica/u04_aurora.py`.",
    "- O `u04lab` oficial gera C com tipos `double` (64 bits). O SIL executado prova equivalência desse artefato em double; não prova ainda a implementação float32 exigida pelo microcontrolador AuroraArm.",
    "- O HIL usa a planta AuroraArm simulada no host. O jitter é um perfil determinístico de até 2 ms, não uma medição no microcontrolador real.",
    "- A matriz exibiu 0 artefatos na coluna código: o scanner ignora `figs/` e o gerador oficial não inclui marcadores REQ no C. A presença do C assinado está comprovada em `figs/AuroraArm_pid_gen.h` e `.c`, mas a ligação automática requisito→código continua pendente.",
]
linhas += ["\n> Evidência não é certificado: nós produzimos a evidência; quem certifica é uma",
           "> autoridade com mandato. Um pipeline aberto bem-feito produz evidência de primeira;",
           "> ferramenta cara não certifica nada por decreto."]
with open("figs/memorial_e_u04_AuroraArm.md", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas))
print("\n[ok] figs/memorial_e_u04_AuroraArm.md salvo — rascunho do item (e) do memorial.")
