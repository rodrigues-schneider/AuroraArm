#!/usr/bin/env bash
# Executa as rotinas práticas com as configurações AuroraArm e guarda cada saída.
set -u
cd "$(dirname "$0")"
mkdir -p resultados/execucoes figs
PY="${PYTHON:-uv run python}"
falhas=0
rodar() {
  nome="$1"; shift
  arquivo="resultados/execucoes/${nome}.txt"
  echo "[execução] ${nome}"
  # PY aceita um comando simples, por padrão "uv run python".
  if $PY "$@" >"$arquivo" 2>&1; then
    echo "[ok] ${nome}"
  else
    rc=$?
    echo "[falhou: ${rc}] ${nome} — consulte ${arquivo}"
    falhas=$((falhas + 1))
  fi
}
for n in $(seq 1 9); do rodar "P${n}" "pratica/p${n}_$(case $n in 1) echo degrau;; 2) echo malha_aberta;; 3) echo espaco_estados;; 4) echo identificacao;; 5) echo polos_bode;; 6) echo atraso;; 7) echo ctrb_alocacao;; 8) echo observador;; 9) echo memorial;; esac).py" AuroraArm.json; done
for spec in '10 malha_fechada' '11 erro_regime' '12 pid_windup' '13 ziegler_nichols' '14 amostragem' '15 discretizacao' '16 cosim' '17 memorial_d'; do set -- $spec; rodar "P$1" "pratica/p$1_$2.py" AuroraArm.json; done
rodar P16b_FMU pratica/p16b_fmu_bonus.py AuroraArm.json
for spec in '18 requisitos' '19 explora_estados' '20 contraexemplo' '21 ltl_ctl' '22 timed' '23 cobertura' '24 hypothesis' '25 memorial_d'; do set -- $spec; rodar "P$1" "pratica/p$1_$2.py" planta_u03.json; done
for spec in '26 gerar_codigo' '27 ponto_fixo' '28 sil_compilar' '29 sil_bug' '30 hil_jitter' '31 orcamento_prazo' '32 watchdog' '33 rastreabilidade'; do set -- $spec; rodar "P$1" "pratica/p$1_$2.py" controlador.json; done
if (( falhas )); then
  echo "Execução concluída com ${falhas} rotina(s) com erro. Consulte resultados/execucoes/ e corrija o ambiente ou as entradas."
  exit 1
fi
echo "Todas as rotinas terminaram sem erro. Consulte resultados/execucoes/."
