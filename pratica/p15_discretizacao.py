"""P15 | Três tradutores (Euler, Tustin, ZOH) e a roda que gira ao contrário (a07)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cpslab import Planta, comparar_discretizacoes, frequencia_alias

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
tau_e, tau_m = p.taus()
lam_ele = p.polos()[0]
for Ts in (p.Ts, tau_m / 10):                      # TODO 7: teste também 3*tau_e
    d = comparar_discretizacoes(p, Ts)
    print(f"\nDegrau de V_max/2 discretizado com Ts = {1000 * Ts:.4g} ms (desvio máximo contra o ZOH exato)")
    for nome, rot in (("zoh", "ZOH (exato)"), ("tustin", "Tustin"), ("euler_tras", "Euler p/ trás"), ("euler_frente", "Euler p/ frente")):
        dv = d[nome]["desvio_pct"]
        print(f"   {rot:<16} desvio = {'EXPLODIU' if dv > 1e6 else f'{dv:.3f} %'}")
ts_lim = 2 / abs(lam_ele)
print(f"\nEuler para frente só é estável se |1 + lambda*Ts| < 1 para TODOS os polos.")
print(f"Polo elétrico = {lam_ele:.4g} rad/s -> Ts limite = 2/|lambda| = {1000 * ts_lim:.4g} ms")
fs = 1 / p.Ts
print(f"\nAliasing com fs = {fs:g} Hz (Nyquist = {fs / 2:g} Hz):")
for k in (0.3, 0.9, 1.15, 2.4):
    f = round(k * fs, 6)
    print(f"   sinal de {f:8.2f} Hz -> controlador enxerga {frequencia_alias(f, fs):8.2f} Hz")
print("Acima de fs/2 a informação já se perdeu na amostra: só um filtro ANALÓGICO antes do conversor resolve.")
