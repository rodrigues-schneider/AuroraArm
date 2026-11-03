"""u03lab.py - Laboratório de verificação formal e testes baseados em modelos (NovaTech Ltda. · MBD for CPS · Unidade 03).

Núcleo didático, sem dependências externas (só a biblioteca-padrão). Cobre:
  - o supervisor de segurança do NexaBot como sistema de transições (6 estados);
  - model checking por busca em largura: invariantes, contraexemplo e o bug de prioridade;
  - o autômato temporizado do watchdog (relógio discreto) e a varredura do atraso de detecção;
  - teste baseado em modelo: cobertura de estados, transições e condições de guarda, e a suíte mínima;
  - um gerador por RA (idêntico ao da U01/U02) que dá a cada aluno a sua própria fronteira de tempo.

CLI:
  python u03lab.py cenario   RA2026999 [--salvar supervisor.json]
  python u03lab.py modelcheck RA2026999 [--bug prioridade]
  python u03lab.py timed      RA2026999
  python u03lab.py cobertura  RA2026999
  python u03lab.py relatorio  RA2026999
"""
from __future__ import annotations
import json
import sys
from collections import deque

VERSAO = "3.0"

# --------------------------------------------------------------------------- #
#  Supervisor do NexaBot como sistema de transições (S, Sigma, ->)
# --------------------------------------------------------------------------- #
OCIOSO, MOVENDO, DESACELERANDO, PARADO_OBSTACULO, EMERGENCIA, FALHA = range(6)
ESTADOS = ["OCIOSO", "MOVENDO", "DESACELERANDO", "PARADO_OBSTACULO", "EMERGENCIA", "FALHA"]
CRITICOS = {EMERGENCIA, FALHA}
# 7 campos de entrada -> 2**7 = 128 combinações por estado (6 booleanos + 1 amostra de velocidade)
CAMPOS = ["partir", "parar", "obstaculo", "obst_removido", "emergencia", "falha", "vel0"]


def entradas():
    """Gera todas as 128 combinações de entrada (Sigma)."""
    for n in range(1 << len(CAMPOS)):
        yield {CAMPOS[i]: bool((n >> i) & 1) for i in range(len(CAMPOS))}


def torque_habilitado(estado):
    """Saída do supervisor: o torque só fica habilitado no estado MOVENDO."""
    return estado == MOVENDO


def transicao(s, e, bug=None):
    """Função de transição pura: (estado, entradas) -> próximo estado.

    bug=None  -> supervisor correto (segurança precede conveniência);
    bug='prioridade' -> inversão de prioridade dentro de MOVENDO (o bug da Aula 10).
    """
    # FALHA e EMERGENCIA têm prioridade de segurança a partir de qualquer estado operacional
    if s not in CRITICOS:
        if e["falha"]:
            return FALHA
        if e["emergencia"]:
            return EMERGENCIA
    if s == OCIOSO:
        return MOVENDO if (e["partir"] and not e["obstaculo"]) else OCIOSO
    if s == MOVENDO:
        if bug == "prioridade":
            # BUG: o comando do operador é avaliado ANTES do obstáculo
            if e["partir"]:
                return MOVENDO
        if e["obstaculo"] and e["vel0"]:
            return PARADO_OBSTACULO         # obstáculo com eixo já parado: pula a desaceleração
        if e["obstaculo"]:
            return DESACELERANDO            # CORRETO: obstáculo primeiro
        if e["partir"] and bug == "prioridade":
            return MOVENDO
        if e["parar"]:
            return OCIOSO
        return MOVENDO
    if s == DESACELERANDO:
        if e["vel0"]:
            return PARADO_OBSTACULO
        if e["obst_removido"] and not e["obstaculo"]:
            return OCIOSO if e["parar"] else MOVENDO
        return DESACELERANDO
    if s == PARADO_OBSTACULO:
        if e["obst_removido"] and not e["obstaculo"]:
            return MOVENDO if e["partir"] else OCIOSO
        return PARADO_OBSTACULO
    if s == EMERGENCIA:
        return EMERGENCIA                   # estado absorvente
    if s == FALHA:
        if bug == "sem_rearme":
            return FALHA                     # BUG de vivacidade: a falha nunca é rearmada
        if e["emergencia"]:
            return EMERGENCIA
        if (not e["falha"]) and e["parar"]:  # rearme explícito do operador
            return OCIOSO
        return FALHA
    return s


# --------------------------------------------------------------------------- #
#  Requisitos de segurança formalizados (REQ-SAFE)
# --------------------------------------------------------------------------- #
# tipo: 'invariante', 'alcancabilidade', 'seguranca', 'vivacidade', 'temporizado'
REQUISITOS = [
    ("REQ-SAFE-001", "invariante",
     "Nunca habilitar torque com obstáculo presente (restrição instantânea).", "explora_estados"),
    ("REQ-SAFE-002", "invariante",
     "Em EMERGENCIA o torque nunca está habilitado.", "explora_estados"),
    ("REQ-SAFE-003", "alcancabilidade",
     "É possível alcançar o estado MOVENDO a partir do repouso.", "explora_estados"),
    ("REQ-SAFE-004", "seguranca",
     "Toda vez que o botão de emergência ocorre, o estado seguinte é EMERGENCIA.", "explora_estados"),
    ("REQ-SAFE-005", "vivacidade",
     "A partir de FALHA sempre existe um caminho de volta a OCIOSO (rearme).", "explora_estados"),
    ("REQ-SAFE-006", "temporizado",
     "O torque físico chega a zero em até o prazo, contado do gatilho físico.", "automato_temporizado"),
    ("REQ-SAFE-007", "invariante_continuo",
     "Velocidade linear do efetuador dentro do limite (grandeza contínua).", "fora_do_escopo"),
]


def invariante_req001(s, e, ns):
    """REQ-SAFE-001 como invariante sobre a transição: a transição não pode terminar
    com torque habilitado tendo obstáculo presente na entrada."""
    return not (torque_habilitado(ns) and e["obstaculo"])


def invariante_req002(s, e, ns):
    """REQ-SAFE-002: nunca torque habilitado em EMERGENCIA (nem indo para lá)."""
    return not (torque_habilitado(ns) and (ns == EMERGENCIA or s == EMERGENCIA))


# --------------------------------------------------------------------------- #
#  Model checking: busca em largura no espaço de estados
# --------------------------------------------------------------------------- #
def explorar(bug=None, inv=invariante_req001):
    """Enumera exaustivamente o espaço de transições a partir de OCIOSO (BFS).

    Devolve dict com estados alcançáveis, arestas distintas, nº de transições,
    e a lista de violações do invariante `inv`.
    """
    visitados = {OCIOSO}
    fila = deque([OCIOSO])
    arestas = set()
    n_trans = 0
    violacoes = []
    while fila:
        s = fila.popleft()
        for e in entradas():
            ns = transicao(s, e, bug)
            n_trans += 1
            arestas.add((s, ns))
            if not inv(s, e, ns):
                violacoes.append((s, dict(e), ns))
            if ns not in visitados:
                visitados.add(ns)
                fila.append(ns)
    return {
        "estados": sorted(visitados),
        "n_estados": len(visitados),
        "arestas": sorted(arestas),
        "n_arestas": len(arestas),
        "n_transicoes": n_trans,
        "violacoes": violacoes,
        "n_violacoes": len(violacoes),
    }


def contraexemplo(bug="prioridade", inv=invariante_req001):
    """Caminho mínimo (BFS) do estado inicial até a primeira transição que viola `inv`."""
    fila = deque([(OCIOSO, [])])
    visto = {OCIOSO}
    while fila:
        s, caminho = fila.popleft()
        for e in entradas():
            ns = transicao(s, e, bug)
            passo = (s, dict(e), ns)
            if not inv(s, e, ns):
                return caminho + [passo]
            if ns not in visto:
                visto.add(ns)
                fila.append((ns, caminho + [passo]))
    return None


def ativos(e):
    """Lista legível dos campos de entrada verdadeiros."""
    return [k for k in CAMPOS if e.get(k)]


def fmt_contraexemplo(ce):
    linhas = []
    for s, e, ns in ce:
        linhas.append(f"{ESTADOS[s]} --{{{', '.join(ativos(e)) or 'ø'}}}--> {ESTADOS[ns]}")
    return linhas


def grafo_estados(bug=None):
    """Relação de alcançabilidade estado->estado (ignora as entradas), para consultas CTL."""
    suc = {s: set() for s in range(len(ESTADOS))}
    vis = {OCIOSO}
    fila = deque([OCIOSO])
    while fila:
        s = fila.popleft()
        for e in entradas():
            ns = transicao(s, e, bug)
            suc[s].add(ns)
            if ns not in vis:
                vis.add(ns)
                fila.append(ns)
    return suc, vis


def alcanca(alvo, bug=None):
    """EF(estado=alvo): conjunto de estados a partir dos quais `alvo` é alcançável."""
    suc, vis = grafo_estados(bug)
    bons = {alvo} if alvo in vis else set()
    mudou = True
    while mudou:
        mudou = False
        for s in vis:
            if s not in bons and any(ns in bons for ns in suc[s]):
                bons.add(s)
                mudou = True
    return bons


def vivacidade_rearme(bug=None):
    """REQ-SAFE-005 (vivacidade): a partir de FALHA sempre existe caminho de volta a OCIOSO
    (o rearme nunca é impossível). EMERGENCIA é estado seguro ABSORVENTE por projeto
    (exige reset físico, fora do modelo) e por isso é excluído da checagem.
    Devolve (ok, estados_presos) entre os estados operacionais."""
    _, vis = grafo_estados(bug)
    bons = alcanca(OCIOSO, bug)
    operacionais = [s for s in vis if s != EMERGENCIA]
    presos = sorted(s for s in operacionais if s not in bons)
    return (len(presos) == 0), presos


# --------------------------------------------------------------------------- #
#  Autômato temporizado do watchdog (relógio discreto) + varredura de pior caso
# --------------------------------------------------------------------------- #
def pior_caso(atraso_max, ciclos_perdidos=1):
    """Explora todas as escolhas não determinísticas do ambiente e devolve
    (pior_caso_em_periodos, numero_de_caminhos).

    DETECTANDO: a cada período, confirma a detecção ou continua atrasando (k <= atraso_max).
    COMANDANDO: atuação bem-sucedida, ou até `ciclos_perdidos` ciclos perdidos por jitter.
    """
    caminhos = []

    def detectar(d, periodos):
        if d < atraso_max:
            detectar(d + 1, periodos + 1)       # continua atrasando
        comandar(0, periodos + 1)                # confirma detecção (1 período)

    def comandar(perdidos, periodos):
        caminhos.append(periodos + 1)            # atuação bem-sucedida -> ZERADO
        if perdidos < ciclos_perdidos:
            comandar(perdidos + 1, periodos + 1)  # ciclo perdido

    detectar(0, 0)
    return max(caminhos), len(caminhos)


def varredura(Ts_ms, prazo_ms, ciclos_perdidos=1, a_max=120):
    """Varre atraso_max de 0 em diante e acha a fronteira exata do prazo."""
    linhas = []
    fronteira = None
    fronteira_ms = viola_ms = None
    for a in range(0, a_max + 1):
        periodos, ncam = pior_caso(a, ciclos_perdidos)
        ms = periodos * Ts_ms
        ok = ms <= prazo_ms
        linhas.append({"atraso_max": a, "periodos": periodos, "ms": ms, "caminhos": ncam, "ok": ok})
        if ok:
            fronteira, fronteira_ms = a, ms
        elif fronteira is not None:
            viola_ms = ms
            break
    return {"linhas": linhas, "fronteira": fronteira,
            "fronteira_ms": fronteira_ms, "viola_ms": viola_ms}


# --------------------------------------------------------------------------- #
#  Teste baseado em modelo (MBT): cobertura e suíte mínima
# --------------------------------------------------------------------------- #
def suite_minima(bug=None):
    """Árvore geradora da BFS: para cada estado, a transição que o revela pela primeira vez.
    Cobre 100% dos estados com o menor número de testes."""
    visitados = {OCIOSO}
    fila = deque([OCIOSO])
    testes = []
    while fila:
        s = fila.popleft()
        for e in entradas():
            ns = transicao(s, e, bug)
            if ns not in visitados:
                visitados.add(ns)
                testes.append((s, dict(e), ns))
                fila.append(ns)
    return testes


def cobertura(bug=None):
    """Cobertura de estados, transições (arestas) e condições de guarda da suíte mínima."""
    ex = explorar(bug)
    sm = suite_minima(bug)
    arestas_total = set(ex["arestas"])
    arestas_suite = {(s, ns) for s, e, ns in sm}
    return {
        "n_estados": ex["n_estados"],
        "n_arestas": ex["n_arestas"],
        "n_transicoes": ex["n_transicoes"],
        "testes_suite": len(sm),
        "cob_estados_pct": 100.0,
        "cob_arestas_pct": round(100.0 * len(arestas_suite) / ex["n_arestas"], 1),
        "arestas_cobertas": len(arestas_suite),
        "arestas_total_teorico": len(ESTADOS) ** 2,
        "suite": sm,
    }


# --------------------------------------------------------------------------- #
#  Gerador por RA (idêntico em Python e JavaScript: FNV-1a + mulberry32)
# --------------------------------------------------------------------------- #
def normaliza(codigo):
    import re
    return re.sub(r"[^A-Z0-9-]", "", str(codigo or "").upper())


def _fnv1a(t):
    h = 0x811C9DC5
    for ch in t:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


def _mulberry32(a):
    state = a & 0xFFFFFFFF

    def rnd():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t ^= (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF
        t &= 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rnd


LINHAS = [
    ("celula", "Célula colaborativa de montagem", "braço + esteira"),
    ("agv", "Corredor de AGVs do armazém", "frota de AGVs"),
    ("paletizadora", "Paletizadora robotizada", "braço paletizador"),
    ("solda", "Estação de solda robotizada", "robô de solda"),
    ("triagem", "Esteira de triagem com desviadores", "desviadores + esteira"),
]
TS_OPCOES = [2, 4, 5]


def gerar_cenario(codigo):
    """Gera o cenário de verificação da U03 a partir do RA. O supervisor lógico é
    o mesmo para todos (6 estados), mas cada aluno recebe a sua fronteira de tempo."""
    cod = normaliza(codigo) or "NT"
    r = _mulberry32(_fnv1a(cod))

    def ri(n):
        return int(r() * n)

    linha = LINHAS[ri(len(LINHAS))]
    Ts = TS_OPCOES[ri(len(TS_OPCOES))]
    # prazo escolhido para que a fronteira caia num intervalo didático (18..40 períodos)
    alvo_front = 18 + ri(23)                       # fronteira desejada em períodos de atraso
    prazo = (alvo_front + 3) * Ts                   # prazo que produz exatamente essa fronteira
    atraso_projeto = 2 + ri(6)                      # atraso de detecção do filtro do sensor (projeto atual)
    ciclos_perdidos = 1 + (1 if r() < 0.25 else 0)  # 1 (ou 2) ciclos de atuação podem se perder
    n_zonas = 1 + ri(4)                             # zonas de exclusão / AGVs (explosão de estados)
    tag = 10 + ri(90)
    return {
        "codigo": cod,
        "linha": linha[0],
        "nome": f"{linha[1]} {linha[0][:3].upper()}-{tag}",
        "composicao": linha[2],
        "Ts_ms": Ts,
        "prazo_ms": prazo,
        "atraso_projeto": atraso_projeto,
        "ciclos_perdidos": ciclos_perdidos,
        "n_zonas": n_zonas,
        "origem": f"gerador u03lab {VERSAO}",
    }


def resumo(cen):
    """Números derivados do cenário (o 'gabarito' da máquina do aluno)."""
    Ts, prazo = cen["Ts_ms"], cen["prazo_ms"]
    cp = cen["ciclos_perdidos"]
    vr = varredura(Ts, prazo, cp)
    pc, ncam = pior_caso(cen["atraso_projeto"], cp)
    ex = explorar()
    cob = cobertura()
    z = cen["n_zonas"]
    # explosão de estados: cada zona de exclusão acrescenta um autômato independente de 3 estados
    estados_compostos = 6 * (3 ** z)
    return {
        "n_estados": ex["n_estados"],
        "n_arestas": ex["n_arestas"],
        "n_transicoes": ex["n_transicoes"],
        "n_violacoes_bug": explorar(bug="prioridade")["n_violacoes"],
        "ce_passos": len(contraexemplo()),
        "fronteira": vr["fronteira"],
        "fronteira_ms": vr["fronteira_ms"],
        "viola_ms": vr["viola_ms"],
        "pior_ms_projeto": pc * Ts,
        "pior_periodos_projeto": pc,
        "caminhos_projeto": ncam,
        "folga_ms": prazo - pc * Ts,
        "cob_arestas_pct": cob["cob_arestas_pct"],
        "testes_suite": cob["testes_suite"],
        "estados_compostos": estados_compostos,
        "prazo_periodos": prazo // Ts,
    }


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def _flag(args, nome, default=None):
    if nome in args:
        i = args.index(nome)
        return args[i + 1] if i + 1 < len(args) else True
    return default


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    ra = args[0] if args and not args[0].startswith("--") else "RA2026999"
    cen = gerar_cenario(ra)
    if cmd == "cenario":
        print(json.dumps(cen, ensure_ascii=False, indent=2))
        destino = _flag(args, "--salvar")
        if destino:
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(cen, f, ensure_ascii=False, indent=2)
            print(f"\n[ok] cenário salvo em {destino}")
    elif cmd == "modelcheck":
        bug = "prioridade" if _flag(args, "--bug") else None
        ex = explorar(bug=bug)
        print(f"Supervisor do {cen['nome']} (RA {cen['codigo']})")
        print(f"  estados alcançáveis : {ex['n_estados']}")
        print(f"  transições exploradas: {ex['n_transicoes']}  ({ex['n_estados']} x 128)")
        print(f"  arestas distintas   : {ex['n_arestas']} de {len(ESTADOS)**2} possíveis")
        print(f"  violações REQ-SAFE-001: {ex['n_violacoes']}" + ("   <-- BUG DE PRIORIDADE" if bug else ""))
        if ex["n_violacoes"]:
            print("  contraexemplo mínimo:")
            for l in fmt_contraexemplo(contraexemplo(bug="prioridade")):
                print("    " + l)
    elif cmd == "timed":
        vr = varredura(cen["Ts_ms"], cen["prazo_ms"], cen["ciclos_perdidos"])
        pc, ncam = pior_caso(cen["atraso_projeto"], cen["ciclos_perdidos"])
        print(f"Watchdog do {cen['nome']} · Ts={cen['Ts_ms']} ms · prazo={cen['prazo_ms']} ms "
              f"· {cen['ciclos_perdidos']} ciclo(s) perdido(s)")
        print(f"  projeto atual (atraso_max={cen['atraso_projeto']}): pior caso = {pc} períodos "
              f"= {pc*cen['Ts_ms']} ms  ({ncam} caminhos) -> folga {cen['prazo_ms']-pc*cen['Ts_ms']} ms")
        print(f"  FRONTEIRA: atraso_max={vr['fronteira']} -> {vr['fronteira_ms']} ms (conforme); "
              f"atraso_max={vr['fronteira']+1} -> {vr['viola_ms']} ms (viola)")
    elif cmd == "cobertura":
        cob = cobertura()
        print(f"Cobertura do supervisor (suíte por percurso do grafo)")
        print(f"  estados   : {cob['n_estados']}  -> cobertura {cob['cob_estados_pct']:.0f}%")
        print(f"  arestas   : {cob['n_arestas']}  -> suíte cobre {cob['arestas_cobertas']} "
              f"({cob['cob_arestas_pct']}%)")
        print(f"  testes na suíte mínima: {cob['testes_suite']}")
    elif cmd == "relatorio":
        rs = resumo(cen)
        print(json.dumps({"cenario": cen, "resumo": rs}, ensure_ascii=False, indent=2))
    else:
        print(f"comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
