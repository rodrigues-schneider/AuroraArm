"""P16b | BÔNUS: uma FMU de verdade. Gera, confere o SHA-256 e co-simula com o fmpy (a08).

    uv add pythonfmu fmpy
    uv run python pratica/p16b_fmu_bonus.py planta.json --gerar     (1x: cria PlantaNovaTech.fmu)
    uv run python pratica/p16b_fmu_bonus.py planta.json             (co-simula e confere)
    uv run python pratica/p16b_fmu_bonus.py planta.json --classe    (se o binário der erro no seu sistema)
"""
import sys, hashlib, subprocess, zipfile
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cpslab import Planta, PIDDiscreto

arq = next((a for a in sys.argv[1:] if not a.startswith("--")), "planta.json")
p = Planta.carregar(arq)
pasta = Path(__file__).resolve().parent
fmu = Path("PlantaNovaTech.fmu")

if "--gerar" in sys.argv:
    (pasta / "planta_params.py").write_text(
        f"P = dict(R={p.R!r}, L={p.L!r}, Kt={p.Kt!r}, Ke={p.Ke!r}, J={p.J!r}, B={p.B!r}, dt={p.taus()[0] / 20!r})\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "pythonfmu", "build", "-f", str(pasta / "planta_fmu.py"), str(pasta / "planta_params.py"), "-d", "."], check=True)
    h = hashlib.sha256(fmu.read_bytes()).hexdigest()
    Path("PlantaNovaTech.fmu.sha256").write_text(h + "  PlantaNovaTech.fmu\n")
    print(f"FMU gerada: {fmu} ({fmu.stat().st_size / 1024:.0f} KB)\nSHA-256 publicado em PlantaNovaTech.fmu.sha256: {h}")
    with zipfile.ZipFile(fmu) as z:
        print("Conteúdo (é um .zip!):", ", ".join(n for n in z.namelist() if not n.endswith("/"))[:300], "...")
    sys.exit(0)

# 1) integridade: o arquivo é o mesmo que foi publicado?
pub = Path("PlantaNovaTech.fmu.sha256").read_text().split()[0]
atual = hashlib.sha256(fmu.read_bytes()).hexdigest()
print(f"SHA-256 publicado: {pub}\nSHA-256 do arquivo: {atual}\nIntegridade: {'OK' if pub == atual else 'FALHOU — NÃO USE ESTA FMU'}")
if pub != atual:
    sys.exit(1)

# 2) co-simulação: FMU (planta) x Python (controlador PI), trocando dados a cada H
G0, tau_m = p.ganho_estatico(), p.taus()[1]
H = 2 * p.Ts                                         # TODO 9: compare H = Ts e H = 4*Ts
m = int(round(H / p.Ts))
pid = PIDDiscreto(1 / G0, 1 / G0 / tau_m, 0.0, p.Ts, p.V_max, 0.5 / p.Ts)


class FMUviaFmpy:
    """Roda o binário da FMU (Windows/Linux) pelo fmpy, como qualquer ferramenta FMI faria."""
    def __init__(self):
        from fmpy import read_model_description, extract
        from fmpy.fmi2 import FMU2Slave
        md = read_model_description(str(fmu))
        self.vr = {v.name: v.valueReference for v in md.modelVariables}
        self.s = FMU2Slave(guid=md.guid, unzipDirectory=extract(str(fmu)), modelIdentifier=md.coSimulation.modelIdentifier, instanceName="planta")
        self.s.instantiate(); self.s.setupExperiment(startTime=0.0); self.s.enterInitializationMode(); self.s.exitInitializationMode()
    def passo(self, t, H, V, T):
        self.s.setReal([self.vr["V"], self.vr["T_carga"]], [V, T]); self.s.doStep(currentCommunicationPoint=t, communicationStepSize=H)
        return self.s.getReal([self.vr["omega"]])[0]
    def fim(self):
        self.s.terminate(); self.s.freeInstance()


class FMUviaClasse:
    """macOS: o pythonfmu 0.7 não traz binário para Mac. Usamos a MESMA classe que está dentro da FMU,
    chamando do_step() exatamente como o mestre FMI chamaria (modo didático)."""
    def __init__(self):
        sys.path.insert(0, str(pasta)); from planta_fmu import PlantaNovaTech
        self.s = PlantaNovaTech(instance_name="planta")
    def passo(self, t, H, V, T):
        self.s.V, self.s.T_carga = V, T; self.s.do_step(t, H); return self.s.omega
    def fim(self):
        pass


try:
    if "--classe" in sys.argv:
        raise RuntimeError("modo --classe pedido na linha de comando")
    planta = FMUviaFmpy(); modo = "fmpy + binário da FMU"
except Exception as e:
    print(f"(fmpy não conseguiu carregar o binário: {str(e)[:90]}...)\n-> usando a classe da FMU diretamente (modo didático, típico no macOS)")
    planta = FMUviaClasse(); modo = "classe da FMU (do_step)"
t, w, ws = 0.0, 0.0, []
while t < 8 * tau_m - 1e-12:
    u = pid.step(p.w_op, w)
    for _ in range(m - 1):
        pid.step(p.w_op, w)                          # entre trocas, o controlador só tem a medida velha
    w = planta.passo(t, H, u, p.T_op if t >= 4 * tau_m - 1e-12 else 0.0)
    t += H; ws.append(w)
planta.fim()
print(f"\nCo-simulação [{modo}] com H = {1000 * H:g} ms: {len(ws)} trocas, velocidade final {ws[-1]:.2f} rad/s (alvo {p.w_op:g})")

# 3) equivalência: a FMU reproduz o modelo de referência (cpslab)?
from cpslab import cosim
ref = cosim(p, 1 / G0, 1 / G0 / tau_m, 0.5 / p.Ts, m, carga=[(0, 0.0), (4 * tau_m, p.T_op)], t_final=8 * tau_m)
n = min(len(ws), len(ref["w"]) - 1)
dif = max(abs(ws[k] - ref["w"][k + 1]) for k in range(n))
print(f"Maior diferença FMU x cpslab (mesmo H): {dif:.3g} rad/s -> {'EQUIVALENTE' if dif < 0.01 * p.w_op else 'NÃO EQUIVALENTE'}")
