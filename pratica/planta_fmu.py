"""Planta (motor CC) empacotada como FMU de co-simulação (FMI 2.0) com pythonfmu.

Gerar a FMU (os parâmetros vêm do SEU planta.json, gravado em planta_params.py):
    uv run python pratica/p16b_fmu_bonus.py planta.json --gerar
"""
import math
from pythonfmu import Fmi2Causality, Fmi2Variability, Fmi2Slave, Real

from planta_params import P   # dicionário com R, L, Kt, Ke, J, B (gerado pelo p16b)


class PlantaNovaTech(Fmi2Slave):
    author = "NovaTech Ltda. (cenário fictício)"
    description = "Motor CC de ímã permanente: x = [i, omega]; entradas V e T_carga"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.V = 0.0
        self.T_carga = 0.0
        self.omega = 0.0
        self.i = 0.0
        self.register_variable(Real("V", causality=Fmi2Causality.input))
        self.register_variable(Real("T_carga", causality=Fmi2Causality.input))
        self.register_variable(Real("omega", causality=Fmi2Causality.output))
        self.register_variable(Real("i", causality=Fmi2Causality.output))

    def _der(self, i, w):
        return ((self.V - P["R"] * i - P["Ke"] * w) / P["L"],
                (P["Kt"] * i - P["B"] * w - self.T_carga) / P["J"])

    def do_step(self, current_time, step_size):
        # Runge-Kutta 4 com subpassos menores que a constante de tempo elétrica
        n = max(1, math.ceil(step_size / P["dt"]))
        h = step_size / n
        i, w = self.i, self.omega
        for _ in range(n):
            k1 = self._der(i, w)
            k2 = self._der(i + h / 2 * k1[0], w + h / 2 * k1[1])
            k3 = self._der(i + h / 2 * k2[0], w + h / 2 * k2[1])
            k4 = self._der(i + h * k3[0], w + h * k3[1])
            i += h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
            w += h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        self.i, self.omega = i, w
        return True
