from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, render_template, request

bp = Blueprint("calculos", __name__)

CENTAVOS = Decimal("0.01")

# (limite superior da base, alíquota, parcela a deduzir)
TABELA_IRPF = [
    (Decimal("2428.80"), Decimal("0"), Decimal("0")),
    (Decimal("2826.65"), Decimal("0.075"), Decimal("182.16")),
    (Decimal("3751.05"), Decimal("0.15"), Decimal("394.16")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("675.49")),
    (None, Decimal("0.275"), Decimal("908.73")),
]


def arredondar(valor):
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def calcular_irpf(salario_bruto):
    """Devolve (imposto, aliquota_em_%, reducao) para o salário bruto mensal."""
    aliquota, deducao = Decimal("0"), Decimal("0")
    for limite, aliq, ded in TABELA_IRPF:
        if limite is None or salario_bruto <= limite:
            aliquota, deducao = aliq, ded
            break

    imposto = max(Decimal("0"), salario_bruto * aliquota - deducao)

    # Redução da Lei 15.270/2025 (vale a partir de 2026)
    if salario_bruto <= Decimal("5000"):
        reducao = Decimal("312.89")
    elif salario_bruto <= Decimal("7350"):
        reducao = Decimal("978.62") - Decimal("0.133145") * salario_bruto
    else:
        reducao = Decimal("0")

    reducao = min(max(reducao, Decimal("0")), imposto)  # nunca passa do imposto
    imposto_final = imposto - reducao

    return arredondar(imposto_final), aliquota * 100, arredondar(reducao)


def calcular_13_proporcional(salario_base, meses):
    """13º proporcional aproximado: salário / 12 x meses trabalhados."""
    return arredondar(salario_base / Decimal("12") * Decimal(meses))


@bp.route("/painel", methods=("GET", "POST"))
def painel():
    resultado = None
    erro = None
    ferramenta = request.form.get("ferramenta")

    if request.method == "POST":
        try:
            if ferramenta == "irpf":
                salario = Decimal(request.form["salario_bruto"])
                if salario <= 0:
                    raise ValueError("O salário deve ser maior que zero.")
                imposto, aliquota, reducao = calcular_irpf(salario)
                resultado = {
                    "tipo": "irpf",
                    "salario": arredondar(salario),
                    "aliquota": aliquota,
                    "reducao": reducao,
                    "imposto": imposto,
                }
            elif ferramenta == "rescisao":
                salario = Decimal(request.form["salario_base"])
                meses = int(request.form["meses"])
                if salario <= 0:
                    raise ValueError("O salário deve ser maior que zero.")
                if not 1 <= meses <= 12:
                    raise ValueError("Os meses devem estar entre 1 e 12.")
                resultado = {
                    "tipo": "rescisao",
                    "salario": arredondar(salario),
                    "meses": meses,
                    "decimo": calcular_13_proporcional(salario, meses),
                }
            else:
                erro = "Ferramenta inválida."
        except (ValueError, ArithmeticError, KeyError) as e:
            erro = str(e) or "Valor inválido. Confira os campos."

    return render_template("calculos/painel.html", resultado=resultado, erro=erro)