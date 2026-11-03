# Memorial — item (e): rastreabilidade e limites da evidência

Controlador: Controlador da junta do cotovelo AuroraArm (cenário AuroraArm)

## Matriz de rastreabilidade

| REQ | modelo | código | teste | descrição |
|---|---|---|---|---|
| REQ-CODE-001 | 2 | 0 | 1 | O código embarcado é gerado a partir do modelo (artefato derivado), nunca editado à mão. |
| REQ-CODE-002 | 2 | 0 | 1 | O passo do controlador é equivalente ao modelo dentro do épsilon de máquina (SIL). |
| REQ-SAFE-006 | 4 | 0 | 3 | O torque chega a zero dentro do prazo, respeitado o jitter medido (HIL). |
| REQ-SAFE-001 | 3 | 0 | 6 | Nunca habilitar torque com obstáculo presente (supervisor, herdado da U03). |
| REQ-CODE-003 | 2 | 0 | 1 | Cada artefato gerado carrega assinatura que o liga aos parâmetros de origem. |

## O que o pipeline prova

- Modelo executável da planta identificado por ensaio (U01).
- Controlador PID projetado com período de amostragem justificado (U02).
- Requisitos formais e verificação exaustiva do supervisor (U03).
- Código C gerado do modelo, com assinatura de rastreabilidade (U04/a13).
- Comparação numérica modelo x código (SIL), erro medido em épsilons (U04/a14).
- Medição de jitter e prazo de pior caso em tempo real (HIL) (U04/a15).
- Watchdog com comando seguro demonstrado em falha do alvo (U04/a15).
- Matriz de rastreabilidade derivada do código (U04/a16).
- Análise do que o pipeline prova e do que não prova (U04/a16).

## O que o pipeline NÃO prova (limites)

- Qualificação das ferramentas segundo a DO-330.
- Cobertura estrutural MC/DC do código (houve só cobertura de transição do modelo).
- Análise estática do código-fonte segundo regras MISRA C.
- Certificação por autoridade — evidência não é certificado.
- Ensaio físico no robô real — HIL usa planta simulada.

## Aplicação ao AuroraArm — limites observados

- O cenário e o PI vieram de `controlador.json`; os parâmetros da planta e o limite de 48 V foram aplicados em memória pelo adaptador `pratica/u04_aurora.py`.
- O `u04lab` oficial gera C com tipos `double` (64 bits). O SIL executado prova equivalência desse artefato em double; não prova ainda a implementação float32 exigida pelo microcontrolador AuroraArm.
- O HIL usa a planta AuroraArm simulada no host. O jitter é um perfil determinístico de até 2 ms, não uma medição no microcontrolador real.
- A matriz exibiu 0 artefatos na coluna código: o scanner ignora `figs/` e o gerador oficial não inclui marcadores REQ no C. A presença do C assinado está comprovada em `figs/AuroraArm_pid_gen.h` e `.c`, mas a ligação automática requisito→código continua pendente.

> Evidência não é certificado: nós produzimos a evidência; quem certifica é uma
> autoridade com mandato. Um pipeline aberto bem-feito produz evidência de primeira;
> ferramenta cara não certifica nada por decreto.