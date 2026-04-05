from calendar import monthrange
from datetime import date, datetime


def normalizar_data(valor):
    """Converte valores comuns de planilha para date."""
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
    return None


def fim_do_mes(ano, mes):
    return date(int(ano), int(mes), monthrange(int(ano), int(mes))[1])


def status_efetivo(colaborador, referencia=None):
    """Deriva o status real considerando datas de entrada e saída."""
    referencia = referencia or date.today()
    entrada = normalizar_data(colaborador.get("data_entrada"))
    saida = normalizar_data(colaborador.get("data_saida"))
    status = colaborador.get("status")

    if entrada and entrada > referencia:
        return "Inativo"
    if saida and saida <= referencia:
        return "Inativo"
    if status == "Inativo" and saida and saida > referencia:
        return "Ativo"
    if status in ("Ativo", "Inativo"):
        return status
    return "Ativo"


def colaborador_ativo_em(colaborador, referencia=None):
    return status_efetivo(colaborador, referencia=referencia) == "Ativo"
