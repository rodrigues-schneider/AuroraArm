"""Adapta o motor didático U04 para a planta e os limites do AuroraArm.

O u04lab.py oficial mantém o NexaBot como configuração padrão. Este helper atualiza
essa configuração em memória, por processo, a partir de controlador.json, sem alterar
o arquivo oficial nem o seu SHA-256.
"""


def configurar_planta(lab, cenario):
    """Aplica os parâmetros AuroraArm ao modelo de planta padrão do u04lab."""
    chaves = ("R", "L", "Kt", "Ke", "J", "B", "V_max", "I_max", "w_op", "T_op")
    faltantes = [k for k in chaves if k not in cenario]
    if faltantes:
        raise ValueError("controlador.json sem parâmetros AuroraArm: " + ", ".join(faltantes))

    lab.NEXABOT.update({k: float(cenario[k]) for k in chaves})
    lab.NEXABOT["Ts"] = float(cenario.get("Ts", cenario["Ts_ms"] / 1000.0))
    lab.NEXABOT["nome"] = cenario.get("nome", "AuroraArm")
