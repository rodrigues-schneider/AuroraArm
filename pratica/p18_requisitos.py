"""p18 - Da linguagem natural à propriedade formal: classificando os REQ-SAFE.

Mostra como o requisito ambíguo "o robô deve parar rapidamente se houver obstáculo"
vira requisitos formais classificáveis, e por que REQ-SAFE-007 fica fora do modelo discreto.

Uso:  uv run python pratica/p18_requisitos.py
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import u03lab as L

TRES_LEITURAS = [
    ("Quão rápido?", '"rapidamente" não tem número — qualquer atraso satisfaz trivialmente.'),
    ("Parar o quê?", "o comando de torque (lógico, imediato) ou a velocidade física (sujeita à inércia)?"),
    ("A partir de quando?", "do obstáculo físico, da detecção pelo sensor ou da decisão do supervisor?"),
]

TIPOS = {
    "invariante": "condição que vale em todo estado/transição alcançável ('isto nunca deixa de valer').",
    "alcancabilidade": "existe pelo menos um caminho até um estado-alvo ('é possível chegar lá?').",
    "seguranca": "safety: 'nada de ruim acontece' — restrição sobre para onde o sistema pode ir.",
    "vivacidade": "liveness: 'algo bom eventualmente acontece' — o sistema não fica preso.",
    "temporizado": "limite de tempo de pior caso, verificado por autômato temporizado (Aula 11).",
    "invariante_continuo": "invariante sobre uma grandeza contínua — fora do vetor discreto de estados.",
}


def regua(c="="):
    print(c * 70)


def main():
    regua()
    print(" p18 · Um requisito, três leituras incompatíveis")
    regua()
    print('Requisito de ata de reunião: "o robô deve parar rapidamente se houver obstáculo".\n')
    for i, (p, exp) in enumerate(TRES_LEITURAS, 1):
        print(f"  {i}. {p:18} {exp}")
    print("\nAs três leituras são defensáveis — e incompatíveis. A solução separa o")
    print("requisito em dois formais: REQ-SAFE-001 (lógico, sem prazo) e REQ-SAFE-006")
    print("(temporizado, com prazo). Verificados por técnicas diferentes.\n")

    regua("-")
    print(" Os sete REQ-SAFE classificados")
    regua("-")
    print(f"{'ID':14} {'TIPO':22} VERIFICAÇÃO")
    for rid, tipo, _desc, metodo in L.REQUISITOS:
        print(f"{rid:14} {tipo:22} {metodo}")
    print()
    for rid, tipo, desc, _m in L.REQUISITOS:
        print(f"  {rid} ({tipo}): {desc}")

    regua("-")
    print(" Por que REQ-SAFE-007 fica de fora desta unidade")
    regua("-")
    print("REQ-SAFE-007 (velocidade linear ≤ limite) é invariante sobre uma GRANDEZA")
    print("CONTÍNUA. O supervisor trata velocidade só de forma binária (vel0), sem o valor")
    print("contínuo no vetor de estados. Verificá-lo exige rodar planta + controlador +")
    print("supervisor juntos (Unidade 4). Por honestidade técnica, ele continua marcado")
    print("como LACUNA rastreada — não um descuido.\n")

    print("Dica de segurança: um requisito formal é aquele em que dois leitores, aplicando")
    print("o mesmo processo mecânico, chegam SEMPRE à mesma conclusão. Ambiguidade em")
    print("requisito de segurança é superfície de ataque: cada leitura vira um comportamento.")


if __name__ == "__main__":
    main()
