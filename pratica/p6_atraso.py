"""P6 | Tempo também é física: atraso (DoS/jitter) na leitura do sensor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cpslab import Planta

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
Kp = p.kp_padrao()  # TODO 5: teste 2*Kp e Kp/2
print(f"Kp = {Kp:g} V/(rad/s) | Ts = {1000 * p.Ts:g} ms")
for d in range(0, 9):
    r = p.raio_com_atraso(Kp, d)
    print(
        f"atraso {d} amostra(s) = {d * 1000 * p.Ts:5.0f} ms | raio {r:6.3f} | {'estável' if r < 1 else 'INSTÁVEL'}"
    )
