# Memorial item (d) — Verificação do prazo de segurança

**Máquina:** Junta do cotovelo AuroraArm (cenário AuroraArm)
**Parâmetros:** Ts = 2 ms · prazo (REQ-SAFE-006 / análogo a REQ-SAFE-AA-001) = 100 ms ·
atraso_deteccao_max = 10 períodos · ciclos_perdidos = 1

## Modelo
Watchdog como autômato temporizado de relógio discreto (períodos de Ts). Pior caso =
atraso máximo de detecção (10) + 1 período de confirmação + 2 períodos de atuação
(incluindo 1 ciclo(s) perdido(s) por jitter).

## Resultado (verificação exaustiva)
- Trajetórias não determinísticas exploradas: **22**
- Pior caso: **13 períodos = 26 ms**
- Prazo: 100 ms  ->  **CUMPRIDO** (folga 74 ms)
- Fronteira exata: até atraso_max = **47** (100 ms) cumpre;
  a partir de 48 (102 ms) viola.

## Conclusão
O prazo de 100 ms deixa de ser número no papel e vira restrição de projeto sobre o
filtro do sensor: relaxar o atraso de detecção além de 47 períodos exige
reverificar o requisito. "Nunca falhou em teste" não substitui esta prova de pior caso.
