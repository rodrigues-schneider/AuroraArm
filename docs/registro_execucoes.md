# Caderno de resultados — AuroraArm

Use este arquivo para registrar resultados reproduzíveis do projeto. Ao acrescentar uma análise, anote a data, o comando ou método usado, os dados de entrada e as conclusões.

## Planta e fonte dos dados

- **Sistema:** junta do cotovelo do braço colaborativo AuroraArm
- **Fonte:** `Model Based Design for Cyber - Physical Systems/Diretrizes_do_TRABALHO.pdf` e imagens em `Model Based Design for Cyber - Physical Systems/imagens/`
- **Arquivo de parâmetros:** `AuroraArm.json`
- **Ferramenta:** `cpslab.py` versão 2.1
- **Data do primeiro registro:** 2026-11-02
- **Comando:** `.venv/bin/python cpslab.py relatorio AuroraArm.json`

### Parâmetros usados

| Parâmetro | Valor | Unidade |
|---|---:|---|
| Resistência de armadura, R | 0,8 | Ω |
| Indutância de armadura, L | 0,0012 | H |
| Constante de torque, Kt | 0,085 | N·m/A |
| Constante de f.c.e.m., Ke | 0,085 | V·s/rad |
| Inércia refletida, J | 0,00042 | kg·m² |
| Atrito viscoso, B | 0,00015 | N·m·s/rad |
| Tensão máxima, V_max | 48 | V |
| Corrente máxima, I_max | 8 | A |
| Período de amostragem, Ts | 0,002 | s |
| Velocidade no ponto de operação, w_op | 450 | rad/s |
| Torque de carga, T_op | 0,25 | N·m |

## Resultados registrados

### Modelo e propriedades

Estados adotados: corrente de armadura e velocidade angular, `x = [i, ω]`.

```text
A = [[-666,7, -70,83],
     [ 202,4,  -0,3571]]
B = [[833,3], [0]]
C = [[0, 1]]
D = [[0]]
```

- **Polo elétrico:** −644,4 rad/s
- **Polo mecânico:** −22,62 rad/s
- **Constante de tempo elétrica:** 1,552 ms
- **Constante de tempo mecânica:** 44,22 ms
- **Separação entre escalas de tempo:** 28,5×
- **Ganho estático:** 11,572 rad/s por V
- **Posto da matriz de controlabilidade:** 2 — sistema controlável
- **Posto da matriz de observabilidade:** 2 — sistema observável para saída de velocidade

### Ponto de operação

- **Corrente em regime:** 3,735 A (aprox. 47% de `I_max`)
- **Tensão em regime:** 41,24 V
- **Folga de tensão:** 6,762 V (14,1% de `V_max`)

### Amostragem

- **Amostras por constante de tempo mecânica:** 22,1
- **Amostras por constante de tempo elétrica:** 0,776
- **Período:** 2 ms (500 Hz)

### Limite de atuação e atraso

- **Polo duplo limite estimado:** −134,1 rad/s (5,93× o polo mecânico)
- **Ganho proporcional padrão da análise:** 0,7642 V/(rad/s)
- **Atraso crítico calculado:** 4 amostras

## Próximas análises

Preencha cada seção conforme os resultados forem obtidos. Inclua gráficos, caminhos de arquivos e referências a scripts quando aplicável.

### Identificação e validação do modelo

- **Data e método:** _pendente_
- **Dados/ensaio usados:** _pendente_
- **Parâmetros identificados:** _pendente_
- **Métrica de validação e resultado:** _pendente_
- **Conclusão:** _pendente_

### Projeto e sintonia do controlador

- **Estrutura escolhida (PID discreto ou realimentação de estados):** _pendente_
- **Ganhos e método de sintonia:** _pendente_
- **Desempenho (erro estacionário, sobressinal, acomodação):** _pendente_
- **Saturação e anti-windup:** _pendente_
- **Scripts/gráficos:** _pendente_

### Verificação formal de segurança e vivacidade

- **Propriedades formalizadas:** _pendente_
- **Modelo/verificador e hipóteses:** _pendente_
- **Atrasos e jitter considerados:** _pendente_
- **Resultado para o prazo de 100 ms:** _pendente_
- **Contraexemplo ou justificativa de ausência:** _pendente_

### Testes e cobertura

- **Testes gerados a partir do modelo:** _pendente_
- **Estados cobertos:** _pendente_
- **Transições cobertas:** _pendente_
- **Comando e relatório:** _pendente_

### Geração de código e equivalência SIL

- **Modelo/ferramenta de geração:** _pendente_
- **Arquivos C gerados:** _pendente_
- **Sequência de teste:** _pendente_
- **Erro máximo absoluto modelo–código:** _pendente_
- **Tipo numérico e épsilon de máquina:** _pendente_
- **Conclusão:** _pendente_

### Rastreabilidade

- **Matriz requisito → modelo → código → teste:** _pendente_
- **Localização da matriz:** _pendente_
- **Requisitos cobertos:** _pendente_

## Prática Guiada U01 — execução com AuroraArm

- **Data:** 2026-11-02
- **Planta usada:** `AuroraArm.json`
- **Scripts:** `pratica/p1_degrau.py` a `pratica/p9_memorial.py`
- **Ambiente:** `.venv` Python 3.12.15; as execuções foram feitas em diretório temporário para preservar figuras já existentes.
- **P9:** os TODOs genéricos de cálculo foram preenchidos em `pratica/p9_memorial.py` e o script foi executado com a planta AuroraArm.

### P1 — degrau de tensão

- **24 V (metade de V_max):** velocidade final simulada 277,03 rad/s; previsão estática 277,74 rad/s; pico de corrente 27,52 A; tempo até 63,2%: 45,6 ms.
- **48 V (V_max):** velocidade final simulada 554,05 rad/s; pico de corrente 55,03 A.
- **Interpretação:** os picos excedem 8 A porque o modelo de planta não limita a tensão nem a corrente. A saturação e a proteção do driver precisam estar no modelo/controlador/supervisor.
- **Figura:** `figs/AuroraArm_U01_p1_degrau_48V.png` (degrau de 48 V).

### P2 — malha aberta, carga e ataque

- **Comando calculado sem carga:** 38,885 V para referência de 450 rad/s.
- **Carga nominal de 0,25 N·m:** 422,77 rad/s em regime, queda de 6,1%.
- **Carga nominal mais redução de 10% do comando:** 377,77 rad/s, queda de 16,1%.
- **Variação de carga no comando fixo calculado sem carga:**

| Carga | Velocidade sem ataque | Velocidade com redução de comando de 10% |
|---:|---:|---:|
| 0,125 N·m (0,5×) | 436,39 rad/s | 391,39 rad/s |
| 0,250 N·m (1×) | 422,77 rad/s | 377,77 rad/s |
| 0,500 N·m (2×) | 395,54 rad/s | 350,54 rad/s |

- **Interpretação:** a queda de velocidade provocada pela carga é proporcional ao torque no modelo linear; em malha aberta, a planta não corrige o erro.
- **Figura:** `figs/AuroraArm_U01_p2_malha_aberta.png`.

### P3 — equações e espaço de estados

- **Elemento A[1,0]:** 202,381 s⁻¹.
- **Conferência SymPy × `cpslab`:** diferença máxima 0.

### P4 — identificação e validação retida

| Fator aplicado aos dados de ajuste | Kt identificado (N·m/A) | Fit no ajuste | Fit retido | Veredito (>90%) |
|---:|---:|---:|---:|---|
| 1,00 | 0,084989 | 99,76% | 99,76% | Aprovado |
| 1,02 | 0,083322 | 99,77% | 92,93% | Aprovado |
| 1,15 | 0,073900 | 99,79% | 46,97% | Reprovado |
| 1,30 | 0,065376 | 99,82% | −6,06% | Reprovado |

- **Interpretação:** ajuste muito bom não garante generalização; o conjunto retido detecta a adulteração dos dados. O limiar de 90% é o critério didático do script.

### P5 — polos, Bode e margens

- **Função de transferência velocidade/tensão:** `168700 / (s² + 667 s + 14570)` (valores arredondados pelo programa).
- **Polos e constantes de tempo:** −644,409 rad/s e −22,615 rad/s; 1,552 ms e 44,218 ms.
- **Separação:** 28,5×; **margem de fase:** 74,6° em 243,7 rad/s; **margem de ganho:** infinita.

### P6 — atraso no laço

- Com `Kp = 0,7642 V/(rad/s)`: raios espectrais para 0, 1, 2, 3 e 4 amostras são 0,612; 0,817; 0,934; 0,992; 1,022. Primeiro atraso instável: 4 amostras = 8 ms.
- Com `Kp/2 = 0,3821`: primeiro atraso instável em 9 amostras = 18 ms.
- Com `2 Kp = 1,528`: primeiro atraso instável em 2 amostras = 4 ms.
- **Interpretação:** o ganho mais agressivo reduz a tolerância ao atraso.

### P7 — controlabilidade, observabilidade e limite do driver

- Postos: controlabilidade 2/2; observabilidade (saída velocidade) 2/2.
- Com `Kt = 0`: postos caem para 1/2 e 1/2, pois a entrada deixa de gerar torque e a corrente deixa de influenciar a velocidade observada.
- Polo duplo limite pela tensão inicial de 48 V: **−134,125 rad/s**.
- A busca em múltiplos inteiros do polo mecânico mostra que 5× (−113,08 rad/s) pede 34,12 V e 6× (−135,69 rad/s) pede 49,13 V, cruzando o limite entre esses valores.

### P8 — replay e observador

- Limiar de alarme: 0,80 A; mudança de tensão em 6τ_m = 265,3 ms.
- Ataque em 1τ_m = 44,2 ms: alarme em 45,3 ms (resíduo 0,863 A).
- Ataque em 4τ_m = 176,9 ms (caso-base): alarme em 267,8 ms, após a mudança de tensão (resíduo 0,801 A).
- Ataque em 9τ_m = 398,0 ms: nenhum alarme no horizonte simulado de 12τ_m.
- **Interpretação:** replay após acomodação pode passar despercebido sem excitação/variação observável. A execução de 4τ_m acusa quando a mudança posterior de entrada cria discrepância.

### P9 — memorial genérico

O script `pratica/p9_memorial.py` agora calcula A, autovalores e constantes de tempo, corrente e tensão de regime e amostras por τ_m. Os resultados conferem com o relatório inicial: `i_ss = 3,735 A`, `V_ss = 41,24 V`, folga de 6,762 V e 22,1 amostras por τ_m.

## Preparação U02 — verificação do ambiente

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U02_ModelBasedDesign_PreparacaoAmbiente.html`
- **Verificador executado:** `.venv/bin/python verificar_ambiente_u02.py`
- **Resultado:** `LABORATÓRIO PRONTO PARA A U02!`; todos os itens obrigatórios do fiscal passaram.
- **Python:** 3.12.15 em `.venv`; numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2 e control 0.10.2.
- **cpslab.py:** versão 2.1; SHA-256 `08fc68e4edfbaf38baf547a019385bdfebcb8218f42932ea4c6ac90b3d174734`, igual ao hash do roteiro.
- **API U02:** `PIDDiscreto`, `malha`, `metricas`, `ts_critico`, `margem_fase_digital`, `ganho_critico`, `ziegler_nichols`, `comparar_discretizacoes`, `cosim` e `equivalencia_fmu` presentes.
- **Reprodução das referências do fiscal:** sobressinal PI 28,50%; windup 45,4%; `Ku = 3,6911 V/(rad/s)`, `Pu = 18,32 ms`; `Ts` crítico 31,66 ms.
- **Scripts U02 encontrados:** `pratica/p10_malha_fechada.py` até `pratica/p17_memorial_d.py`.
- **Bônus FMU:** `fmpy 0.3.32` e `pythonfmu 0.7.0` instalados. O script mencionado para gerar a FMU (`p16b_fmu_bonus.py`) não foi encontrado, então a geração/co-simulação do bônus não foi verificada.
- **Trilha navegador:** o arquivo `U02_ModelBasedDesign_JogoSalaControle.html`, citado pelo roteiro, não foi encontrado na pasta `PraticaGuiada`; esse teste ficou pendente.
- **Commit do roteiro:** não realizado; a verificação não exigiu alterações ao `cpslab.py` ou ao verificador.

## Prática Guiada U02 — execução com AuroraArm

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U02_ModelBasedDesign_PraticaGuiada_v2.html`
- **Planta:** `AuroraArm.json`; Parte B, scripts `pratica/p10_malha_fechada.py` a `pratica/p17_memorial_d.py`.
- **Parte A (jogo no navegador):** não executada; o arquivo `U02_ModelBasedDesign_JogoSalaControle.html` citado no roteiro não está no workspace.
- **P17:** completei as fórmulas genéricas d1–d6 e gerei `figs/memorial_d.md` com os ganhos sugeridos.

### P10–P11 — malha aberta, P e PI

- Para `Kp_P = 4/G0 = 0,3456`, erro após a entrada da carga nominal: **21,210%**. A malha aberta termina em **422,93 rad/s**, erro **6,015%**.
- PI (`Kp = 0,1728`, `Ki = 7,817`, `Kaw = 250 1/s`): velocidade final **449,99 rad/s**, erro **0,002%**, sobressinal **1,89%**.
- Dobrando a carga para 0,50 N·m, o erro P aumenta para **22,42%**; dobrando `Kp_P`, cai para **11,78%**. Com carga dobrada e `Kp_P` dobrado, erro **12,46%**. O PI manteve erro abaixo de **0,004%** nesses ensaios.
- Para `Kp·G0 = 32`, erro teórico e simulado coincidiram em **14,461 rad/s**.
- **Figura:** `figs/AuroraArm_U02_p10_malha_fechada.png`.

### P12–P13 — windup e Ziegler–Nichols

- Menor valor da tabela que atende sobressinal ≤5%: **`Kaw·Ts = 0,25`** (sobressinal 3,66%). Em 0,1, o sobressinal é 14,62%; sem anti-windup, 44,42%.
- Ganho crítico: `Ku = 5,071 V/(rad/s)`; período crítico `Pu = 8,23 ms` (4,12 amostras).
- ZN PID: `Kp = 3,043`, `Ki = 739,4`, `Kd = 0,00313`; sobressinal simulado 0,78% com anti-windup.
- No termo derivativo com ruído, desvio-padrão: **2,127 V** para `Tf = Ts/2`, **0,9421 V** para `Tf = 2Ts` e **0,4376 V** para `Tf = 5Ts`.
- **Figura:** `figs/AuroraArm_U02_p12_windup.png`.

### P14–P15 — amostragem e discretização

- Com o controlador de teste P14, no `Ts = 2 ms` da planta: **22,1 amostras/τ_m**, margem de fase **70,73°**, estável.
- `Ts` crítico dessa sintonia P14: **17,55 ms**. O período da planta cumpre a margem requerida no roteiro.
- Em `Ts = 2 ms`, desvios máximos frente ao ZOH: Tustin **0,216%**, Euler para trás **0,848%**, Euler para frente **1,953%**.
- Euler para frente tem limite teórico de estabilidade **3,104 ms**. Em `3τ_e = 4,6554 ms`, divergiu; Tustin teve desvio 0,902% e Euler para trás 1,928%.
- Aliasing com `fs = 500 Hz`: 450 Hz aparece como 50 Hz; 575 Hz como 75 Hz; 1200 Hz como 200 Hz.

### P16 e bônus P16b — co-simulação/FMI

- Na co-simulação digital, o maior `m` da lista testada com desvio <2% é **3** (`H = 6 ms`, desvio 1,368%). Em `m = 4` (`H = 8 ms`), o desvio é 2,102%.
- Comparação de modelo: FMU íntegra teve diferença máxima **0,2077 rad/s** no ensaio de equivalência simples do P16; uma variante com `Kt` e `Ke` +6% deu **14,28 rad/s**.
- Gerei e co-simulei uma FMU FMI 2.0 real usando `fmpy` e `pythonfmu`. Com `H = Ts`, `2Ts` e `4Ts`, as diferenças máximas FMU–`cpslab` foram, respectivamente, **3,12×10⁻⁷**, **1,72×10⁻⁷** e **2,61×10⁻⁸ rad/s**; as três foram classificadas como equivalentes.
- Hash SHA-256 do arquivo FMU gerado no workspace: `3df8bc735485a9308f67e2b54f53737e033c847ea3b65745b894c8b9007d1424` (registrado em `PlantaNovaTech.fmu.sha256`). Uma cópia temporária alterada em 1 byte foi rejeitada pelo verificador de integridade.
- Arquivos da FMU e scripts: `PlantaNovaTech.fmu`, `PlantaNovaTech.fmu.sha256`, `pratica/planta_fmu.py`, `pratica/p16b_fmu_bonus.py` e `pratica/planta_params.py`.

### P17 — memorial preliminar do controle digital

- Ganhos sugeridos: `Kp = 3/G0 = 0,2592 V/(rad/s)`, `Ki = 11,73 V/rad`, `Kaw = 250 1/s`; `Ts = 2 ms`.
- Margem de fase com atraso de amostragem: **64,7°**; perdendo um ciclo de 2 ms: **56,1°**, estável segundo o modelo do exercício.
- Com carga nominal: erro final **0,000%**, sobressinal **0,51%**, acomodação **80 ms**, nenhuma saturação ao final.
- Co-simulação em `H = 2Ts`: desvio **0,936%** do alvo.
- **Memorial gerado:** `figs/memorial_d.md`. Ele é um rascunho técnico da U02; formalização de segurança e restrições ISO ainda pertencem às etapas seguintes do trabalho.

## Preparação U03 — verificação do ambiente

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U03_ModelBasedDesign_PreparacaoAmbiente.html`
- **Verificador:** `.venv/bin/python verificar_ambiente_u03.py` — todos os itens passaram; resultado `LABORATÓRIO PRONTO PARA A U03!`.
- **Python/Hypothesis:** Python 3.12.15 no `.venv`; Hypothesis 6.170.14.
- **Integridade do motor formal:** SHA-256 de `u03lab.py` = `d9bfe5b2a3e997f16eedb61a3215e64443d3b5285d4de2762bd4337a50782c96`, igual ao roteiro.
- **Resultados canônicos:** 6 estados, 768 transições, 25 arestas; 0 violações no supervisor correto; 8 violações com o bug de prioridade; contraexemplo mínimo de 2 passos; suíte mínima com 5 testes, cobertura de 100% dos estados e 20% das arestas.
- **Scripts encontrados:** `pratica/p18_requisitos.py` a `pratica/p25_memorial_d.py`.
- **Cenário adaptado:** `planta_u03.json` agora usa os dados do desafio AuroraArm, sem gerar cenário pelo RA: `Ts = 2 ms`, atraso de sensor de `20 ms` (10 períodos), 1 ciclo perdido por jitter e prazo de `100 ms`. `n_zonas = 0` representa que o enunciado não especifica zonas de segurança independentes.
- **Verificação temporizada:** o autômato explorou 22 caminhos; pior caso de detecção e atuação = **13 períodos / 26 ms**, com **74 ms de folga** para o prazo. Na varredura, atraso máximo de 47 períodos resulta em 100 ms (cumpre); 48 períodos resulta em 102 ms (viola).
- **Limite da evidência:** esse resultado assume a abstração do watchdog, que representa a atuação bem-sucedida como torque zerado. Não modela a dinâmica física de decaimento do torque do motor/atuador; essa parte precisa ser verificada no modelo da planta e na validação SIL/HIL.
- **Resultado do supervisor:** supervisor correto, 0 violações; bug de prioridade, 8 violações (mesmos resultados canônicos do motor formal).
- **Trilha navegador:** `U03_ModelBasedDesign_JogoCacaAoContraexemplo.html` não foi encontrado no workspace; o teste interativo não foi executado.
- **Commit do roteiro:** não feito; foi preservado o estado de trabalho e não houve pedido explícito para criar commit.

## Prática Guiada U03 — execução com dados do AuroraArm

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U03_ModelBasedDesign_PraticaGuiada.html`
- **Dados temporais:** `planta_u03.json`, agora adaptado ao caso AuroraArm (`Ts=2 ms`, sensor até `20 ms`, 1 ciclo perdido, prazo `100 ms`). Os parâmetros elétricos do motor não entram no supervisor discreto U03; a dinâmica física do torque continua fora desta abstração.
- **Scripts executados:** `pratica/p18_requisitos.py` a `pratica/p25_memorial_d.py`.
- **P18 — formalização:** REQ-SAFE-007, limite contínuo de velocidade linear do efetuador, permanece fora do modelo discreto e precisa de modelo contínuo/planta + controlador.
- **P19 — model checking:** 6 estados, 768 transições e 25 arestas; REQ-SAFE-001 e REQ-SAFE-002 satisfeitos (0 violações cada).
- **P20 — contraexemplo:** versão com bug tem 8 violações. Caminho mínimo: `OCIOSO --{partir}--> MOVENDO --{partir, obstaculo}--> MOVENDO`; a última transição deixa torque habilitado com obstáculo.
- **P21 — vivacidade:** REQ-SAFE-005 satisfeito no modelo correto. Mutante `sem_rearme` viola vivacidade e prende o supervisor em `FALHA`, embora o invariante de segurança continue sem violações.
- **P22/P25 — watchdog:** 22 caminhos não determinísticos; pior caso **13 períodos = 26 ms**, folga **74 ms**. Fronteira exata: `atraso_max=47` dá 100 ms (cumpre); `48` dá 102 ms (viola). O P25 completado conferiu período, pior caso e fronteira contra o motor `u03lab`.
- **P23 — cobertura:** suíte mínima de 5 testes cobre 100% dos estados, mas apenas 20% das 25 arestas.
- **P24 — Hypothesis:** 2.000 sequências no supervisor correto sem violação; no mutante, 22 sequências falhas encontradas e sequência mínima de 2 passos, igual à BFS.
- **Artefatos:** [memorial_d_u03.md](figs/memorial_d_u03.md) e [varredura_u03.txt](figs/varredura_u03.txt).
- **Limite da evidência temporal:** o autômato abstrai a atuação bem-sucedida como torque zerado; não modela o decaimento físico do torque. O atraso de parada física precisa ser composto com a dinâmica da junta e validado em SIL/HIL.
- **Parte A (jogo no navegador):** não executada; `U03_ModelBasedDesign_JogoCacaAoContraexemplo.html` não está no workspace.

## Preparação U04 — ambiente e configuração AuroraArm

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U04_ModelBasedDesign_PreparacaoAmbiente.html`
- **Fiscal:** `.venv/bin/python verificar_ambiente_u04.py` — todos os itens passaram; resultado `LABORATÓRIO PRONTO PARA A U04!`.
- **Integridade:** SHA-256 do `u04lab.py` = `6c063393d160bb0f43246c06499fdae77b7ec1b49ea3d252009cb7b4650eaed9`, igual ao roteiro.
- **Ambiente:** Python 3.12.15; compilador C disponível em `/usr/bin/cc`; SIL real pode ser compilado.
- **Arquivos U04:** `pratica/p26_gerar_codigo.py` a `pratica/p33_rastreabilidade.py` presentes.
- **Configuração:** substituí o cenário anterior por `controlador.json` adaptado ao AuroraArm: `Ts=2 ms`, referência `450 rad/s`, PI U02 (`Kp=0,2592`, `Ki=11,73`, `Kaw=250`), limites de 48 V/8 A, atraso de sensor 20 ms, um ciclo perdido e prazo 100 ms. O orçamento temporal herda 13 períodos da U03.
- **Formato fixo:** Q16.16 fica como comparação didática; o firmware do caso é especificado com ponto flutuante de 32 bits.
- **Limite do motor U04 oficial:** `ctrl_de_cenario` e `malha_hil` usam NexaBot (inclusive saturação de 24 V) como planta padrão. Embora `controlador.json` registre os dados da junta, as práticas SIL/HIL padrão ainda precisam de adaptação específica para que os resultados representem AuroraArm. Mantive `u04lab.py` intacto para preservar o hash oficial.
- **Trilha navegador:** `U04_ModelBasedDesign_JogoOperacaoEvidencia.html` não foi encontrado no workspace; o painel interativo não foi executado.
- **Commit:** não criado.

## Prática Guiada U04 — execução com AuroraArm

- **Data:** 2026-11-02
- **Roteiro:** `PraticaGuiada/U04_ModelBasedDesign_PraticaGuiada.html`
- **Dados:** `controlador.json`; adaptação de processo por `pratica/u04_aurora.py` atualiza em memória os parâmetros padrão do `u04lab` para R, L, Kt, Ke, J, B, limites, ponto de operação e período AuroraArm. O `u04lab.py` oficial permanece inalterado e com hash válido.
- **Scripts executados:** P26–P33.

### P26–P29 — geração, formato numérico e SIL

- **P26:** C gerado com `Kp=0,2592`, `Ki=11,73`, `Kaw=250`, saturação de 48 V e contrato de `Ts=2 ms`. Assinatura SHA-256 do controlador: `13c498799ed6a3ada5d4d72e75364ed32d507b9cfc9dd436d4881e3cf2c85815`; duas gerações repetiram a assinatura. Alterar Kp para 0,260 mudou 60 dos 64 caracteres.
- **Artefatos:** `figs/AuroraArm_pid_gen.c` e `figs/AuroraArm_pid_gen.h`.
- **P27:** formato comparativo Q16.16 (32 bits), degrau `1,526×10⁻⁵`, faixa `[-32768, 32768]`. Após 2000 ciclos, erro acumulado float–Q de `0,01412` (925,1 degraus). Incremento de 0,000020 rad/s por ciclo arredonda a zero. Q16.16 é análise didática; o alvo especificado é float32.
- **P28:** C compilado com `/usr/bin/cc -O2`; modelo double × código double, erro máximo **0 V** (0 épsilons, εdouble=`2,220×10⁻¹⁶`). Variante Q16.16: erro máximo `7,629×10⁻⁵ V` (5 degraus).
- **P29:** bug com anti-windup desligado divergiu **96 V** na amostra 800, acima do limite de 48 V; controlador correto deu erro 0 no SIL.

### P30–P32 — HIL simulado, orçamento e watchdog

- **P30:** planta AuroraArm simulada convergiu a 450 rad/s. Perfil determinístico de 400 ciclos: jitter médio `0,232 ms`; pior jitter `1,963 ms`; período máximo `3,963 ms`. Dados salvos em `figs/AuroraArm_jitter_u04.txt`.
- **P31:** 13 períodos herdados da U03: prazo nominal `26,0 ms`; pessimista, supondo todos os ciclos no pior período observado, `51,5 ms`; prazo de segurança `100 ms`, folga pessimista `48,5 ms`.
- **P32:** watchdog configurado para `2 ms` (um ciclo). Atraso de 2,6 ms produziu comando seguro (torque zero) e alvo derrubado.

### P33 — matriz e memorial item (e)

- **Busca:** 4715 arquivos examinados, 14 com marcadores REQ.
- **Matriz:** REQ-CODE-001 (1 modelo/0 código/1 teste); REQ-CODE-002 (1/0/1); REQ-SAFE-006 (3/0/3); REQ-SAFE-001 (4/0/6); REQ-CODE-003 (1/0/1).
- **Lacuna de rastreabilidade:** a coluna código ficou vazia porque o scanner exclui `figs/` e o gerador oficial não põe marcadores REQ no C. Os artefatos assinados existem, mas a ligação automática requisito→C precisa ser fechada.
- **Limitações para o AuroraArm:** o C do `u04lab` usa `double` (64 bits); o SIL comprova double, não float32. HIL é simulação no host e o jitter é determinístico, não medido no microcontrolador. O watchdog de 2 ms é escolha de projeto para detectar um ciclo perdido; deve ser validado com o supervisor e hardware reais. Tempo de execução e tamanho do binário não foram medidos.
- **Memorial:** `figs/memorial_e_u04_AuroraArm.md`.
- **Parte A (jogo no navegador):** não executada; `U04_ModelBasedDesign_JogoOperacaoEvidencia.html` não está no workspace.
- **Commit:** não criado.

## Registro de atualizações

| Data | Análise acrescentada | Arquivos relacionados |
|---|---|---|
| 2026-11-02 | Preparação do ambiente e relatório inicial da planta | `AuroraArm.json`, `cpslab.py` |
| 2026-11-02 | Prática Guiada U01 P1–P9 executada e registrada | `pratica/p9_memorial.py`, `figs/AuroraArm_U01_p1_degrau_48V.png`, `figs/AuroraArm_U01_p2_malha_aberta.png` |
| 2026-11-02 | Requisitos da preparação U02 verificados | `verificar_ambiente_u02.py`, `cpslab.py`, `pratica/p10_malha_fechada.py`–`pratica/p17_memorial_d.py` |
| 2026-11-02 | Prática U02 Parte B P10–P17 e bônus FMU executados | `figs/memorial_d.md`, `PlantaNovaTech.fmu`, `pratica/p16b_fmu_bonus.py`, `pratica/planta_fmu.py` |
| 2026-11-02 | Preparação U03 verificada e cenário temporizado adaptado ao AuroraArm | `u03lab.py`, `verificar_ambiente_u03.py`, `planta_u03.json` |
| 2026-11-02 | Prática U03 P18–P25 executada; P25 completado com dados AuroraArm | `pratica/p22_timed.py`, `pratica/p25_memorial_d.py`, `figs/memorial_d_u03.md`, `figs/varredura_u03.txt` |
| 2026-11-02 | Preparação U04 verificada e `controlador.json` adaptado ao AuroraArm | `u04lab.py`, `verificar_ambiente_u04.py`, `controlador.json` |
| 2026-11-02 | Prática U04 P26–P33 executada com adaptador AuroraArm | `pratica/u04_aurora.py`, `figs/AuroraArm_pid_gen.c`, `figs/AuroraArm_jitter_u04.txt`, `figs/memorial_e_u04_AuroraArm.md` |

## Reexecução agrupada para a pasta de entrega

Em 3 de novembro de 2026, as rotinas P1–P17, P16b (bônus FMI), P18–P25 e P26–P33 foram reexecutadas dentro desta pasta, com `AuroraArm.json`, `planta_u03.json` ou `controlador.json`, conforme a unidade. O roteiro `executar_rotinas.sh` salvou a saída completa de cada comando em `resultados/execucoes/P*.txt`. Todas as rotinas terminaram com código de saída zero nesta execução.

A execução P26 regenerou o controlador e confirmou a assinatura `13c498799ed6a3ada5d4d72e75364ed32d507b9cfc9dd436d4881e3cf2c85815`. A execução P28 compilou com `/usr/bin/cc -O2` e registrou erro máximo de 0 V no comparador double. A rotina P33 encontrou marcadores genéricos em 13 requisitos didáticos; a matriz específica do desafio está em `docs/matriz_rastreabilidade.md` e explicita o que essa análise automática ainda não vincula.
