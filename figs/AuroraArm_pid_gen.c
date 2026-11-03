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
#include "pid_gen.h"

void pid_reset(pid_estado_t *st){ st->I=0; st->D=0; st->e_ant=0; st->y_ant=0; st->tem_y=0; }

double pid_step(pid_estado_t *st, double ref, double y){
    const double Kp=0.2592, Ki=11.73, Kd=0.0;
    const double Kaw=250.0, N=10.0, Ts=0.002, umax=48.0;
    double e = ref - y;
    st->I += Ki*Ts*(e + st->e_ant)/2.0;            /* integral (Tustin) */
    if (Kd>0 && st->tem_y){
        double Tf = (Kp>0)? Kd/(Kp*N) : Ts;
        double a = Tf/(Tf+Ts);
        st->D = a*st->D - (1-a)*Kd*(y - st->y_ant)/Ts;  /* derivada filtrada */
    }
    double v = Kp*e + st->I + st->D;                /* comando */
    double u = v>umax? umax : (v<-umax? -umax : v);  /* saturação */
    st->I += Kaw*Ts*(u - v);                        /* anti-windup */
    st->e_ant = e; st->y_ant = y; st->tem_y = 1;
    return u;
}
