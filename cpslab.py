"""cpslab - Laboratório genérico de Sistemas Ciberfísicos (NovaTech Ltda.)

Funciona com QUALQUER planta acionada por motor CC de ímã permanente:
um cenário sorteado pelo código (ex.: seu RA), um JSON escrito por você
ou os dados de um datasheet/artigo.

Uso pela linha de comando:
    uv run python cpslab.py cenario NT-12345 --salvar planta.json
    uv run python cpslab.py relatorio planta.json
    uv run python cpslab.py datasheet --help
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict, replace

import numpy as np

VERSAO = "2.1"

# ---------------------------------------------------------------------------
# 1. Gerador de cenários (idêntico ao do navegador: mesma semente, mesmos números)
# ---------------------------------------------------------------------------
TIPOS = [
    # id, nome, tensões possíveis, transmissão, carga do processo
    ("esteira", "Esteira transportadora", (24, 36, 48), "rolo de tração + correia", "peças sobre a correia"),
    ("agv", "AGV de armazém", (24, 36, 48), "redutor + roda", "caixa transportada"),
    ("junta", "Junta de braço robótico", (24, 48), "redutor harmônico", "payload na garra"),
    ("ventilador", "Ventilador de resfriamento do painel", (12, 24), "hélice", "fluxo de ar e poeira no filtro"),
    ("bomba", "Bomba dosadora", (12, 24, 36), "rotor da bomba", "pressão e viscosidade do fluido"),
]


def _normaliza(codigo: str) -> str:
    return re.sub(r"[^A-Z0-9-]", "", str(codigo).upper())


def _fnv1a(texto: str) -> int:
    h = 0x811C9DC5
    for b in texto.encode("ascii"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def _imul(a: int, b: int) -> int:
    return (a * b) & 0xFFFFFFFF


def _mulberry32(semente: int):
    estado = [semente & 0xFFFFFFFF]

    def proximo() -> float:
        estado[0] = (estado[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = estado[0]
        t = _imul(t ^ (t >> 15), t | 1)
        t ^= (t + _imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return proximo


def _polos_2x2(R, L, Kt, Ke, J, B):
    a11, a12, a21, a22 = -R / L, -Ke / L, Kt / J, -B / J
    tr = a11 + a22
    det = a11 * a22 - a12 * a21
    disc = tr * tr - 4 * det
    if disc <= 0:
        return None
    s = math.sqrt(disc)
    return ((tr - s) / 2, (tr + s) / 2)        # (rápido, lento)


def gerar_cenario(codigo: str) -> dict:
    """Sorteia uma máquina da NovaTech a partir de um código (ex.: RA do aluno)."""
    cod = _normaliza(codigo) or "NT"
    r = _mulberry32(_fnv1a(cod))

    def ri(n):
        return math.floor(r() * n)

    for _ in range(2000):
        tipo = TIPOS[ri(len(TIPOS))]
        V_max = tipo[2][ri(len(tipo[2]))]
        R = (20 + ri(181)) / 100
        L = (5 + ri(46)) / 10000
        K = (20 + ri(101)) / 1000
        J = (5 + ri(96)) / 100000
        B = (2 + ri(39)) / 100000
        Ts = (1, 2, 5, 10)[ri(4)] / 1000
        frac_w = (50 + ri(36)) / 100
        frac_T = (40 + ri(46)) / 100
        folga_I = (15 + ri(11)) / 10
        tag = 10 + ri(90)
        p = _polos_2x2(R, L, K, K, J, B)
        if p is None:
            continue
        p_r, p_l = p
        if p_r / p_l < 8:
            continue
        tau_m = -1 / p_l
        if not (8 <= tau_m / Ts <= 80):
            continue
        G0 = K / (R * B + K * K)
        w_op = math.floor(frac_w * V_max * G0 + 0.5)
        T_disp = K * (V_max - K * w_op) / R - B * w_op
        if T_disp <= 0:
            continue
        T_op = math.floor(T_disp * frac_T * 1000 + 0.5) / 1000
        if T_op < 0.001:
            continue
        i_ss = (B * w_op + T_op) / K
        V_ss = R * i_ss + K * w_op
        if not (0.05 <= (V_max - V_ss) / V_max <= 0.40):
            continue
        I_max = math.floor(i_ss * folga_I) + 1
        a21, b1 = K / J, 1 / L
        p_lim = math.sqrt(V_max * a21 * b1 / w_op)
        if not (2.5 <= p_lim / -p_l <= 14):
            continue
        return {
            "codigo": cod, "tipo": tipo[0], "nome": f"{tipo[1]} {tipo[0][:3].upper()}-{tag}",
            "transmissao": tipo[3], "carga": tipo[4],
            "R": R, "L": L, "Kt": K, "Ke": K, "J": J, "B": B,
            "V_max": float(V_max), "I_max": float(I_max), "Ts": Ts,
            "w_op": float(w_op), "T_op": T_op, "origem": "gerador cpslab " + VERSAO,
        }
    raise RuntimeError("não foi possível gerar cenário para este código")


# ---------------------------------------------------------------------------
# 2. A planta (qualquer motor CC de ímã permanente)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Planta:
    nome: str
    R: float        # resistência de armadura [ohm]
    L: float        # indutância de armadura [H]
    Kt: float       # constante de torque [N.m/A]
    Ke: float       # constante de f.c.e.m. [V.s/rad]
    J: float        # inércia no eixo do motor [kg.m^2]
    B: float        # atrito viscoso [N.m.s/rad]
    V_max: float    # tensão máxima do driver [V]
    I_max: float    # corrente máxima do driver [A]
    Ts: float       # período de amostragem do controlador [s]
    w_op: float     # velocidade do ponto de operação [rad/s]
    T_op: float     # torque de carga do ponto de operação [N.m]
    codigo: str = ""
    tipo: str = "livre"
    transmissao: str = "transmissão"
    carga: str = "carga"
    origem: str = "manual"

    @classmethod
    def de_dict(cls, d: dict) -> "Planta":
        campos = cls.__dataclass_fields__
        return cls(**{k: v for k, v in d.items() if k in campos})

    @classmethod
    def carregar(cls, caminho: str = "planta.json") -> "Planta":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    @classmethod
    def de_codigo(cls, codigo: str) -> "Planta":
        return cls.de_dict(gerar_cenario(codigo))

    def salvar(self, caminho: str = "planta.json") -> None:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    # ---- modelo -----------------------------------------------------------
    def matrizes(self):
        A = np.array([[-self.R / self.L, -self.Ke / self.L],
                      [self.Kt / self.J, -self.B / self.J]])
        B = np.array([[1.0 / self.L], [0.0]])
        C = np.array([[0.0, 1.0]])
        D = np.array([[0.0]])
        return A, B, C, D

    def derivadas(self, x, V, T):
        i, w = x
        return np.array([(V - self.R * i - self.Ke * w) / self.L,
                         (self.Kt * i - self.B * w - T) / self.J])

    def polos(self):
        """(polo rápido/elétrico, polo lento/mecânico) em rad/s."""
        A, *_ = self.matrizes()
        ev = np.linalg.eigvals(A)
        if np.max(np.abs(ev.imag)) > 1e-9:
            return tuple(sorted(ev, key=lambda z: z.real))
        ev = np.sort(ev.real)
        return float(ev[0]), float(ev[1])

    def taus(self):
        p_r, p_l = self.polos()
        return -1 / np.real(p_r), -1 / np.real(p_l)

    def ganho_estatico(self):
        return self.Kt / (self.R * self.B + self.Kt * self.Ke)

    def regime(self, w=None, T=None):
        """Corrente e tensão para sustentar w sob T (derivadas = 0)."""
        w = self.w_op if w is None else w
        T = self.T_op if T is None else T
        i = (self.B * w + T) / self.Kt
        return i, self.R * i + self.Ke * w

    def queda_por_torque(self):
        """rad/s perdidos por N.m de carga em malha aberta."""
        return self.R / (self.R * self.B + self.Kt * self.Ke)

    def dt_sugerido(self):
        return self.taus()[0] / 20

    def simular(self, V, T=0.0, t_final=None, dt=None, x0=(0.0, 0.0)):
        """Runge-Kutta 4. V e T podem ser números ou funções f(t)."""
        dt = dt or self.dt_sugerido()
        t_final = t_final or 6 * self.taus()[1]
        fV = V if callable(V) else (lambda t: V)
        fT = T if callable(T) else (lambda t: T)
        n = int(round(t_final / dt)) + 1
        t = np.linspace(0, (n - 1) * dt, n)
        x = np.zeros((n, 2)); x[0] = x0
        for k in range(n - 1):
            tk, xk = t[k], x[k]
            k1 = self.derivadas(xk, fV(tk), fT(tk))
            k2 = self.derivadas(xk + dt / 2 * k1, fV(tk + dt / 2), fT(tk + dt / 2))
            k3 = self.derivadas(xk + dt / 2 * k2, fV(tk + dt / 2), fT(tk + dt / 2))
            k4 = self.derivadas(xk + dt * k3, fV(tk + dt), fT(tk + dt))
            x[k + 1] = xk + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        return t, x[:, 0], x[:, 1]

    # ---- análise ----------------------------------------------------------
    def postos(self):
        import control as ct
        A, B, C, _ = self.matrizes()
        return (int(np.linalg.matrix_rank(ct.ctrb(A, B))),
                int(np.linalg.matrix_rank(ct.obsv(A, C))))

    def u0_polo_duplo(self, p, ref=None):
        """Tensão pedida em t=0 (x=0) pela realimentação de estados com polo duplo p."""
        ref = self.w_op if ref is None else ref
        return ref * p * p * self.J * self.L / self.Kt

    def polo_limite(self, ref=None):
        """Polo duplo mais rápido cujo u(0) cabe em V_max."""
        ref = self.w_op if ref is None else ref
        return -math.sqrt(self.V_max * self.Kt / (self.J * self.L * ref))

    def kp_padrao(self):
        """Ganho proporcional de velocidade do ataque de atraso.

        Escolhido para ganho de malha = 0,4 x (tau_m / Ts): assim o atraso crítico
        fica perto de 4 amostras em qualquer planta (mesma regra do navegador).
        """
        p = _polos_2x2(self.R, self.L, self.Kt, self.Ke, self.J, self.B)
        tau_m = -1 / p[1] if p else self.taus()[1]
        return math.floor(0.4 * (tau_m / self.Ts) / self.ganho_estatico() * 10000 + 0.5) / 10000

    def raio_com_atraso(self, Kp, d):
        """Raio espectral da malha discreta u = -Kp*y[k-d] (ZOH em Ts)."""
        from scipy.linalg import expm
        A, B, C, _ = self.matrizes()
        M = np.zeros((3, 3)); M[:2, :2] = A; M[:2, 2:] = B
        E = expm(M * self.Ts)
        Ad, Bd = E[:2, :2], E[:2, 2:]
        n = 2 + d
        F = np.zeros((n, n))
        if d == 0:
            F[:2, :2] = Ad - Kp * Bd @ C
        else:
            F[:2, :2] = Ad
            F[:2, n - 1:n] = -Kp * Bd
            F[2, :2] = C
            for k in range(1, d):
                F[2 + k, 1 + k] = 1.0
        return float(max(abs(np.linalg.eigvals(F))))

    def atraso_critico(self, Kp=None, d_max=20):
        Kp = self.kp_padrao() if Kp is None else Kp
        for d in range(d_max + 1):
            if self.raio_com_atraso(Kp, d) >= 1:
                return d
        return None


# ---------------------------------------------------------------------------
# 3. Datasheet -> parâmetros SI
# ---------------------------------------------------------------------------
def de_datasheet(nome, R_ohm, L_mH, Kt_mNm_A, J_gcm2, V_nominal, n0_rpm=None, I0_mA=None,
                 B_SI=None, V_max=None, I_max=None, Ts_ms=5.0, w_op=None, T_op=None):
    """Converte unidades típicas de catálogo para o SI.

    - Kt em mN.m/A -> N.m/A; no SI, Ke [V.s/rad] tem o mesmo valor de Kt [N.m/A].
    - J em g.cm^2 -> kg.m^2 (divide por 10^7).
    - B: se não informado, estimado pela corrente em vazio: B = Kt*I0/w0.
    """
    Kt = Kt_mNm_A / 1000
    J = J_gcm2 / 1e7
    if B_SI is None:
        if n0_rpm and I0_mA:
            B_SI = Kt * (I0_mA / 1000) / (n0_rpm * 2 * math.pi / 60)
        else:
            raise ValueError("informe B_SI ou (n0_rpm e I0_mA) para estimar o atrito")
    V_max = V_max or V_nominal
    w0 = V_max * Kt / (R_ohm * B_SI + Kt * Kt)
    w_op = w_op or math.floor(0.7 * w0 + 0.5)
    T_op = T_op if T_op is not None else round(0.5 * (Kt * (V_max - Kt * w_op) / R_ohm - B_SI * w_op), 4)
    i_ss = (B_SI * w_op + T_op) / Kt
    return Planta(nome=nome, R=R_ohm, L=L_mH / 1000, Kt=Kt, Ke=Kt, J=J, B=B_SI, V_max=float(V_max),
                  I_max=float(I_max or math.ceil(2 * i_ss)), Ts=Ts_ms / 1000, w_op=float(w_op),
                  T_op=float(T_op), tipo="datasheet", origem="datasheet")


# ---------------------------------------------------------------------------
# 4. Identificação (motor "sem manual")
# ---------------------------------------------------------------------------
def gerar_ensaio(p: Planta, V, semente=1, fator_adulteracao=1.0):
    rng = np.random.default_rng(semente)
    t, i, w = p.simular(V, t_final=6 * p.taus()[1], dt=p.taus()[1] / 400)
    passo = max(abs(w[-1]) / 500, 1e-6)
    i_med = i + rng.normal(0, 0.01 * max(abs(i).max(), 1e-6), i.size)
    w_med = np.round(w * fator_adulteracao / passo) * passo
    return t, i_med, w_med


def identificar(p_ref: Planta, t, V, i_med, w_med, chute=None):
    from scipy.optimize import least_squares
    p0 = np.array(chute if chute is not None else [p_ref.R, p_ref.L, p_ref.Kt, p_ref.J, p_ref.B])
    esc_w = max(abs(w_med).max(), 1e-6); esc_i = max(abs(i_med).max(), 1e-6)

    def candidato(z):
        R, L, K, J, B = z * p0
        return replace(p_ref, R=R, L=L, Kt=K, Ke=K, J=J, B=B)

    def residuo(z):
        _, i_s, w_s = candidato(z).simular(V, t_final=t[-1], dt=t[1] - t[0])
        return np.concatenate([(i_s - i_med) / esc_i, (w_s - w_med) / esc_w])

    r = least_squares(residuo, np.ones(5), bounds=(0.05, 20), xtol=1e-12, ftol=1e-12, gtol=1e-12)
    return candidato(r.x), r.nfev


def fit_percent(medido, previsto):
    medido, previsto = np.asarray(medido), np.asarray(previsto)
    return float(100 * (1 - np.linalg.norm(medido - previsto) / np.linalg.norm(medido - medido.mean())))


# ---------------------------------------------------------------------------
# 5. Controle digital (Unidade 02): malha fechada, PID, amostragem, co-simulação
#    Tudo aqui tem um "gêmeo" idêntico em JavaScript (jogo e páginas da U02):
#    mesma conta, mesma ordem, mesmos números.
# ---------------------------------------------------------------------------
def _mul22(M, v):
    return (M[0][0] * v[0] + M[0][1] * v[1], M[1][0] * v[0] + M[1][1] * v[1])


def zoh(p: Planta, h: float):
    """Discretização EXATA da planta para entrada constante durante h segundos (ZOH).

    Devolve (Ad, Bv, Bt): x[k+1] = Ad·x[k] + Bv·V[k] + Bt·T[k]
    (V = tensão aplicada, T = torque de carga).
    """
    a11, a12, a21, a22 = -p.R / p.L, -p.Ke / p.L, p.Kt / p.J, -p.B / p.J
    l1, l2 = _polos_2x2(p.R, p.L, p.Kt, p.Ke, p.J, p.B)
    v1, v2 = (a12, l1 - a11), (a12, l2 - a11)
    dt = v1[0] * v2[1] - v2[0] * v1[1]
    e1, e2 = math.exp(l1 * h), math.exp(l2 * h)
    Vi = ((v2[1] / dt, -v2[0] / dt), (-v1[1] / dt, v1[0] / dt))
    Ad = tuple(tuple(v1[i] * e1 * Vi[0][j] + v2[i] * e2 * Vi[1][j] for j in range(2)) for i in range(2))
    det = a11 * a22 - a12 * a21
    Ai = ((a22 / det, -a12 / det), (-a21 / det, a11 / det))
    M = ((Ad[0][0] - 1, Ad[0][1]), (Ad[1][0], Ad[1][1] - 1))
    Bv = _mul22(Ai, _mul22(M, (1 / p.L, 0.0)))
    Bt = _mul22(Ai, _mul22(M, (0.0, -1 / p.J)))
    return Ad, Bv, Bt


class PIDDiscreto:
    """PID digital como roda no microcontrolador: soma em vez de integral.

    - integral pelo método escolhido: 'tustin' (padrão), 'euler_tras' ou 'euler_frente'
    - derivativo sobre a MEDIDA, com filtro de 1ª ordem (Tf = Kd / (Kp·N))
    - saturação em ±u_max e anti-windup por back-calculation (Kaw, em 1/s)
    """

    def __init__(self, Kp, Ki=0.0, Kd=0.0, Ts=0.005, u_max=24.0, Kaw=0.0, N=10.0, metodo="tustin"):
        self.Kp, self.Ki, self.Kd, self.Ts = float(Kp), float(Ki), float(Kd), float(Ts)
        self.u_max, self.Kaw, self.N, self.metodo = float(u_max), float(Kaw), float(N), metodo
        self.reset()

    def reset(self):
        self.I = 0.0
        self.D = 0.0
        self.e_ant = 0.0
        self.y_ant = None
        self.v = 0.0

    def step(self, ref, y):
        e = ref - y
        if self.metodo == "euler_frente":
            self.I += self.Ki * self.Ts * self.e_ant
        elif self.metodo == "euler_tras":
            self.I += self.Ki * self.Ts * e
        else:
            self.I += self.Ki * self.Ts * (e + self.e_ant) / 2
        if self.Kd > 0 and self.y_ant is not None:
            Tf = self.Kd / (self.Kp * self.N) if self.Kp > 0 else self.Ts
            a = Tf / (Tf + self.Ts)
            self.D = a * self.D - (1 - a) * self.Kd * (y - self.y_ant) / self.Ts
        v = self.Kp * e + self.I + self.D
        u = min(max(v, -self.u_max), self.u_max)
        self.I += self.Kaw * self.Ts * (u - v)
        self.e_ant, self.y_ant, self.v = e, y, v
        return u


def _degraus(x, t):
    """x pode ser número, função f(t) ou lista de degraus [(t0, valor0), (t1, valor1), ...]."""
    if callable(x):
        return x(t)
    if isinstance(x, (list, tuple)):
        val = 0.0
        for ti, vi in x:
            if t >= ti - 1e-12:
                val = vi
        return val
    return float(x)


def _ruido(semente):
    r = _mulberry32(semente)
    return lambda: 2 * r() - 1


def malha(p: Planta, Kp=None, Ki=0.0, Kd=0.0, Kaw=0.0, N=10.0, Ts=None, ref=None, carga=0.0,
          t_final=None, vies=None, atraso=0, metodo="tustin", saturar=True, ruido=0.0, semente=7,
          guarda=None, V_aberta=None):
    """Simula o laço digital: mede -> compara -> corrige, a cada Ts.

    Kp=None  -> MALHA ABERTA: tensão calculada uma única vez (V_aberta ou ref/G0).
    vies     -> (t_inicio, fator): ataque ao sensor, a leitura vira fator·ω real.
    atraso   -> amostras de atraso computacional (DoS / jitter): u[k] só é aplicado em k+atraso.
    ruido    -> ruído de medição, fração de w_op (determinístico pela semente).
    guarda   -> (ref_max, taxa_max): limitador de setpoint (defesa contra injeção de referência).
    """
    Ts = Ts or p.Ts
    ref = p.w_op if ref is None else ref
    t_final = t_final or 10 * p.taus()[1]
    Ad, Bv, Bt = zoh(p, Ts)
    n = int(round(t_final / Ts))
    x = (0.0, 0.0)
    pid = None if Kp is None else PIDDiscreto(Kp, Ki, Kd, Ts, p.V_max if saturar else 1e18, Kaw, N, metodo)
    rnd = _ruido(semente)
    fila = [0.0] * atraso
    r_g = 0.0
    out = {k: [] for k in ("t", "w", "y", "u", "v", "i", "r", "T")}
    for k in range(n + 1):
        t = k * Ts
        w = x[1]
        y = w
        if vies is not None and t >= vies[0] - 1e-12:
            y = w * vies[1]
        if ruido:
            y += ruido * p.w_op * rnd()
        r = _degraus(ref, t)
        if guarda is not None:
            r = min(max(r, 0.0), guarda[0])
            passo = guarda[1] * Ts
            r_g = r_g + min(max(r - r_g, -passo), passo)
            r = r_g
        if pid is None:
            v = V_aberta if V_aberta is not None else _degraus(ref, 0.0) / p.ganho_estatico()
            u = min(max(v, -p.V_max), p.V_max) if saturar else v
        else:
            u = pid.step(r, y)
            v = pid.v
        if atraso:
            fila.append(u)
            u_ap = fila.pop(0)
        else:
            u_ap = u
        T = _degraus(carga, t)
        for nome, val in (("t", t), ("w", w), ("y", y), ("u", u_ap), ("v", v), ("i", x[0]), ("r", r), ("T", T)):
            out[nome].append(val)
        a, b = _mul22(Ad, x), (Bv[0] * u_ap + Bt[0] * T, Bv[1] * u_ap + Bt[1] * T)
        x = (a[0] + b[0], a[1] + b[1])
        if not (abs(x[1]) < 1e9):
            break
    return out


def metricas(res, V_max, t_carga=None):
    """Indicadores de aceitação de um ensaio (os mesmos do jogo)."""
    t, w, r, v = res["t"], res["w"], res["r"], res["v"]
    n = len(t)
    if n < 2 or not all(abs(x) < 1e8 for x in w):
        return {"instavel": True}
    nf = max(1, n // 20)
    w_fin = sum(w[n - nf:]) / nf
    r_fin = r[-1]
    k_c = n if t_carga is None else next((k for k in range(n) if t[k] >= t_carga - 1e-12), n)
    r1 = r[k_c - 1] if k_c > 0 else r_fin
    w_max = max(w[:k_c]) if k_c > 0 else max(w)
    sob = max(0.0, 100 * (w_max - r1) / r1) if r1 else 0.0
    sat = [abs(vk) > V_max + 1e-9 for vk in v]
    n4 = max(1, n // 4)
    ult = w[n - n4:]
    med = sum(ult) / len(ult)
    osc = math.sqrt(sum((x - med) ** 2 for x in ult) / len(ult))
    t_ac = 0.0
    for k in range(k_c):
        if abs(w[k] - r1) > 0.02 * abs(r1):
            t_ac = t[k] + (t[1] - t[0])
    return {
        "instavel": False,
        "w_final": w_fin,
        "erro_final": r_fin - w_fin,
        "erro_pct": 100 * (r_fin - w_fin) / r_fin if r_fin else 0.0,
        "sobressinal": sob,
        "pico_V_partida": max(abs(x) for x in v[:k_c]) if k_c > 0 else 0.0,
        "pico_V_carga": max(abs(x) for x in v[k_c:]) if k_c < n else 0.0,
        "ciclos_sat": sum(sat),
        "sat_final": sum(sat[n - n4:]),
        "t_acomodacao": t_ac,
        "oscilacao": osc,
    }


def matriz_malha(p: Planta, Kp, Ki=0.0, Ts=None, metodo="tustin", atraso=0):
    """Matriz F da malha fechada discreta: z[k+1] = F·z[k] (sem saturação).

    Estados: corrente, velocidade, [integral, erro anterior] e 'atraso' comandos na fila.
    """
    Ts = Ts or p.Ts
    Ad, Bv, _ = zoh(p, Ts)
    ni = 2 if Ki else 0                      # sem integral, os estados I e e_ant não existem
    n = 2 + ni + atraso
    F = [[0.0] * n for _ in range(n)]
    for c in range(n):
        z = [0.0] * n
        z[c] = 1.0
        x1, x2 = z[0], z[1]
        I, e_ant = (z[2], z[3]) if ni else (0.0, 0.0)
        e = -x2
        if metodo == "euler_frente":
            I = I + Ki * Ts * e_ant
        elif metodo == "euler_tras":
            I = I + Ki * Ts * e
        else:
            I = I + Ki * Ts * (e + e_ant) / 2
        u = Kp * e + I
        fila = z[2 + ni:] + [u]
        u_ap = fila.pop(0)
        nz = [Ad[0][0] * x1 + Ad[0][1] * x2 + Bv[0] * u_ap,
              Ad[1][0] * x1 + Ad[1][1] * x2 + Bv[1] * u_ap] + ([I, e] if ni else []) + fila
        for r in range(n):
            F[r][c] = nz[r]
    return F


def raio_espectral(F):
    return float(max(abs(np.linalg.eigvals(np.array(F)))))


def ts_critico(p: Planta, Kp, Ki=0.0, metodo="tustin", atraso=0):
    """Menor período de amostragem que torna a malha instável (raio espectral = 1)."""
    lo = 1e-5
    if raio_espectral(matriz_malha(p, Kp, Ki, lo, metodo, atraso)) >= 1:
        return 0.0
    hi = lo
    while True:
        hi *= 1.05
        if hi > 50 * p.taus()[1]:
            return math.inf
        if raio_espectral(matriz_malha(p, Kp, Ki, hi, metodo, atraso)) >= 1:
            break
        lo = hi
    for _ in range(50):
        m = (lo + hi) / 2
        if raio_espectral(matriz_malha(p, Kp, Ki, m, metodo, atraso)) >= 1:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


def margem_fase_digital(p: Planta, Kp, Ki=0.0, Ts=None, atraso=0):
    """Margem de fase [graus] do PI contínuo + atraso equivalente do digital (Ts/2 + atraso·Ts).

    Devolve (margem, w_cruzamento). Margem = inf se o ganho de malha nunca chega a 1.
    """
    Ts = Ts or p.Ts
    Td = Ts / 2 + atraso * Ts
    a, b, c0 = p.L * p.J, p.R * p.J + p.L * p.B, p.R * p.B + p.Kt * p.Ke

    def mag(w):
        g = p.Kt / math.hypot(c0 - a * w * w, b * w)
        return g * math.hypot(Kp, Ki / w)

    lo, hi = 1e-3, 1e-3
    if mag(lo) < 1:
        return math.inf, None
    while mag(hi) >= 1:
        lo = hi
        hi *= 1.5
        if hi > 1e8:
            return math.inf, None
    for _ in range(100):
        m = (lo + hi) / 2
        if mag(m) >= 1:
            lo = m
        else:
            hi = m
    w = (lo + hi) / 2
    fase = -math.atan2(Ki, Kp * w) - math.atan2(b * w, c0 - a * w * w) - w * Td
    return 180 + math.degrees(fase), w


def ganho_critico(p: Planta, Ts=None):
    """Ziegler-Nichols em malha fechada: Kp (só P, sem saturação) no limite de estabilidade.

    Devolve (Ku, Pu). Na planta contínua de 2ª ordem esse limite NÃO existe:
    ele só aparece por causa da amostragem (o digital atrasa a informação).
    """
    Ts = Ts or p.Ts
    G0 = p.ganho_estatico()
    lo, hi = 0.0, 1.0 / G0
    while raio_espectral(matriz_malha(p, hi, 0.0, Ts)) < 1:
        lo = hi
        hi *= 2
    for _ in range(60):
        m = (lo + hi) / 2
        if raio_espectral(matriz_malha(p, m, 0.0, Ts)) < 1:
            lo = m
        else:
            hi = m
    Ku = (lo + hi) / 2
    ev = np.linalg.eigvals(np.array(matriz_malha(p, Ku, 0.0, Ts)))
    z = max(ev, key=lambda q: (round(abs(q), 9), abs(np.angle(q))))
    th = abs(float(np.angle(z)))
    Pu = 2 * math.pi * Ts / th if th > 1e-9 else math.inf
    return Ku, Pu


def ziegler_nichols(Ku, Pu, tipo="PID"):
    """Receita clássica (ponto de partida, não resposta final)."""
    if tipo == "P":
        return {"Kp": 0.5 * Ku, "Ki": 0.0, "Kd": 0.0}
    if tipo == "PI":
        return {"Kp": 0.45 * Ku, "Ki": 0.54 * Ku / Pu, "Kd": 0.0}
    return {"Kp": 0.6 * Ku, "Ki": 1.2 * Ku / Pu, "Kd": 0.075 * Ku * Pu}


def discretizar_planta(p: Planta, Ts, metodo="zoh"):
    """(Ad, Bv) por 'zoh' (exato), 'tustin', 'euler_tras' ou 'euler_frente'."""
    if metodo == "zoh":
        Ad, Bv, _ = zoh(p, Ts)
        return Ad, Bv
    A = ((-p.R / p.L, -p.Ke / p.L), (p.Kt / p.J, -p.B / p.J))
    b = (1 / p.L, 0.0)
    if metodo == "euler_frente":
        Ad = ((1 + A[0][0] * Ts, A[0][1] * Ts), (A[1][0] * Ts, 1 + A[1][1] * Ts))
        return Ad, (b[0] * Ts, b[1] * Ts)
    h = Ts / 2 if metodo == "tustin" else Ts
    M = ((1 - A[0][0] * h, -A[0][1] * h), (-A[1][0] * h, 1 - A[1][1] * h))
    d = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    Mi = ((M[1][1] / d, -M[0][1] / d), (-M[1][0] / d, M[0][0] / d))
    if metodo == "euler_tras":
        Ad = Mi
    else:
        P = ((1 + A[0][0] * h, A[0][1] * h), (A[1][0] * h, 1 + A[1][1] * h))
        Ad = tuple(tuple(Mi[i][0] * P[0][j] + Mi[i][1] * P[1][j] for j in range(2)) for i in range(2))
    return Ad, _mul22(Mi, (b[0] * Ts, b[1] * Ts))


def comparar_discretizacoes(p: Planta, Ts=None, V=None, t_final=None):
    """Degrau de tensão em cada método x exato (ZOH). Desvio máximo em % do valor final."""
    Ts = Ts or p.Ts
    V = p.V_max / 2 if V is None else V
    t_final = t_final or 6 * p.taus()[1]
    n = int(round(t_final / Ts))
    trajs = {}
    for m in ("zoh", "tustin", "euler_tras", "euler_frente"):
        Ad, Bv = discretizar_planta(p, Ts, m)
        x, w = (0.0, 0.0), [0.0]
        for _ in range(n):
            a = _mul22(Ad, x)
            x = (a[0] + Bv[0] * V, a[1] + Bv[1] * V)
            w.append(x[1] if abs(x[1]) < 1e12 else math.inf)
        trajs[m] = w
    ref = trajs["zoh"]
    wf = ref[-1]
    out = {}
    for m, w in trajs.items():
        dev = max(abs(a - b) for a, b in zip(w, ref))
        out[m] = {"w_final": w[-1], "desvio_pct": 100 * dev / abs(wf) if math.isfinite(dev) else math.inf, "w": w}
    return out


def frequencia_alias(f, fs):
    """Frequência aparente de um sinal de f Hz amostrado a fs Hz."""
    return abs(f - fs * round(f / fs))


def cosim(p: Planta, Kp, Ki=0.0, Kaw=0.0, m=1, Ts=None, ref=None, carga=0.0, t_final=None, planta_fmu=None):
    """Co-simulação mestre/escravo com passo de comunicação H = m·Ts (entrada congelada, Jacobi).

    O 'FMU' da planta só recebe a tensão nos instantes de troca; o controlador só recebe a
    velocidade nos mesmos instantes e, entre eles, roda com a informação velha.
    """
    Ts = Ts or p.Ts
    pf = planta_fmu or p
    ref = p.w_op if ref is None else ref
    t_final = t_final or 10 * p.taus()[1]
    H = m * Ts
    Ad, Bv, Bt = zoh(pf, H)
    pid = PIDDiscreto(Kp, Ki, 0.0, Ts, p.V_max, Kaw)
    n = int(round(t_final / H))
    x = (0.0, 0.0)
    t_l, w_l = [], []
    for k in range(n + 1):
        t = k * H
        y = x[1]
        t_l.append(t)
        w_l.append(y)
        u = pid.step(_degraus(ref, t), y)
        for j in range(1, m):
            pid.step(_degraus(ref, t + j * Ts), y)
        T = _degraus(carga, t)
        a = _mul22(Ad, x)
        x = (a[0] + Bv[0] * u + Bt[0] * T, a[1] + Bv[1] * u + Bt[1] * T)
    return {"t": t_l, "w": w_l, "H": H, "trocas": n + 1}


def desvio_cosim(p: Planta, Kp, Ki=0.0, Kaw=0.0, m=1, ref=None, carga=0.0, t_final=None, planta_fmu=None):
    """Maior desvio (rad/s e % da referência) entre a co-simulação com H = m·Ts e a de referência (H = Ts)."""
    a = cosim(p, Kp, Ki, Kaw, 1, None, ref, carga, t_final)
    b = cosim(p, Kp, Ki, Kaw, m, None, ref, carga, t_final, planta_fmu)
    dev = 0.0
    for k, w in enumerate(b["w"]):
        j = k * m
        if j < len(a["w"]):
            dev = max(dev, abs(w - a["w"][j]))
    r = _degraus(p.w_op if ref is None else ref, t_final or 10 * p.taus()[1])
    return dev, 100 * dev / abs(r), b["trocas"]


def equivalencia_fmu(p_ref: Planta, p_fmu: Planta, V=None, t_final=None, h=None):
    """Confere um 'FMU' contra o modelo de referência: degrau de tensão, maior diferença em rad/s."""
    V = p_ref.V_max / 2 if V is None else V
    t_final = t_final or 5 * p_ref.taus()[1]
    h = h or p_ref.Ts / 5
    _, _, w_ref = p_ref.simular(V, 0.0, t_final, p_ref.dt_sugerido())
    Ad, Bv, _ = zoh(p_fmu, h)
    n = int(round(t_final / h))
    x, dif = (0.0, 0.0), 0.0
    passo = len(w_ref) - 1
    for k in range(1, n + 1):
        a = _mul22(Ad, x)
        x = (a[0] + Bv[0] * V, a[1] + Bv[1] * V)
        j = min(passo, int(round(k * h / t_final * passo)))
        dif = max(dif, abs(x[1] - w_ref[j]))
    return dif


def projeto_u02(p: Planta) -> dict:
    """Ganhos de partida da Unidade 02 para QUALQUER planta (mesma regra do jogo)."""
    G0, tm = p.ganho_estatico(), p.taus()[1]
    Kp = 2.0 / G0
    return {
        "Kp_P": 4.0 / G0,
        "Kp": Kp,
        "Ki": Kp / tm,
        "Kaw": 0.5 / p.Ts,
        "w_max": G0 * p.V_max,
    }


# ---------------------------------------------------------------------------
# 6. Linha de comando
# ---------------------------------------------------------------------------
def _fmt(x, n=4):
    return f"{x:.{n}g}"


def relatorio(p: Planta) -> str:
    A, B, C, _ = p.matrizes()
    p_r, p_l = p.polos()
    t_e, t_m = p.taus()
    i_ss, V_ss = p.regime()
    rc, ro = p.postos()
    L = []
    L.append("=" * 66)
    L.append(f" cpslab {VERSAO} | {p.nome}  [{p.codigo or p.origem}]")
    L.append("=" * 66)
    L.append(f"R={_fmt(p.R)} ohm  L={_fmt(p.L)} H  Kt={_fmt(p.Kt)}  Ke={_fmt(p.Ke)}  J={_fmt(p.J)}  B={_fmt(p.B)}")
    L.append(f"Driver: {p.V_max:g} V / {p.I_max:g} A | Ts = {1000*p.Ts:g} ms | ponto: {p.w_op:g} rad/s com {p.T_op:g} N.m")
    L.append("\n(a) MODELO  x = [i, omega]")
    L.append(f"A = [[{A[0,0]:.4g}, {A[0,1]:.4g}], [{A[1,0]:.4g}, {A[1,1]:.4g}]]   B = [{B[0,0]:.4g}, 0]")
    L.append(f"polos: {np.real(p_r):.4g} (elétrico) e {np.real(p_l):.4g} (mecânico) rad/s")
    L.append(f"tau_e = {1000*t_e:.4g} ms | tau_m = {1000*t_m:.4g} ms | separação = {np.real(p_r)/np.real(p_l):.3g}x")
    L.append(f"ganho estático = {p.ganho_estatico():.5g} rad/s por V | posto ctrb = {rc} | posto obsv = {ro}")
    L.append("\n(b) PONTO DE OPERAÇÃO")
    L.append(f"i_ss = {i_ss:.4g} A ({100*i_ss/p.I_max:.0f}% de I_max) | V_ss = {V_ss:.4g} V | folga = {p.V_max-V_ss:.4g} V ({100*(p.V_max-V_ss)/p.V_max:.1f}%)")
    L.append("\n(c) AMOSTRAGEM")
    L.append(f"amostras por tau_m = {t_m/p.Ts:.3g} | amostras por tau_e = {t_e/p.Ts:.3g}")
    L.append("\nLIMITES E ATAQUES")
    L.append(f"polo duplo limite (u(0) = V_max p/ ir a w_op) = {p.polo_limite():.4g} rad/s ({p.polo_limite()/np.real(p_l):.3g}x o polo mecânico)")
    Kp = p.kp_padrao()
    L.append(f"atraso crítico com Kp = {Kp:g} V/(rad/s): {p.atraso_critico(Kp)} amostra(s)")
    return "\n".join(L)


def _cli(argv=None):
    ap = argparse.ArgumentParser(prog="cpslab", description="Laboratório genérico de CPS (motor CC)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cenario", help="gera uma planta a partir de um código (ex.: seu RA)")
    c.add_argument("codigo"); c.add_argument("--salvar", default=None)
    r = sub.add_parser("relatorio", help="analisa um planta.json")
    r.add_argument("arquivo", nargs="?", default="planta.json")
    d = sub.add_parser("datasheet", help="converte dados de catálogo para planta.json")
    for nome, tipo in [("--nome", str), ("--R", float), ("--L_mH", float), ("--Kt_mNm_A", float), ("--J_gcm2", float),
                       ("--V", float), ("--n0_rpm", float), ("--I0_mA", float), ("--B", float), ("--I_max", float),
                       ("--Ts_ms", float), ("--w_op", float), ("--T_op", float)]:
        d.add_argument(nome, type=tipo, default=None)
    d.add_argument("--salvar", default="planta.json")
    a = ap.parse_args(argv)
    if a.cmd == "cenario":
        p = Planta.de_codigo(a.codigo)
        print(relatorio(p))
        if a.salvar:
            p.salvar(a.salvar); print(f"\nSalvo em {a.salvar}")
    elif a.cmd == "relatorio":
        print(relatorio(Planta.carregar(a.arquivo)))
    else:
        p = de_datasheet(a.nome or "Motor do datasheet", a.R, a.L_mH, a.Kt_mNm_A, a.J_gcm2, a.V, a.n0_rpm, a.I0_mA,
                         a.B, None, a.I_max, a.Ts_ms or 5.0, a.w_op, a.T_op)
        p.salvar(a.salvar); print(relatorio(p)); print(f"\nSalvo em {a.salvar}")


if __name__ == "__main__":
    _cli(sys.argv[1:])
