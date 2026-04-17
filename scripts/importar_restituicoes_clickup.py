"""Importa os processos de restituição do Excel exportado do ClickUp para as
novas abas ``Restituicoes`` e ``RestituicoesLog`` do ``dados.xlsx``.

Uso:
    python scripts/importar_restituicoes_clickup.py [arquivo.xlsx]

Se nenhum arquivo for passado, usa ``Controle de Restituições.xlsx`` na raiz.

O parser trata cada sheet de forma linear:
- detecta cabeçalhos de seção (ex: "INTIMAÇÃO PENDENTE", "JURÍDICO")
- mapeia cada seção para um status do novo sistema
- pula linhas de header repetido
- converte cada linha de dados em chamada a ``inserir_em_lote``

As colunas "Latest Comment" e "OBSERVAÇÃO" do ClickUp viram entradas
separadas na timeline (tipo=comentario), preservando o texto original.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# permite rodar como script: raiz do projeto no sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from utils.restituicoes import inserir_em_lote  # noqa: E402

DEFAULT_XLSX = ROOT / "Controle de Restituições.xlsx"

USUARIO_MIGRACAO = "migração ClickUp"

# Cabeçalhos de seção → status final
SECAO_PARA_STATUS = {
    "INTIMAÇÃO PENDENTE": "Intimação Pendente",
    "INTIMAÇÃO RESPONDIDA": "Intimação Respondida",
    "JURÍDICO": "Judicializado",
    "FAVORÁVEL AG VALOR": "Deferido",
    "RESTITUIÇÃO SOLICITADA": "Protocolado",
    "PENDENCIA DOC": "Com Pendências",
    "INDEFERIDOS": "Indeferido",
    "DEFERIDO - PAGAMENTO PROGRAMADO PARA 20/04": "Pago",
}

# Termos no Task Name que indicam arquivamento por desistência
SUFIXOS_ARQUIVAMENTO = ("DESISTÊNCIA", "DESISTENCIA")
# Sufixos irrelevantes que vamos remover do nome do cliente
SUFIXOS_REMOVER = (
    " - INDEFERIDO",
    " - DESISTÊNCIA",
    " - DESISTENCIA",
)


def _norm_divisao(valor) -> str | None:
    if not valor or pd.isna(valor):
        return None
    v = str(valor).strip().upper()
    if v.startswith("WINNING"):
        return "Winning"
    if v.startswith("LEADER"):
        return "Leader"
    return None


def _norm_desencaixe(valor) -> str | None:
    if not valor or pd.isna(valor):
        return None
    v = str(valor).strip().upper()
    if v == "3S":
        return "3S"
    if v.startswith("CLIENTE"):
        return "Cliente"
    return None


def _norm_bool(valor) -> bool:
    if valor is None or pd.isna(valor):
        return False
    s = str(valor).strip().lower()
    return s in ("true", "1", "sim", "x", "✓", "yes")


def _norm_str(valor) -> str | None:
    if valor is None or pd.isna(valor):
        return None
    s = str(valor).strip()
    return s or None


def _norm_numero(valor) -> float | None:
    if valor is None or pd.isna(valor):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _norm_data(valor):
    if valor is None or pd.isna(valor):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if hasattr(valor, "date"):
        try:
            return valor.date()
        except Exception:
            pass
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(valor.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _separar_numero_cliente(task_name: str | None) -> tuple[str | None, str | None]:
    """Separa 'OE1260/24 - BLK' em ('OE1260/24', 'BLK').

    Remove sufixos conhecidos (- INDEFERIDO, - DESISTÊNCIA).
    Se não houver separador, retorna o texto todo em numero_processo.
    """
    if not task_name:
        return None, None
    nome = task_name.strip()
    for sufixo in SUFIXOS_REMOVER:
        if nome.upper().endswith(sufixo.upper()):
            nome = nome[: -len(sufixo)].strip()

    if " - " in nome:
        numero, cliente = nome.split(" - ", 1)
        return numero.strip() or None, cliente.strip() or None
    # tenta um único hífen como fallback (sem espaços)
    partes = re.split(r"\s*-\s*", nome, maxsplit=1)
    if len(partes) == 2:
        return partes[0].strip() or None, partes[1].strip() or None
    return nome, None


_RE_DATA_PREFIXO = re.compile(
    r"^(?P<d>\d{1,2})/(?P<m>\d{1,2})(?:/(?P<y>\d{2,4}))?\s*:\s*"
)


def _extrair_data_comentario(texto: str) -> datetime | None:
    """Se o comentário começar com 'DD/MM/YY:' ou 'DD/MM/YYYY:', retorna data.
    Senão retorna None (usaremos o timestamp da migração).
    """
    m = _RE_DATA_PREFIXO.match(texto.strip())
    if not m:
        return None
    d, mo, y = int(m.group("d")), int(m.group("m")), m.group("y")
    if y is None:
        y = datetime.now().year
    else:
        y = int(y)
        if y < 100:
            y += 2000
    try:
        return datetime(y, mo, d)
    except ValueError:
        return None


def _construir_mapa_colunas(headers: list[str], tem_valor_corrigido: bool) -> dict[str, int]:
    """Mapeia nome lógico → índice de coluna, baseado na linha de header.

    Concluídos tem uma coluna 'VALOR CORRIGIDO' extra; as demais sheets não.
    """
    # fallback por posição caso o nome não bata
    if tem_valor_corrigido:
        return {
            "task_id": 0,
            "task_name": 1,
            "assignee": 2,
            "divisao": 3,
            "desencaixe": 4,
            "valor_principal": 5,
            "valor_corrigido": 6,
            "processo_ecac": 7,
            "prazo_fatal": 8,
            "latest_comment": 9,
            "observacao": 10,
            "data_retificacao": 11,
            "cnpj": 12,
            "termo_assinado": 13,
            "data_protocolo": 14,
            "motivo_retificacao": 15,
        }
    return {
        "task_id": 0,
        "task_name": 1,
        "assignee": 2,
        "divisao": 3,
        "desencaixe": 4,
        "valor_principal": 5,
        "processo_ecac": 6,
        "prazo_fatal": 7,
        "latest_comment": 8,
        "observacao": 9,
        "data_retificacao": 10,
        "cnpj": 11,
        "termo_assinado": 12,
        "data_protocolo": 13,
        "motivo_retificacao": 14,
    }


def _linha_eh_secao(row) -> str | None:
    """Se a linha tem só um valor na primeira coluna e é uma seção conhecida, retorna o nome."""
    primeira = str(row[0]).strip().upper() if (len(row) and not pd.isna(row[0])) else ""
    if primeira in SECAO_PARA_STATUS:
        return primeira
    return None


def _linha_eh_header(row) -> bool:
    primeira = str(row[0]).strip() if (len(row) and not pd.isna(row[0])) else ""
    return primeira == "Task ID"


def _extrair_registro(row, cols: dict[str, int], status: str) -> dict | None:
    """Converte uma linha bruta em dict de registro pronto para inserir."""
    task_name = _norm_str(row[cols["task_name"]])
    if not task_name:
        return None

    numero, cliente = _separar_numero_cliente(task_name)

    registro = {
        "numero_processo": numero,
        "cliente": cliente,
        "cnpj": _norm_str(row[cols["cnpj"]]),
        "processo_ecac": _norm_str(row[cols["processo_ecac"]]),
        "divisao": _norm_divisao(row[cols["divisao"]]),
        "desencaixe": _norm_desencaixe(row[cols["desencaixe"]]),
        "valor_principal": _norm_numero(row[cols["valor_principal"]]),
        "responsavel": _norm_str(row[cols["assignee"]]),
        "data_protocolo": _norm_data(row[cols["data_protocolo"]]),
        "data_retificacao": _norm_data(row[cols["data_retificacao"]]),
        "motivo_retificacao": _norm_str(row[cols["motivo_retificacao"]]),
        "termo_assinado": _norm_bool(row[cols["termo_assinado"]]),
        "prazo_fatal": _norm_data(row[cols["prazo_fatal"]]),
        "status": status,
    }
    if "valor_corrigido" in cols:
        registro["valor_corrigido"] = _norm_numero(row[cols["valor_corrigido"]])

    # constrói comentários iniciais a partir de Latest Comment e Observação
    comentarios = []

    if task_name.upper().endswith(SUFIXOS_ARQUIVAMENTO):
        comentarios.append({
            "data_hora": datetime.now(),
            "usuario": USUARIO_MIGRACAO,
            "tipo": "comentario",
            "texto": "Arquivado por desistência.",
        })

    latest = _norm_str(row[cols["latest_comment"]])
    if latest:
        dt = _extrair_data_comentario(latest) or datetime.now()
        comentarios.append({
            "data_hora": dt,
            "usuario": USUARIO_MIGRACAO,
            "tipo": "comentario",
            "texto": latest,
        })

    obs = _norm_str(row[cols["observacao"]])
    if obs:
        comentarios.append({
            "data_hora": datetime.now(),
            "usuario": USUARIO_MIGRACAO,
            "tipo": "comentario",
            "texto": f"Observação: {obs}",
        })

    if comentarios:
        registro["comentarios_iniciais"] = comentarios

    return registro


def processar_sheet(df: pd.DataFrame, status_default: str | None = None,
                    forcar_status: bool = False) -> list[dict]:
    """Percorre uma sheet, rastreando a seção atual e extraindo registros.

    Se ``forcar_status`` é True, ignora cabeçalhos de seção e usa
    ``status_default`` para todas as linhas (útil na aba Concluídos,
    que tem dois títulos horizontais na mesma linha).
    """
    registros: list[dict] = []
    status_atual = status_default
    cols = None

    # sheet "Concluídos" tem seções na linha 0 e headers na linha 1
    # sheet "Ativos"/"Indeferidos" tem "Restituições" na 1, seção na 2, header na 3
    for idx in range(len(df)):
        row = df.iloc[idx].tolist()
        if all(pd.isna(v) for v in row):
            continue

        # verifica cabeçalhos de seção em qualquer coluna não-vazia
        if not forcar_status:
            celulas_preenchidas = [(i, str(v).strip().upper()) for i, v in enumerate(row) if not pd.isna(v)]
            for _i, texto in celulas_preenchidas:
                if texto in SECAO_PARA_STATUS:
                    status_atual = SECAO_PARA_STATUS[texto]
                    break

        # header "Task ID ..." → define mapa de colunas
        if _linha_eh_header(row):
            tem_vc = any(not pd.isna(v) and "VALOR CORRIGIDO" in str(v).upper() for v in row)
            cols = _construir_mapa_colunas(row, tem_vc)
            continue

        # linha de "Restituições" (título da sheet), seções isoladas ou totalizadores
        primeira = str(row[0]).strip().upper() if not pd.isna(row[0]) else ""
        if primeira in SECAO_PARA_STATUS or primeira in ("RESTITUIÇÕES", "RESTITUICOES"):
            continue
        # linhas com só numéricos (total) — descartar
        if not _norm_str(row[1] if len(row) > 1 else None):
            continue

        if cols is None or status_atual is None:
            # dados antes de header/seção — inesperado, pula
            continue

        registro = _extrair_registro(row, cols, status_atual)
        if registro:
            registros.append(registro)

    return registros


def processar_concluidos(df: pd.DataFrame) -> list[dict]:
    """Sheet 'Concluídos' tem layout diferente: seções no row 0 (horizontal).

    Todos os registros dessa aba representam processos com pagamento
    programado para 20/04 — antecipados para status ``Pago`` já na
    importação para abastecer a aba Concluídos da UI.
    """
    status = SECAO_PARA_STATUS["DEFERIDO - PAGAMENTO PROGRAMADO PARA 20/04"]
    return processar_sheet(df, status_default=status, forcar_status=True)


def importar(caminho: Path) -> list[int]:
    xl = pd.ExcelFile(caminho)
    todos: list[dict] = []
    for nome in xl.sheet_names:
        df = xl.parse(nome, header=None)
        if nome.strip().lower().startswith("conclu"):
            registros = processar_concluidos(df)
        else:
            registros = processar_sheet(df)
        print(f"[{nome}] {len(registros)} registros extraídos")
        todos.extend(registros)

    ids = inserir_em_lote(todos, usuario=USUARIO_MIGRACAO)
    return ids


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}", file=sys.stderr)
        sys.exit(1)
    ids = importar(caminho)
    print(f"\n✓ {len(ids)} processos importados")


if __name__ == "__main__":
    main()
