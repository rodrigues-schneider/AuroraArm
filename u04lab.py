"""u04lab.py - Do modelo ao código: geração, SIL, HIL e evidências (NovaTech Ltda. · MBD for CPS · Unidade 04).

Núcleo didático, SEM dependências externas (só a biblioteca-padrão). Fecha o pipeline MBD:
  - geração de código C a partir do controlador (artefato derivado) + assinatura de rastreabilidade;
  - ponto flutuante x ponto fixo Q(m.n): degrau, faixa e os modos de falha (incremento -> 0, estouro);
  - Software-in-the-Loop (SIL): compila o C de verdade (gcc/clang) ou usa o equivalente em Python,
    roda modelo x código com a MESMA sequência e mede a divergência em épsilons de máquina;
  - Hardware-in-the-Loop (HIL): laço fechado com alvo loopback, jitter (médio x pior caso), latência,
    orçamento de prazo e watchdog com comando seguro;
  - matriz de rastreabilidade derivada do código, evidência x certificado e qualificação de ferramenta.
  - um gerador por RA (idêntico à U01/U02/U03: FNV-1a + mulberry32) dá a cada aluno a sua variante.

CLI:
  python u04lab.py cenario    RA2026999 [--salvar controlador.json]
  python u04lab.py gerar       RA2026999 [--fmt q16.16]
  python u04lab.py pontofixo   RA2026999
  python u04lab.py sil         RA2026999 [--bug antiwindup] [--fmt q16.16]
  python u04lab.py hil         RA2026999
  python u04lab.py rastrear    [--raiz .]
  python u04lab.py relatorio   RA2026999
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
import sys

VERSAO = "4.0"

# --------------------------------------------------------------------------- #
#  NexaBot das videoaulas (parâmetros "congelados" — iguais em toda a disciplina)
# --------------------------------------------------------------------------- #
NEXABOT = {
    "nome": "NexaBot (videoaulas)",
    "R": 1.2, "L": 3.5e-3, "Kt": 0.045, "Ke": 0.045, "J": 2.5e-4, "B": 8e-5,
    "V_max": 24.0, "I_max": 12.0, "Ts": 0.005, "w_op": 200.0, "T_op": 0.15,
}
# Ganhos do controlador de referência (mesmos da apresentação U02: PI com anti-windup)
GANHOS_REF = {"Kp": 0.3, "Ki": 10.0, "Kd": 0.0, "Kaw": 100.0, "N": 10.0}


# --------------------------------------------------------------------------- #
#  Planta CC de ímã permanente — Euler escalar (sem numpy)
# --------------------------------------------------------------------------- #
class Planta:
    """Motor CC: estados (corrente i, velocidade w). Integração de Euler em passo fino."""

    def __init__(self, p=None):
        p = p or NEXABOT
        for k in ("R", "L", "Kt", "Ke", "J", "B", "V_max", "I_max", "Ts", "w_op", "T_op"):
            setattr(self, k, float(p[k]))
        self.nome = p.get("nome", "planta")

    def passo(self, i, w, V, T, dt):
        di = (V - self.R * i - self.Ke * w) / self.L
        dw = (self.Kt * i - self.B * w - T) / self.J
        return i + di * dt, w + dw * dt

    def G0(self):
        return self.Kt / (self.R * self.B + self.Kt * self.Ke)


# --------------------------------------------------------------------------- #
#  Controlador PID discreto (idêntico ao das aulas 6/7: Tustin + anti-windup)
# --------------------------------------------------------------------------- #
class PIDDiscreto:
    """u = Kp*e + I + D, com integral por Tustin, derivada filtrada sobre a medida,
    saturação em ±u_max e anti-windup por back-calculation (Kaw, em 1/s)."""

    def __init__(self, Kp, Ki=0.0, Kd=0.0, Ts=0.005, u_max=24.0, Kaw=0.0, N=10.0):
        self.Kp, self.Ki, self.Kd, self.Ts = float(Kp), float(Ki), float(Kd), float(Ts)
        self.u_max, self.Kaw, self.N = float(u_max), float(Kaw), float(N)
        self.reset()

    def reset(self):
        self.I = 0.0
        self.D = 0.0
        self.e_ant = 0.0
        self.y_ant = None

    def step(self, ref, y):
        e = ref - y
        # integral (Tustin / trapézio)
        self.I += self.Ki * self.Ts * (e + self.e_ant) / 2.0
        # derivada filtrada sobre a medida
        if self.Kd > 0 and self.y_ant is not None:
            Tf = self.Kd / (self.Kp * self.N) if self.Kp > 0 else self.Ts
            a = Tf / (Tf + self.Ts)
            self.D = a * self.D - (1 - a) * self.Kd * (y - self.y_ant) / self.Ts
        v = self.Kp * e + self.I + self.D          # comando sem saturar
        u = min(max(v, -self.u_max), self.u_max)    # saturação
        self.I += self.Kaw * self.Ts * (u - v)      # anti-windup (back-calculation)
        self.e_ant, self.y_ant = e, y
        return u


def ctrl_de_cenario(cen, bug=None):
    """Monta o PID a partir do cenário do RA. bug='antiwindup' zera o Kaw (o bug da aula 14)."""
    g = cen["ganhos"]
    kaw = 0.0 if bug == "antiwindup" else g["Kaw"]
    return PIDDiscreto(g["Kp"], g["Ki"], g["Kd"], cen["Ts_ms"] / 1000.0,
                       NEXABOT["V_max"], kaw, g["N"])


# --------------------------------------------------------------------------- #
#  1. Ponto fixo Q(m.n)
# --------------------------------------------------------------------------- #
def q_info(m, n):
    escala = 1 << n
    degrau = 1.0 / escala
    faixa = (1 << (m + n - 1))                 # 32 bits com sinal: 2**31
    maxv = (faixa - 1) / escala
    minv = -faixa / escala
    return {"m": m, "n": n, "bits": m + n, "escala": escala,
            "degrau": degrau, "max": maxv, "min": minv}


def to_q(x, n):
    return int(math.floor(x * (1 << n) + 0.5))


def from_q(q, n):
    return q / (1 << n)


def cabe_32(x, n):
    q = x * (1 << n)
    return -(1 << 31) <= q < (1 << 31)


def erro_quantizacao(x, n):
    return abs(x - from_q(to_q(x, n), n))


def acumulador(erro_ciclo, ciclos, Ki, Ts, n):
    """Dois integradores (float x Q.n) somando o MESMO incremento a cada ciclo.
    Devolve os dois acumulados, o desvio e se o incremento 'sumiu' em ponto fixo."""
    inc = Ki * Ts * erro_ciclo
    inc_q = to_q(inc, n)                        # incremento já quantizado (inteiro)
    acc_f = 0.0
    acc_q = 0                                   # inteiro Q.n
    for _ in range(ciclos):
        acc_f += inc
        acc_q += inc_q
    acc_q_real = from_q(acc_q, n)
    desvio = abs(acc_f - acc_q_real)
    return {
        "inc": inc, "inc_q": inc_q, "inc_sumiu": inc_q == 0,
        "acc_float": acc_f, "acc_q": acc_q_real,
        "desvio": desvio, "desvio_rel": desvio / abs(acc_f) if acc_f else 0.0,
        "degraus": desvio * (1 << n),
    }


# --------------------------------------------------------------------------- #
#  2. Geração de código C (artefato derivado) + assinatura de rastreabilidade
# --------------------------------------------------------------------------- #
def assinatura(ctrl, fmt):
    """Hash determinístico sobre os parâmetros que entram no código (NÃO sobre o relógio)."""
    base = "|".join([
        f"gen=u04lab:{VERSAO}", f"fmt={fmt}",
        f"Kp={ctrl.Kp!r}", f"Ki={ctrl.Ki!r}", f"Kd={ctrl.Kd!r}",
        f"Kaw={ctrl.Kaw!r}", f"N={ctrl.N!r}", f"Ts={ctrl.Ts!r}", f"umax={ctrl.u_max!r}",
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def gerar_c(ctrl, fmt="float", quando="(geração determinística)", qn=16):
    """Gera (header, source) do passo do PID. fmt in {'float','q16.16'/'qN'}.
    O arquivo começa pelo bloco de auditoria que responde às perguntas da certificação."""
    assin = assinatura(ctrl, fmt)
    Ts_ms = ctrl.Ts * 1000.0
    cab = (
        "/* ===========================================================================\n"
        " * ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITAR À MÃO.\n"
        " * Este é um artefato derivado: se o comportamento estiver errado, corrija o\n"
        " * MODELO e gere de novo. Edições manuais serão apagadas na próxima geração.\n"
        " * ---------------------------------------------------------------------------\n"
        f" * gerador .......: u04lab {VERSAO}\n"
        f" * formato .......: {fmt}\n"
        f" * ganhos ........: Kp={ctrl.Kp} Ki={ctrl.Ki} Kd={ctrl.Kd} Kaw={ctrl.Kaw} N={ctrl.N}\n"
        f" * saturação .....: +/- {ctrl.u_max} V\n"
        f" * período (Ts) ..: {Ts_ms:.3f} ms  <-- CONTRATO: chame pid_step() exatamente nessa cadência\n"
        f" * gerado em .....: {quando}\n"
        f" * assinatura ....: {assin}\n"
        " * =========================================================================== */\n"
    )
    header = (
        cab +
        "#ifndef PID_GEN_H\n#define PID_GEN_H\n"
        "typedef struct { double I, D, e_ant, y_ant; int tem_y; } pid_estado_t;\n"
        "void pid_reset(pid_estado_t *st);\n"
        "double pid_step(pid_estado_t *st, double ref, double y);\n"
        "#endif\n"
    )
    if fmt == "float":
        src = (
            cab +
            '#include "pid_gen.h"\n\n'
            "void pid_reset(pid_estado_t *st){ st->I=0; st->D=0; st->e_ant=0; st->y_ant=0; st->tem_y=0; }\n\n"
            "double pid_step(pid_estado_t *st, double ref, double y){\n"
            f"    const double Kp={ctrl.Kp}, Ki={ctrl.Ki}, Kd={ctrl.Kd};\n"
            f"    const double Kaw={ctrl.Kaw}, N={ctrl.N}, Ts={ctrl.Ts}, umax={ctrl.u_max};\n"
            "    double e = ref - y;\n"
            "    st->I += Ki*Ts*(e + st->e_ant)/2.0;            /* integral (Tustin) */\n"
            "    if (Kd>0 && st->tem_y){\n"
            "        double Tf = (Kp>0)? Kd/(Kp*N) : Ts;\n"
            "        double a = Tf/(Tf+Ts);\n"
            "        st->D = a*st->D - (1-a)*Kd*(y - st->y_ant)/Ts;  /* derivada filtrada */\n"
            "    }\n"
            "    double v = Kp*e + st->I + st->D;                /* comando */\n"
            "    double u = v>umax? umax : (v<-umax? -umax : v);  /* saturação */\n"
            "    st->I += Kaw*Ts*(u - v);                        /* anti-windup */\n"
            "    st->e_ant = e; st->y_ant = y; st->tem_y = 1;\n"
            "    return u;\n"
            "}\n"
        )
    else:
        src = (
            cab +
            "/* Variante Q%d.%d: a integral vive em ponto fixo e arredonda a cada ciclo. */\n" % (32 - qn, qn) +
            '#include "pid_gen.h"\n'
            "#include <stdint.h>\n"
            f"#define QN {qn}\n#define ESCALA (1L<<QN)\n"
            "static long to_q(double x){ return (long)(x*ESCALA + (x>=0?0.5:-0.5)); }\n"
            "static double de_q(long q){ return (double)q/ESCALA; }\n\n"
            "void pid_reset(pid_estado_t *st){ st->I=0; st->D=0; st->e_ant=0; st->y_ant=0; st->tem_y=0; }\n\n"
            "double pid_step(pid_estado_t *st, double ref, double y){\n"
            f"    const double Kp={ctrl.Kp}, Ki={ctrl.Ki}, Kaw={ctrl.Kaw}, Ts={ctrl.Ts}, umax={ctrl.u_max};\n"
            "    static long I_q = 0;                            /* integral em Q ponto fixo */\n"
            "    double e = ref - y;\n"
            "    long inc_q = to_q(Ki*Ts*(e + st->e_ant)/2.0);   /* <-- pode arredondar p/ ZERO */\n"
            "    I_q += inc_q;\n"
            "    double v = Kp*e + de_q(I_q);\n"
            "    double u = v>umax? umax : (v<-umax? -umax : v);\n"
            "    I_q += to_q(Kaw*Ts*(u - v));\n"
            "    st->e_ant = e; st->y_ant = y; st->tem_y = 1;\n"
            "    return u;\n"
            "}\n"
        )
    return header, src


# --------------------------------------------------------------------------- #
#  3. Software-in-the-Loop (SIL)
# --------------------------------------------------------------------------- #
def sequencia_teste(ref_alvo=200.0, n=1200):
    """Sequência aberta (não é malha fechada): ref em degraus e medida perseguindo com atraso.
    Os dois controladores recebem exatamente o mesmo par (ref, y) em cada instante."""
    refs, meds = [], []
    y = 0.0
    for k in range(n):
        if k < n // 3:
            r = ref_alvo
        elif k < 2 * n // 3:
            r = ref_alvo * 1.75
        else:
            r = ref_alvo * 0.75
        y += 0.06 * (r - y)                      # medida persegue a referência com atraso
        refs.append(r)
        meds.append(y)
    return refs, meds


def rodar_modelo(ctrl, refs, meds):
    ctrl.reset()
    return [ctrl.step(r, y) for r, y in zip(refs, meds)]


def rodar_codigo_equivalente(ctrl, refs, meds, fmt="float", qn=16):
    """Equivalente do C em Python puro (fallback quando não há compilador).
    fmt='float' -> mesma sequência de operações -> erro EXATAMENTE zero.
    fmt='qN'    -> integral em ponto fixo -> erro que ACUMULA (degraus de quantização)."""
    I = 0.0
    I_q = 0
    D = 0.0
    e_ant = 0.0
    y_ant = None
    out = []
    escala = 1 << qn
    for r, y in zip(refs, meds):
        e = r - y
        if fmt == "float":
            I += ctrl.Ki * ctrl.Ts * (e + e_ant) / 2.0
            Iuso = I
        else:
            inc_q = int(math.floor(ctrl.Ki * ctrl.Ts * (e + e_ant) / 2.0 * escala + 0.5))
            I_q += inc_q
            Iuso = I_q / escala
        if ctrl.Kd > 0 and y_ant is not None:
            Tf = ctrl.Kd / (ctrl.Kp * ctrl.N) if ctrl.Kp > 0 else ctrl.Ts
            a = Tf / (Tf + ctrl.Ts)
            D = a * D - (1 - a) * ctrl.Kd * (y - y_ant) / ctrl.Ts
        v = ctrl.Kp * e + Iuso + D
        u = min(max(v, -ctrl.u_max), ctrl.u_max)
        if fmt == "float":
            I += ctrl.Kaw * ctrl.Ts * (u - v)
        else:
            I_q += int(math.floor(ctrl.Kaw * ctrl.Ts * (u - v) * escala + 0.5))
        e_ant, y_ant = e, y
        out.append(u)
    return out


EPS = 2.220446049250313e-16   # épsilon de máquina (double, 64 bits)


def comparar(saida_modelo, saida_codigo):
    difs = [abs(a - b) for a, b in zip(saida_modelo, saida_codigo)]
    max_abs = max(difs) if difs else 0.0
    i_max = difs.index(max_abs) if difs else -1
    base = max(abs(x) for x in saida_modelo) if saida_modelo else 1.0
    return {
        "max_abs": max_abs,
        "epsilons": max_abs / EPS,
        "max_rel": max_abs / base if base else 0.0,
        "amostra_pior": i_max,
        "veredito": classificar(max_abs),
    }


def classificar(max_abs):
    """Veredito FÍSICO (a saída está em volts de comando): o épsilon separa 'exato' de
    'equivalente'; a quantização do ponto fixo cai em 'pequena' (registre, mas é irrelevante
    no atuador); um bug de verdade diverge por VOLTS."""
    if max_abs == 0:
        return "EXATO (bit a bit idêntico)"
    if max_abs < 1e-9:
        return "EQUIVALENTE (da ordem do épsilon)"
    if max_abs < 1e-2:
        return "DIVERGÊNCIA PEQUENA (quantização de ponto fixo; registre no relatório)"
    return "DIVERGÊNCIA GROSSEIRA (há um bug de verdade)"


def compilador_disponivel():
    import shutil
    for cc in ("cc", "gcc", "clang"):
        if shutil.which(cc):
            return shutil.which(cc)
    return None


def sil(cen, bug=None, fmt="float", qn=16, usar_c=True):
    """Executa o SIL. Tenta compilar o C de verdade; se não houver compilador, usa o
    equivalente em Python. Devolve o relatório de comparação e como o 'código' foi obtido."""
    ctrl_ref = ctrl_de_cenario(cen)                       # modelo de referência (sempre correto)
    ctrl_cod = ctrl_de_cenario(cen, bug=bug)              # o que foi "gerado" (pode ter o bug)
    refs, meds = sequencia_teste(cen["ref"], cen["n_amostras"])
    saida_modelo = rodar_modelo(ctrl_ref, refs, meds)
    modo = "python-equivalente"
    cc = compilador_disponivel() if usar_c else None
    saida_cod = None
    if cc:
        try:
            saida_cod = _rodar_c_real(ctrl_cod, refs, meds, fmt, qn, cc)
            modo = f"C compilado com {os.path.basename(cc)} -O2"
        except Exception:
            saida_cod = None
    if saida_cod is None:
        saida_cod = rodar_codigo_equivalente(ctrl_cod, refs, meds, fmt, qn)
    rel = comparar(saida_modelo, saida_cod)
    rel["modo"] = modo
    rel["fmt"] = fmt
    rel["bug"] = bug or "nenhum"
    return rel


def _rodar_c_real(ctrl, refs, meds, fmt, qn, cc):
    """Gera o C, compila como biblioteca compartilhada com -O2 e roda via ctypes."""
    import ctypes
    import subprocess
    import tempfile
    header, src = gerar_c(ctrl, fmt, qn=qn)
    # driver C que expõe uma função de varredura sobre os vetores
    driver = (
        '#include "pid_gen.h"\n'
        "void rodar(double *ref, double *y, double *out, int n){\n"
        "    pid_estado_t st; pid_reset(&st);\n"
        "    for(int k=0;k<n;k++) out[k]=pid_step(&st, ref[k], y[k]);\n"
        "}\n"
    )
    d = tempfile.mkdtemp(prefix="u04sil_")
    with open(os.path.join(d, "pid_gen.h"), "w") as f:
        f.write(header)
    with open(os.path.join(d, "pid_gen.c"), "w") as f:
        f.write(src)
    with open(os.path.join(d, "driver.c"), "w") as f:
        f.write(driver)
    so = os.path.join(d, "libpid.so")
    subprocess.run([cc, "-O2", "-shared", "-fPIC", "-o", so,
                    os.path.join(d, "pid_gen.c"), os.path.join(d, "driver.c")],
                   check=True, capture_output=True)
    lib = ctypes.CDLL(so)
    n = len(refs)
    Arr = ctypes.c_double * n
    cref, cy, cout = Arr(*refs), Arr(*meds), Arr()
    lib.rodar(cref, cy, cout, ctypes.c_int(n))
    return list(cout)


# --------------------------------------------------------------------------- #
#  4. Hardware-in-the-Loop (HIL): laço fechado + jitter + watchdog
# --------------------------------------------------------------------------- #
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


def jitter_sim(cen):
    """Jitter determinístico por RA (reprodutível): período observado = nominal + cauda à direita.
    Modela o que o notebook da aula 15 mede, sem depender do relógio da máquina."""
    Ts_ms = cen["Ts_ms"]
    r = _mulberry32(_fnv1a(cen["codigo"] + "#jitter"))
    base = cen["jitter_med_ms"]
    pico = cen["jitter_max_ms"]
    N = 400
    durs = []
    for _ in range(N):
        x = r()
        # maior parte perto do nominal + base; cauda exponencial rara até o pico
        extra = base * x + (pico - base) * (x ** 8)
        durs.append(Ts_ms + extra)
    med = sum(durs) / N
    mx = max(durs)
    var = sum((d - med) ** 2 for d in durs) / N
    return {
        "nominal_ms": Ts_ms, "n": N,
        "medio_ms": med, "max_ms": mx, "desvio_padrao_ms": var ** 0.5,
        "jitter_medio_ms": med - Ts_ms, "jitter_max_ms": mx - Ts_ms,
        "durs": durs,
    }


def orcamento_prazo(cen, jmax_ms):
    """Liga a aula 15 à aula 11: o pior caso em períodos vira milissegundos reais.
    Compara o prazo nominal (todo ciclo = Ts) com o pessimista (todo ciclo = pior tempo)."""
    periodos = cen["wc_periodos"]                 # pior caso em períodos (herdado do watchdog/U03)
    nominal_ms = periodos * cen["Ts_ms"]
    pessimista_ms = periodos * (cen["Ts_ms"] + jmax_ms)
    limite = cen["prazo_ms"]                       # limite do REQUISITO (tem folga sobre o nominal)
    return {
        "periodos": periodos, "nominal_ms": nominal_ms,
        "pessimista_ms": pessimista_ms, "limite_ms": limite,
        "folga_nominal_ms": limite - nominal_ms,
        "folga_pessimista_ms": limite - pessimista_ms,
        "passa_nominal": nominal_ms <= limite,
        "passa_pessimista": pessimista_ms <= limite,
    }


def watchdog(cen, atrasos_ms):
    """Watchdog: se o alvo não responde dentro do prazo, devolve comando seguro (torque zero)
    e derruba o alvo (um alvo que estourou o prazo pode nunca responder)."""
    prazo = cen["prazo_wd_ms"]
    linhas = []
    derrubado = False
    for a in atrasos_ms:
        if derrubado:
            linhas.append({"atraso_ms": a, "dentro": False, "comando": "SEGURO (alvo já caído)", "ciclos": None})
            continue
        dentro = a <= prazo
        linhas.append({
            "atraso_ms": a, "dentro": dentro,
            "comando": "normal" if dentro else "SEGURO (torque 0)",
            "ciclos": round(a / cen["Ts_ms"], 1),
        })
        if not dentro:
            derrubado = True
    return {"prazo_wd_ms": prazo, "prazo_wd_ciclos": prazo / cen["Ts_ms"], "linhas": linhas}


def malha_hil(cen, t_final=2.0, bug=None):
    """Laço fechado HIL (planta simulada no host, PID no 'alvo'): devolve a trajetória.
    Integração fina interna por Ts com sub-passos de Euler (determinística)."""
    pl = Planta()
    ctrl = ctrl_de_cenario(cen, bug=bug)
    Ts = cen["Ts_ms"] / 1000.0
    ref = cen["ref"]
    sub = max(1, int(round(Ts / 2e-4)))
    dt = Ts / sub
    i = w = 0.0
    t = 0.0
    T = pl.T_op
    ts, ws, us = [], [], []
    n = int(t_final / Ts)
    for _ in range(n):
        u = ctrl.step(ref, w)
        for _ in range(sub):
            i, w = pl.passo(i, w, u, T, dt)
        t += Ts
        ts.append(t); ws.append(w); us.append(u)
    return {"t": ts, "w": ws, "u": us, "ref": ref, "convergiu": abs(ws[-1] - ref) < 0.05 * ref}


# --------------------------------------------------------------------------- #
#  5. Rastreabilidade, evidência x certificado e qualificação de ferramenta
# --------------------------------------------------------------------------- #
RE_REQ = re.compile(r"REQ-[A-Z]{2,4}-\d{3}")

REQUISITOS = [
    ("REQ-CODE-001", "O código embarcado é gerado a partir do modelo (artefato derivado), nunca editado à mão."),
    ("REQ-CODE-002", "O passo do controlador é equivalente ao modelo dentro do épsilon de máquina (SIL)."),
    ("REQ-SAFE-006", "O torque chega a zero dentro do prazo, respeitado o jitter medido (HIL)."),
    ("REQ-SAFE-001", "Nunca habilitar torque com obstáculo presente (supervisor, herdado da U03)."),
    ("REQ-CODE-003", "Cada artefato gerado carrega assinatura que o liga aos parâmetros de origem."),
]


def matriz_rastreabilidade(raiz="."):
    """Varre a árvore procurando marcadores REQ e classifica por pasta (modelo/código/teste)."""
    achados = {req: {"modelo": set(), "codigo": set(), "teste": set(), "desc": desc}
               for req, desc in REQUISITOS}
    n_arq = n_com = 0
    for base, _dirs, arqs in os.walk(raiz):
        if any(x in base for x in (".git", "__pycache__", "figs")):
            continue
        for a in arqs:
            if not a.endswith((".py", ".c", ".h", ".md", ".json")):
                continue
            cam = os.path.join(base, a)
            n_arq += 1
            try:
                with open(cam, encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
            except OSError:
                continue
            reqs = set(RE_REQ.findall(txt))
            if reqs:
                n_com += 1
            low = (base + "/" + a).lower()
            cat = ("teste" if ("test" in low or a.startswith("p") and "memorial" not in low)
                   else "codigo" if (a.endswith((".c", ".h")) or "gen" in low)
                   else "modelo")
            for req in reqs:
                if req in achados:
                    achados[req][cat].add(cam)
    tabela = []
    for req, desc in REQUISITOS:
        d = achados[req]
        tabela.append({"req": req, "desc": desc,
                       "modelo": len(d["modelo"]), "codigo": len(d["codigo"]),
                       "teste": len(d["teste"]),
                       "vazio_teste": len(d["teste"]) == 0})
    return {"n_arquivos": n_arq, "n_com_req": n_com, "tabela": tabela}


EVIDENCIAS_PRODUZ = [
    "Modelo executável da planta identificado por ensaio (U01).",
    "Controlador PID projetado com período de amostragem justificado (U02).",
    "Requisitos formais e verificação exaustiva do supervisor (U03).",
    "Código C gerado do modelo, com assinatura de rastreabilidade (U04/a13).",
    "Comparação numérica modelo x código (SIL), erro medido em épsilons (U04/a14).",
    "Medição de jitter e prazo de pior caso em tempo real (HIL) (U04/a15).",
    "Watchdog com comando seguro demonstrado em falha do alvo (U04/a15).",
    "Matriz de rastreabilidade derivada do código (U04/a16).",
    "Análise do que o pipeline prova e do que não prova (U04/a16).",
]
EVIDENCIAS_NAO = [
    "Qualificação das ferramentas segundo a DO-330.",
    "Cobertura estrutural MC/DC do código (houve só cobertura de transição do modelo).",
    "Análise estática do código-fonte segundo regras MISRA C.",
    "Certificação por autoridade — evidência não é certificado.",
    "Ensaio físico no robô real — HIL usa planta simulada.",
]

FERRAMENTAS = [
    # (nome, pode_introduzir_erro, permite_pular_verificacao, erro_detectado_por_outra_atividade)
    ("Gerador de código C", True, False, True),
    ("Model checker (U03)", False, True, False),
    ("Gerador de testes (MBT)", False, True, True),
    ("Compilador C (gcc -O2)", True, False, True),
    ("Biblioteca de gráficos", False, False, True),
]


def qualificar_ferramenta():
    """DO-330: a exigência de qualificação depende de 3 perguntas, nenhuma sobre licença/preço."""
    out = []
    for nome, p1, p2, p3 in FERRAMENTAS:
        exige = p1 or p2            # qualifica se pode introduzir erro OU deixar de detectar
        out.append({"ferramenta": nome, "introduz_erro": p1, "permite_pular": p2,
                    "detectado_por_outra": p3,
                    "exige_qualificacao": exige})
    return out


# --------------------------------------------------------------------------- #
#  Gerador por RA (idêntico à U01/U02/U03: FNV-1a + mulberry32)
# --------------------------------------------------------------------------- #
def normaliza(codigo):
    return re.sub(r"[^A-Z0-9-]", "", str(codigo or "").upper())


def _fnv1a(t):
    h = 0x811C9DC5
    for ch in t:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


LINHAS = [
    ("celula", "Célula de montagem", "braço + esteira"),
    ("agv", "AGV de armazém", "redutor + roda"),
    ("paletizadora", "Paletizadora robotizada", "braço paletizador"),
    ("solda", "Estação de solda", "robô de solda"),
    ("triagem", "Esteira de triagem", "desviadores + esteira"),
]
TS_OPCOES = [2, 4, 5]
QFORMATOS = [(16, 16), (12, 20), (20, 12), (8, 24)]   # (m parte inteira, n parte fracionária)


def gerar_cenario(codigo):
    """Gera a variante do aluno. O NexaBot é o mesmo para todos; o RA individualiza
    período, formato de ponto fixo, referência, orçamento de prazo e perfil de jitter."""
    cod = normaliza(codigo) or "NT"
    r = _mulberry32(_fnv1a(cod))

    def ri(n):
        return int(r() * n)

    def rnd(x, casas):                            # arredondamento half-up (igual em Python e JS)
        f = 10 ** casas
        return math.floor(x * f + 0.5) / f

    linha = LINHAS[ri(len(LINHAS))]
    Ts = TS_OPCOES[ri(len(TS_OPCOES))]
    qm, qn = QFORMATOS[ri(len(QFORMATOS))]
    ref = [150, 200, 250, 300][ri(4)]
    # ganhos (escala leve em torno do PI de referência, mantendo estabilidade a Ts<=5 ms)
    kp = rnd(GANHOS_REF["Kp"] * (0.8 + 0.4 * r()), 3)
    ki = rnd(GANHOS_REF["Ki"] * (0.7 + 0.6 * r()), 2)
    ganhos = {"Kp": kp, "Ki": ki, "Kd": 0.0, "Kaw": 100.0, "N": 10.0}
    # erro por ciclo usado no acumulador (pequeno de propósito, para flertar com o degrau)
    erro_ciclo = rnd((0.4 + 1.6 * r()) / 1000.0, 5)
    ciclos = 2000 + 200 * ri(11)
    # pior caso em períodos até zerar o torque (herdado do watchdog da U03/a11)
    wc_periodos = 24 + ri(12)
    # limite do REQUISITO: pior caso + folga de projeto (1,3 a 1,8x) -> dá margem no nominal
    folga = 1.3 + 0.5 * r()
    prazo_ms = math.floor(wc_periodos * Ts * folga + 0.5)
    prazo_wd_ms = (2 + ri(5)) * Ts * 3            # prazo do watchdog (HAL-006), múltiplo de Ts
    jitter_med = rnd((0.05 + 0.20 * r()) * Ts, 3)
    jitter_max = rnd(jitter_med * (2 + 3 * r()), 3)
    tag = 10 + ri(90)
    return {
        "codigo": cod, "linha": linha[0],
        "nome": f"{linha[1]} {linha[0][:3].upper()}-{tag}", "composicao": linha[2],
        "Ts_ms": Ts, "qm": qm, "qn": qn, "ref": float(ref),
        "ganhos": ganhos, "erro_ciclo": erro_ciclo, "ciclos": ciclos,
        "n_amostras": 1200,
        "wc_periodos": wc_periodos, "prazo_ms": prazo_ms,
        "prazo_wd_ms": prazo_wd_ms,
        "jitter_med_ms": jitter_med, "jitter_max_ms": jitter_max,
        "origem": f"gerador u04lab {VERSAO}",
    }


def resumo(cen):
    """Números derivados do cenário (o 'gabarito' da máquina do aluno)."""
    qi = q_info(cen["qm"], cen["qn"])
    ctrl = ctrl_de_cenario(cen)
    acc = acumulador(cen["erro_ciclo"], cen["ciclos"], cen["ganhos"]["Ki"], cen["Ts_ms"] / 1000.0, cen["qn"])
    # gabarito canônico: caminho determinístico (equivalente em Python), para bater com o JS
    # e não depender de haver compilador. O SIL com C real fica para a CLI e os scripts.
    sil_ok = sil(cen, bug=None, fmt="float", usar_c=False)
    sil_fx = sil(cen, bug=None, fmt="q%d" % cen["qn"], qn=cen["qn"], usar_c=False)
    sil_bug = sil(cen, bug="antiwindup", fmt="float", usar_c=False)
    jit = jitter_sim(cen)
    orc = orcamento_prazo(cen, jit["jitter_max_ms"])
    return {
        "assinatura": assinatura(ctrl, "float"),
        "q_degrau": qi["degrau"], "q_max": qi["max"], "q_min": qi["min"],
        "acc_desvio": acc["desvio"], "acc_degraus": acc["degraus"], "acc_inc_sumiu": acc["inc_sumiu"],
        "sil_ok_epsilons": sil_ok["epsilons"], "sil_ok_veredito": sil_ok["veredito"],
        "sil_fx_epsilons": sil_fx["epsilons"], "sil_fx_veredito": sil_fx["veredito"],
        "sil_bug_abs": sil_bug["max_abs"], "sil_bug_amostra": sil_bug["amostra_pior"],
        "sil_bug_veredito": sil_bug["veredito"],
        "jitter_medio_ms": jit["jitter_medio_ms"], "jitter_max_ms": jit["jitter_max_ms"],
        "prazo_nominal_ms": orc["nominal_ms"], "prazo_pessimista_ms": orc["pessimista_ms"],
        "prazo_passa": orc["passa_pessimista"], "folga_pessimista_ms": orc["folga_pessimista_ms"],
        "prazo_wd_ciclos": cen["prazo_wd_ms"] / cen["Ts_ms"],
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
            print(f"\n[ok] controlador salvo em {destino}")
    elif cmd == "gerar":
        fmt = _flag(args, "--fmt", "float")
        ctrl = ctrl_de_cenario(cen)
        h, s = gerar_c(ctrl, fmt, qn=cen["qn"])
        print(h)
        print(s)
        print(f"[assinatura] {assinatura(ctrl, fmt)}")
    elif cmd == "pontofixo":
        qi = q_info(cen["qm"], cen["qn"])
        acc = acumulador(cen["erro_ciclo"], cen["ciclos"], cen["ganhos"]["Ki"], cen["Ts_ms"] / 1000.0, cen["qn"])
        print(f"Formato Q{qi['m']}.{qi['n']}  degrau={qi['degrau']:.3e}  faixa=[{qi['min']:.0f}, {qi['max']:.0f}]")
        print(f"Acumulador ({cen['ciclos']} ciclos): desvio={acc['desvio']:.3e} = {acc['degraus']:.1f} degraus"
              + ("   <-- INCREMENTO VIROU ZERO" if acc["inc_sumiu"] else ""))
    elif cmd == "sil":
        bug = "antiwindup" if _flag(args, "--bug") else None
        fmt = _flag(args, "--fmt", "float")
        qn = cen["qn"] if fmt.startswith("q") else 16
        rel = sil(cen, bug=bug, fmt=fmt, qn=qn)
        print(f"SIL [{rel['modo']}]  fmt={rel['fmt']}  bug={rel['bug']}")
        print(f"  erro máx = {rel['max_abs']:.3e}  ({rel['epsilons']:.1f} épsilons)  amostra {rel['amostra_pior']}")
        print(f"  veredito: {rel['veredito']}")
    elif cmd == "hil":
        jit = jitter_sim(cen)
        orc = orcamento_prazo(cen, jit["jitter_max_ms"])
        print(f"HIL · Ts={cen['Ts_ms']} ms · {jit['n']} ciclos")
        print(f"  período médio = {jit['medio_ms']:.3f} ms (jitter médio {jit['jitter_medio_ms']:.3f} ms)")
        print(f"  pior caso     = {jit['max_ms']:.3f} ms (jitter máx {jit['jitter_max_ms']:.3f} ms)")
        print(f"  prazo: nominal {orc['nominal_ms']:.1f} ms / pessimista {orc['pessimista_ms']:.1f} ms "
              f"/ limite {orc['limite_ms']} ms -> {'PASSA' if orc['passa_pessimista'] else 'VIOLA'}")
    elif cmd == "rastrear":
        mr = matriz_rastreabilidade(_flag(args, "--raiz", "."))
        print(f"{mr['n_arquivos']} arquivos varridos, {mr['n_com_req']} com marcador de requisito\n")
        print(f"{'REQ':<16}{'modelo':>7}{'código':>8}{'teste':>7}  descrição")
        for l in mr["tabela"]:
            flag = "  <-- SEM TESTE" if l["vazio_teste"] else ""
            print(f"{l['req']:<16}{l['modelo']:>7}{l['codigo']:>8}{l['teste']:>7}  {l['desc'][:40]}{flag}")
    elif cmd == "relatorio":
        print(json.dumps({"cenario": cen, "resumo": resumo(cen)}, ensure_ascii=False, indent=2))
    else:
        print(f"comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
