"""CRUD e regras de negócio do módulo de Restituições.

Persiste em duas abas do `dados.xlsx`:
- ``Restituicoes``: uma linha por processo de restituição.
- ``RestituicoesLog``: timeline de eventos (criação, comentários, mudanças de campo).

Toda alteração relevante gera entrada automática no log, com autor e timestamp.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from utils.excel_io import (
    SHEET_RESTITUICOES,
    SHEET_RESTITUICOES_LOG,
    carregar_workbook,
    encontrar_linha,
    proximo_id,
    salvar_workbook,
    sheet_to_list,
    HEADERS,
)

# ── Domínios fixos ────────────────────────────────────────────────────

STATUS = [
    "Em análise",
    "Com Pendências",
    "Protocolado",
    "Judicializado",
    "Intimação Pendente",
    "Intimação Respondida",
    "Deferido",
    "Pago",
    "Indeferido",
]

# Categorização usada para as 3 abas da UI
STATUS_INDEFERIDO = {"Indeferido"}
STATUS_CONCLUIDO = {"Pago"}
STATUS_ATIVO = [s for s in STATUS if s not in STATUS_INDEFERIDO and s not in STATUS_CONCLUIDO]

DIVISOES = ["Leader", "Winning"]
DESENCAIXES = ["3S", "Cliente"]

# Campos monetários / datas — usados para normalização
CAMPOS_DATA = {"data_protocolo", "data_retificacao", "prazo_fatal"}
CAMPOS_NUMERICOS = {"valor_principal", "valor_corrigido"}
CAMPOS_BOOLEANOS = {"termo_assinado"}

# Rótulos amigáveis para registrar no log quando o campo mudar
ROTULOS_CAMPOS = {
    "numero_processo": "Número do Processo",
    "cliente": "Cliente",
    "cnpj": "CNPJ",
    "status": "Status",
    "processo_ecac": "Processo e-CAC",
    "divisao": "Divisão",
    "desencaixe": "Desencaixe",
    "valor_principal": "Valor Principal",
    "valor_corrigido": "Valor Corrigido",
    "responsavel": "Responsável",
    "data_protocolo": "Data de Protocolo",
    "data_retificacao": "Data de Retificação",
    "motivo_retificacao": "Motivo da Retificação",
    "termo_assinado": "Termo Assinado",
    "prazo_fatal": "Prazo Fatal",
}

TIPO_LOG_CRIACAO = "criacao"
TIPO_LOG_COMENTARIO = "comentario"
TIPO_LOG_STATUS = "status"
TIPO_LOG_EDICAO = "edicao"

# ── Normalização ──────────────────────────────────────────────────────


def _normalizar_data(valor: Any) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valor.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _normalizar_numero(valor: Any) -> float | None:
    if valor in (None, ""):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _normalizar_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "1", "sim", "yes", "x", "✓", "✔")
    return False


def _normalizar_registro(registro: dict) -> dict:
    """Retorna uma cópia com tipos normalizados para gravação/exibição."""
    norm = dict(registro)
    for campo in CAMPOS_DATA:
        if campo in norm:
            norm[campo] = _normalizar_data(norm[campo])
    for campo in CAMPOS_NUMERICOS:
        if campo in norm:
            norm[campo] = _normalizar_numero(norm[campo])
    for campo in CAMPOS_BOOLEANOS:
        if campo in norm:
            norm[campo] = _normalizar_bool(norm[campo])
    return norm


# ── Leitura ───────────────────────────────────────────────────────────


def listar_restituicoes() -> list[dict]:
    wb = carregar_workbook()
    linhas = sheet_to_list(wb[SHEET_RESTITUICOES])
    return [_normalizar_registro(r) for r in linhas]


def buscar_restituicao(restituicao_id: int) -> dict | None:
    for r in listar_restituicoes():
        if r.get("id") == restituicao_id:
            return r
    return None


def listar_log(restituicao_id: int | None = None) -> list[dict]:
    wb = carregar_workbook()
    linhas = sheet_to_list(wb[SHEET_RESTITUICOES_LOG])
    resultado = []
    for r in linhas:
        if restituicao_id is not None and r.get("restituicao_id") != restituicao_id:
            continue
        # timestamp string -> datetime (ordenação estável)
        dh = r.get("data_hora")
        if isinstance(dh, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    r["data_hora"] = datetime.strptime(dh, fmt)
                    break
                except ValueError:
                    continue
        resultado.append(r)
    resultado.sort(key=lambda x: x.get("data_hora") or datetime.min, reverse=True)
    return resultado


def existe_intimacao_pendente() -> bool:
    return any(r.get("status") == "Intimação Pendente" for r in listar_restituicoes())


def intimacoes_pendentes() -> list[dict]:
    return [r for r in listar_restituicoes() if r.get("status") == "Intimação Pendente"]


# ── Escrita ───────────────────────────────────────────────────────────


def _escrever_linha(ws, headers: list[str], valores: dict, linha: int) -> None:
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=linha, column=col_idx, value=valores.get(header))


def _registrar_log(wb, restituicao_id: int, tipo: str, texto: str, usuario: str) -> None:
    ws = wb[SHEET_RESTITUICOES_LOG]
    headers = HEADERS[SHEET_RESTITUICOES_LOG]
    novo_id = proximo_id(ws)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = ws.max_row + 1
    _escrever_linha(ws, headers, {
        "id": novo_id,
        "restituicao_id": restituicao_id,
        "data_hora": agora,
        "usuario": usuario,
        "tipo": tipo,
        "texto": texto,
    }, linha)


def criar_restituicao(dados: dict, usuario: str) -> int:
    """Insere um novo processo de restituição e registra criação no log."""
    wb = carregar_workbook()
    ws = wb[SHEET_RESTITUICOES]
    headers = HEADERS[SHEET_RESTITUICOES]

    novo_id = proximo_id(ws)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    registro = _normalizar_registro(dados)
    registro.update({
        "id": novo_id,
        "criado_em": agora,
        "criado_por": usuario,
        "atualizado_em": agora,
        "atualizado_por": usuario,
    })
    if not registro.get("status"):
        registro["status"] = "Em análise"

    linha = ws.max_row + 1
    _escrever_linha(ws, headers, registro, linha)

    _registrar_log(
        wb,
        novo_id,
        TIPO_LOG_CRIACAO,
        f"Processo {registro.get('numero_processo') or '—'} criado com status "
        f"'{registro.get('status')}'.",
        usuario,
    )

    salvar_workbook(wb)
    return novo_id


def atualizar_restituicao(restituicao_id: int, dados: dict, usuario: str) -> None:
    """Atualiza campos do processo. Gera entradas no log para cada campo alterado."""
    wb = carregar_workbook()
    ws = wb[SHEET_RESTITUICOES]
    headers = HEADERS[SHEET_RESTITUICOES]

    linha = encontrar_linha(ws, 1, restituicao_id)
    if linha is None:
        raise ValueError(f"Restituição id={restituicao_id} não encontrada.")

    # snapshot atual
    atual = {h: ws.cell(row=linha, column=i).value for i, h in enumerate(headers, 1)}
    atual = _normalizar_registro(atual)

    novos = _normalizar_registro(dados)
    mudancas: list[tuple[str, Any, Any]] = []
    for campo, novo_valor in novos.items():
        if campo in ("id", "criado_em", "criado_por"):
            continue
        if campo not in headers:
            continue
        if atual.get(campo) != novo_valor:
            mudancas.append((campo, atual.get(campo), novo_valor))

    if not mudancas:
        return

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for campo, _, novo_valor in mudancas:
        atual[campo] = novo_valor
    atual["atualizado_em"] = agora
    atual["atualizado_por"] = usuario

    _escrever_linha(ws, headers, atual, linha)

    for campo, antigo, novo in mudancas:
        rotulo = ROTULOS_CAMPOS.get(campo, campo)
        tipo = TIPO_LOG_STATUS if campo == "status" else TIPO_LOG_EDICAO
        texto = f"{rotulo}: {_formatar_valor(antigo)} → {_formatar_valor(novo)}"
        _registrar_log(wb, restituicao_id, tipo, texto, usuario)

    salvar_workbook(wb)


def adicionar_comentario(restituicao_id: int, texto: str, usuario: str) -> None:
    """Adiciona entrada livre de comentário na timeline."""
    texto = (texto or "").strip()
    if not texto:
        return
    wb = carregar_workbook()
    _registrar_log(wb, restituicao_id, TIPO_LOG_COMENTARIO, texto, usuario)
    # carimbo de atualização no registro principal
    ws = wb[SHEET_RESTITUICOES]
    linha = encontrar_linha(ws, 1, restituicao_id)
    if linha is not None:
        headers = HEADERS[SHEET_RESTITUICOES]
        col_atu_em = headers.index("atualizado_em") + 1
        col_atu_por = headers.index("atualizado_por") + 1
        ws.cell(row=linha, column=col_atu_em, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ws.cell(row=linha, column=col_atu_por, value=usuario)
    salvar_workbook(wb)


def excluir_restituicao(restituicao_id: int) -> None:
    """Remove o processo e todas as entradas do seu log."""
    wb = carregar_workbook()
    ws = wb[SHEET_RESTITUICOES]
    linha = encontrar_linha(ws, 1, restituicao_id)
    if linha is not None:
        ws.delete_rows(linha)

    ws_log = wb[SHEET_RESTITUICOES_LOG]
    # percorre de baixo pra cima para preservar índices
    for row in range(ws_log.max_row, 1, -1):
        if ws_log.cell(row=row, column=2).value == restituicao_id:
            ws_log.delete_rows(row)

    salvar_workbook(wb)


# ── Inserção em lote (seed / migração) ────────────────────────────────


def inserir_em_lote(registros: Iterable[dict], usuario: str = "sistema") -> list[int]:
    """Versão otimizada de criação em massa — salva o workbook uma única vez.

    Cada registro pode incluir ``comentarios_iniciais``: lista de dicts com
    chaves ``data_hora`` (str ISO ou datetime), ``usuario`` e ``texto``.
    """
    wb = carregar_workbook()
    ws = wb[SHEET_RESTITUICOES]
    headers = HEADERS[SHEET_RESTITUICOES]

    ids_criados = []
    for dados in registros:
        comentarios = dados.pop("comentarios_iniciais", None)

        novo_id = proximo_id(ws)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        registro = _normalizar_registro(dados)
        registro.update({
            "id": novo_id,
            "criado_em": registro.get("criado_em") or agora,
            "criado_por": registro.get("criado_por") or usuario,
            "atualizado_em": registro.get("atualizado_em") or agora,
            "atualizado_por": registro.get("atualizado_por") or usuario,
        })
        if not registro.get("status"):
            registro["status"] = "Em análise"

        linha = ws.max_row + 1
        _escrever_linha(ws, headers, registro, linha)

        _registrar_log(
            wb,
            novo_id,
            TIPO_LOG_CRIACAO,
            f"Processo {registro.get('numero_processo') or '—'} importado "
            f"com status '{registro.get('status')}'.",
            usuario,
        )

        if comentarios:
            for c in comentarios:
                dh = c.get("data_hora")
                if isinstance(dh, datetime):
                    dh = dh.strftime("%Y-%m-%d %H:%M:%S")
                ws_log = wb[SHEET_RESTITUICOES_LOG]
                log_headers = HEADERS[SHEET_RESTITUICOES_LOG]
                linha_log = ws_log.max_row + 1
                _escrever_linha(ws_log, log_headers, {
                    "id": proximo_id(ws_log),
                    "restituicao_id": novo_id,
                    "data_hora": dh or agora,
                    "usuario": c.get("usuario") or usuario,
                    "tipo": c.get("tipo") or TIPO_LOG_COMENTARIO,
                    "texto": c.get("texto") or "",
                }, linha_log)

        ids_criados.append(novo_id)

    salvar_workbook(wb)
    return ids_criados


# ── Formatação ────────────────────────────────────────────────────────


def _formatar_valor(valor: Any) -> str:
    if valor is None or valor == "":
        return "—"
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, float):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)
