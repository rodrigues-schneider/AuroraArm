/* ===========================================================================
 * ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITAR À MÃO.
 * Este é um artefato derivado: se o comportamento estiver errado, corrija o
 * MODELO e gere de novo. Edições manuais serão apagadas na próxima geração.
 * ---------------------------------------------------------------------------
 * gerador .......: u04lab 4.0
 * formato .......: float
 * ganhos ........: Kp=0.2592 Ki=11.73 Kd=0.0 Kaw=250.0 N=10.0
 * saturação .....: +/- 48.0 V
 * período (Ts) ..: 2.000 ms  <-- CONTRATO: chame pid_step() exatamente nessa cadência
 * gerado em .....: (geração determinística)
 * assinatura ....: 13c498799ed6a3ada5d4d72e75364ed32d507b9cfc9dd436d4881e3cf2c85815
 * =========================================================================== */
#ifndef PID_GEN_H
#define PID_GEN_H
typedef struct { double I, D, e_ant, y_ant; int tem_y; } pid_estado_t;
void pid_reset(pid_estado_t *st);
double pid_step(pid_estado_t *st, double ref, double y);
#endif
