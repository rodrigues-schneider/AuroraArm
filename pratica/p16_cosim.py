"""P16 | Co-simulação: o preço de espaçar a comunicação (H) e a conferência da FMU (a08)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from cpslab import Planta, desvio_cosim, equivalencia_fmu

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
G0, tau_m = p.ganho_estatico(), p.taus()[1]
Kp, Ki, Kaw = 1 / G0, 1 / G0 / tau_m, 0.5 / p.Ts
carga = [(0, 0.0), (4 * tau_m, p.T_op)]
print(f"Controlador a Ts = {1000 * p.Ts:g} ms | planta 'FMU' trocando dados a cada H = m*Ts")
print(f"{'m':>3}{'H [ms]':>9}{'trocas':>8}{'desvio [rad/s]':>16}{'desvio [%]':>12}{'desvio/H [%/ms]':>17}")
for m in (1, 2, 3, 4, 6, 8, 12, 16):              # TODO 8: qual o maior m com desvio < 2%?
    dev, pct, trocas = desvio_cosim(p, Kp, Ki, Kaw, m, carga=carga, t_final=8 * tau_m)
    H = 1000 * m * p.Ts
    print(f"{m:>3}{H:>9.3g}{trocas:>8}{dev:>16.3f}{pct:>12.3f}{(pct / H if m > 1 else 0):>17.4f}")
print("O erro cresce com H (quase linear enquanto H é pequeno perto de tau_mec): a planta recebe a mesma tensão do começo ao fim de cada H.")
# conferência: a FMU recebida é equivalente ao modelo de referência?
for nome, pf in (("FMU íntegra", p), ("FMU adulterada (Kt +6%)", replace(p, Kt=p.Kt * 1.06, Ke=p.Ke * 1.06))):
    print(f"{nome:<26}: maior diferença = {equivalencia_fmu(p, pf):.4g} rad/s")
print("Confiar sem conferir é o oposto do Model-Based Design: confira o hash E o comportamento.")
