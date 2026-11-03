# AuroraArm — pacote da parte prática

Este repositório reúne o modelo, o controlador e as evidências práticas preparados para a junta do cotovelo do braço colaborativo AuroraArm. A organização acompanha as etapas das Unidades 1 a 4. Os arquivos foram escritos para que outra pessoa consiga entender o que foi feito e repetir os cálculos principais.

## O que o pacote contém

- `AuroraArm.json`: parâmetros físicos e limites informados no desafio.
- `cpslab.py`: modelo da planta e rotinas de simulação e controle das Unidades 1 e 2. **Planta** é o nome usado em controle para o sistema físico que recebe comandos e produz uma resposta.
- `controlador.json`: ganhos e limites do controlador PI discreto.
- `u03lab.py` e `planta_u03.json`: supervisor de segurança e cenário temporizado. **Supervisor** é a lógica que autoriza, interrompe ou permite retomar o movimento.
- `u04lab.py` e `pratica/u04_aurora.py`: rotinas de geração de código e adaptação dos dados AuroraArm às práticas da Unidade 4.
- `pratica/`: scripts das atividades, numerados P1 a P33.
- `figs/`: gráficos, código C gerado, assinatura, varredura de prazo e memoriais calculados.
- `docs/registro_execucoes.md`: comandos executados e resumo dos resultados.
- `docs/matriz_rastreabilidade.md`: relação entre os oito requisitos, os modelos, o código e os testes, com as lacunas identificadas.
- `resultados/execucoes/`: saída integral de cada rotina executada.

## Dados e modelo

O modelo representa o motor de corrente contínua da junta. As variáveis de estado são a corrente na armadura e a velocidade angular do motor. **Variável de estado** é uma grandeza que resume a condição atual do sistema e permite calcular como ela evoluirá. O modelo usa as leis de Kirchhoff para a parte elétrica e a segunda lei de Newton para a rotação.

Os parâmetros principais são resistência de 0,8 Ω, indutância de 1,2 mH, constantes de torque e força contraeletromotriz de 0,085, inércia equivalente de 0,00042 kg·m² e atrito viscoso de 0,00015 N·m·s/rad. Os limites são 48 V e 8 A; o período de controle é 2 ms. O ponto nominal informado é 450 rad/s, com torque de carga refletido de 0,25 N·m. A transmissão harmônica 100:1 é descrita no desafio; o modelo escalar não calcula a posição ou a velocidade linear da ponta do braço.

As matrizes de espaço de estados são calculadas a partir desses parâmetros pelo `cpslab.py` e podem ser conferidas com `pratica/p3_espaco_estados.py` e `pratica/p9_memorial.py`. **Espaço de estados** é uma forma de escrever as equações do sistema como matrizes que relacionam estado, comando, perturbação e saída.

## Controlador

Foi usado um PI digital, isto é, um controlador proporcional-integral executado em intervalos regulares de 2 ms. A ação proporcional responde ao erro atual; a integral acumula erros anteriores e remove erro constante. A saída é limitada à faixa de tensão do acionamento e o mecanismo **anti-windup** por retrocálculo reduz o acúmulo indevido da integral quando essa limitação é atingida.

Os ganhos registrados em `controlador.json` são Kp = 0,2592, Ki = 11,73 e Kaw = 250. Os scripts P10 a P17 comparam malha aberta, P e PI, avaliam saturação, amostragem e atrasos. A saída C é gerada pela rotina P26 a partir da configuração, em vez de ser transcrita manualmente; P28 compila o código e compara sua resposta com o modelo em teste **SIL** (software-in-the-loop, ou teste do código em um computador junto ao modelo).

## Verificação e resultados

A Unidade 3 explora o supervisor e suas combinações de estados e eventos. **Verificação formal** é a checagem sistemática de propriedades do modelo, em vez de verificar apenas alguns exemplos escolhidos. Foram verificados o prazo de parada (propriedade de segurança com prazo) e o retorno do movimento após remoção do obstáculo e rearme (propriedade de vivacidade, isto é, algo esperado deve eventualmente ocorrer). A versão preliminar com erro de prioridade produz um contraexemplo; o relatório explica a sequência que leva à violação.

A suíte derivada do grafo visita todos os estados, mas cobre somente parte das transições. O número e o critério estão registrados nos logs P19 a P24. O memorial U03 contém a varredura dos atrasos e a fronteira em que o prazo deixa de ser cumprido.

Os resultados numéricos detalhados, premissas e comandos estão nos documentos de `docs/` e nos logs. As conclusões valem para os modelos e hipóteses descritos. A parada instantânea do supervisor não representa a desaceleração física do motor; o HIL existente é uma simulação no computador, não um ensaio em hardware real. O SIL disponível foi comparado em precisão `double` (64 bits), enquanto o microcontrolador indicado no desafio usa ponto flutuante `float32` (32 bits). Essa equivalência ainda precisa ser demonstrada no formato e no alvo finais.

A matriz também registra duas lacunas de implementação: o código C gerado não possui marcadores de requisito que permitam ligar cada linha de requisito ao código automaticamente; e o modelo atual não calcula a velocidade linear do efetuador necessária para comprovar o limite de 250 mm/s. Não se interpreta ausência de falha nos ensaios como comprovação dessas partes.

## Como repetir as rotinas

É necessário Python 3.12 ou superior e as dependências descritas em `pyproject.toml`. Com `uv` instalado, prepare o ambiente na raiz deste repositório:

```bash
uv sync
```

Execute as práticas com os dados AuroraArm:

```bash
bash executar_rotinas.sh
```

O script salva a saída de cada execução em `resultados/execucoes/`. Também é possível executar uma rotina individual, por exemplo:

```bash
uv run python pratica/p3_espaco_estados.py AuroraArm.json
uv run python pratica/p22_timed.py planta_u03.json
uv run python pratica/p28_sil_compilar.py controlador.json
```

Para compilar o SIL, é necessário um compilador C disponível no sistema. A rotina P28 informa se encontrou o compilador e registra o método usado. A geração e co-simulação FMU são complementares ao conjunto mínimo.

## Limites e uso

Este material é um pacote acadêmico de modelagem e evidências. Ele não é uma certificação de segurança funcional nem substitui ensaios do braço físico, validação do acionamento, medição de latência no microcontrolador ou avaliação independente. Consulte `docs/matriz_rastreabilidade.md` antes de interpretar um requisito como integralmente demonstrado.
