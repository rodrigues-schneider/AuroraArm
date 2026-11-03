"""P4 | Planta sem manual: identificação, validação retida e dados envenenados."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from cpslab import Planta, gerar_ensaio, identificar, fit_percent

p = Planta.carregar(sys.argv[1] if len(sys.argv) > 1 else "planta.json")
FATOR = 1.15  # TODO 4: teste 1.00, 1.02 e 1.30
V_aj, V_val = 0.5 * p.V_max, 0.3 * p.V_max

t, i_m, w_m = gerar_ensaio(
    p, V_aj, semente=1, fator_adulteracao=FATOR
)  # arquivo "do fornecedor"
tv, iv, wv = gerar_ensaio(p, V_val, semente=7)  # ensaio retido, honesto
chute = [p.R * 1.5, p.L * 0.6, p.Kt * 1.3, p.J * 0.6, p.B * 1.5]  # palpite bem errado
est, nfev = identificar(p, t, V_aj, i_m, w_m, chute)

print(f"Fator de adulteração: {FATOR} | avaliações: {nfev}")
for nome in ["R", "L", "Kt", "J", "B"]:
    v, e = getattr(p, nome), getattr(est, nome)
    print(
        f"{nome:<3} verdadeiro {v:11.4g} | identificado {e:11.4g} | erro {100 * (e - v) / v:7.2f}%"
    )
_, _, w_aj = est.simular(V_aj, t_final=t[-1], dt=t[1] - t[0])
_, _, w_v = est.simular(V_val, t_final=tv[-1], dt=tv[1] - tv[0])
fa, fv = fit_percent(w_m, w_aj), fit_percent(wv, w_v)
print(f"fit no próprio ensaio: {fa:.2f}% | fit no ensaio RETIDO: {fv:.2f}%")
print(
    "VEREDITO:",
    "modelo aprovado" if fv > 90 else "MODELO REPROVADO - investigue os dados!",
)
