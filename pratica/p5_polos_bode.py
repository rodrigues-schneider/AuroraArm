"""P5 | Função de transferência, polos, constantes de tempo e Bode."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import control as ct
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
A, B, C, D = p.matrizes()
G = ct.ss2tf(ct.ss(A, B, C, D)); print(G)
pr, pl = p.polos(); te, tm = p.taus()
print(f"polo elétrico : {pr:10.3f} rad/s  tau = {1000*te:8.3f} ms")
print(f"polo mecânico : {pl:10.3f} rad/s  tau = {1000*tm:8.3f} ms   (5 tau = {5000*tm:.1f} ms)")
print(f"separação     : {pr/pl:.1f} vezes | ganho estático = {ct.dcgain(G):.4g} rad/s por V")
gm, pm, wcg, wcp = ct.margin(G)
print(f"margem de ganho: {gm} | margem de fase: {pm:.1f} graus em {wcp:.1f} rad/s")