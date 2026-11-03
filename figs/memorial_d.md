## (d) Controle digital · Junta do cotovelo do braço colaborativo AuroraArm [Diretrizes_do_TRABALHO.pdf]
- Planta: G0 = Kt/(R·B + Kt·Ke) = 11.572 rad/s/V (cpslab: 11.572); tau_mec = 44.22 ms
- Controlador: PI discreto (Tustin), u[k] = Kp·e[k] + I[k], I[k] = I[k-1] + Ki·Ts·(e[k]+e[k-1])/2
- Ganhos: Kp = 0.2592 V/(rad/s) (Kp·G0 = 3), Ki = 11.73 V/rad (Ti = 22.11 ms)
- Saturação: |u| <= 48 V; anti-windup por back-calculation, I += Kaw·Ts·(u - v), Kaw = 250 1/s
- Sem a integral, o erro de regime seria (w_op + T·q)/(1 + Kp·G0) = 119.3 rad/s: por isso o I é necessário
- Ts = 2 ms -> 22.1 amostras por tau_mec (regra: 10 a 20) | Ts crítico = 33 ms
- Margem de fase (atraso Ts/2): 64.7 graus em wc = 75.29 rad/s -> ATENDE (>= 45)
- Perdendo 1 ciclo (jitter): 56.1 graus -> ATENDE (>= 30 e estável)
- Ensaio com carga 0.25 N·m: erro final 0.000 % (ATENDE), sobressinal 0.51 % (ATENDE),
  acomodação 80 ms, ciclos saturados 24 (no fim: 0)
- Co-simulação com H = 2·Ts: desvio 0.936 % do alvo
