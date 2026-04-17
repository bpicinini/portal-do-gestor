"""CRUD e regras de negócio do módulo de Processos Judiciais.

Persiste em duas abas do `dados.xlsx`:
- ``ProcessosJudiciais``: uma linha por processo judicial.
- ``ProcessosJudiciaisLog``: timeline de eventos (criação, comentários, mudanças de campo).

Toda alteração relevante gera entrada automática no log, com autor e timestamp.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from utils.excel_io import (
    SHEET_PROCESSOS_JUDICIAIS,
    SHEET_PROCESSOS_JUDICIAIS_LOG,
    carregar_workbook,
    encontrar_linha,
    proximo_id,
    salvar_workbook,
    sheet_to_list,
    HEADERS,
)

# ── Domínios fixos ────────────────────────────────────────────────────

STATUS = [
    "Análise/Triagem",
    "Intimação Pendente",
    "Intimação Respondida",
    "Judicializado",
    "Etapa Finalizada",
    "Encerrado",
    "Indeferido",
]

# Categorização usada para as abas da UI
STATUS_ATIVO = [s for s in STATUS if s not in {"Encerrado", "Indeferido", "Etapa Finalizada"}]
STATUS_FINALIZADA = {"Etapa Finalizada"}
STATUS_CONCLUIDO = {"Encerrado"}
STATUS_INDEFERIDO = {"Indeferido"}

TIPOS_PROCESSO = ["Administrativo", "Judicial", "Extrajudicial"]

# Campos monetários / datas — usados para normalização
CAMPOS_DATA = {"data_maturacao", "prazo_fatal"}
CAMPOS_NUMERICOS = {"valor"}

# Rótulos amigáveis para registrar no log quando o campo mudar
ROTULOS_CAMPOS = {
    "titulo": "Título",
    "tipo_processo": "Tipo de Processo",
    "parte_contraria": "Parte Contrária",
    "cliente": "Cliente",
    "numero_processo": "Número do Processo",
    "status": "Status",
    "valor": "Valor",
    "prazo_fatal": "Prazo Fatal",
    "data_maturacao": "Data de Maturação",
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


def _normalizar_registro(registro: dict) -> dict:
    """Retorna uma cópia com tipos normalizados para gravação/exibição."""
    norm = dict(registro)
    for campo in CAMPOS_DATA:
        if campo in norm:
            norm[campo] = _normalizar_data(norm[campo])
    for campo in CAMPOS_NUMERICOS:
        if campo in norm:
            norm[campo] = _normalizar_numero(norm[campo])
    return norm


# ── Leitura ───────────────────────────────────────────────────────────


def listar_processos() -> list[dict]:
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    if ws.max_row <= 1:
        return []
    linhas = sheet_to_list(ws)
    return [_normalizar_registro(r) for r in linhas]


def buscar_processo(processo_id: int) -> dict | None:
    for p in listar_processos():
        if p.get("id") == processo_id:
            return p
    return None


def listar_log(processo_id: int | None = None) -> list[dict]:
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS_LOG]
    if ws.max_row <= 1:
        return []
    linhas = sheet_to_list(ws)
    resultado = []
    for r in linhas:
        if processo_id is not None and r.get("processo_id") != processo_id:
            continue
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


def intimacoes_pendentes() -> list[dict]:
    return [p for p in listar_processos() if p.get("status") == "Intimação Pendente"]


# ── Escrita ───────────────────────────────────────────────────────────


def _escrever_linha(ws, headers: list[str], valores: dict, linha: int) -> None:
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=linha, column=col_idx).value = valores.get(header)


def _registrar_log(wb, processo_id: int, tipo: str, texto: str, usuario: str) -> None:
    ws = wb[SHEET_PROCESSOS_JUDICIAIS_LOG]
    headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS_LOG]
    novo_id = proximo_id(ws)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = ws.max_row + 1
    _escrever_linha(ws, headers, {
        "id": novo_id,
        "processo_id": processo_id,
        "data_hora": agora,
        "usuario": usuario,
        "tipo": tipo,
        "texto": texto,
    }, linha)


def criar_processo(dados: dict, usuario: str) -> int:
    """Insere um novo processo judicial e registra criação no log."""
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS]

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
        registro["status"] = "Análise/Triagem"

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


def atualizar_processo(processo_id: int, dados: dict, usuario: str) -> None:
    """Atualiza campos do processo. Gera entradas no log para cada campo alterado."""
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS]

    linha = encontrar_linha(ws, 1, processo_id)
    if linha is None:
        raise ValueError(f"Processo id={processo_id} não encontrado.")

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
        _registrar_log(wb, processo_id, tipo, texto, usuario)

    salvar_workbook(wb)


def adicionar_comentario(processo_id: int, texto: str, usuario: str) -> None:
    """Adiciona entrada livre de comentário na timeline."""
    texto = (texto or "").strip()
    if not texto:
        return
    wb = carregar_workbook()
    _registrar_log(wb, processo_id, TIPO_LOG_COMENTARIO, texto, usuario)
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    linha = encontrar_linha(ws, 1, processo_id)
    if linha is not None:
        headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS]
        col_atu_em = headers.index("atualizado_em") + 1
        col_atu_por = headers.index("atualizado_por") + 1
        ws.cell(row=linha, column=col_atu_em, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ws.cell(row=linha, column=col_atu_por, value=usuario)
    salvar_workbook(wb)


def excluir_processo(processo_id: int) -> None:
    """Remove o processo e todas as entradas do seu log."""
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    linha = encontrar_linha(ws, 1, processo_id)
    if linha is not None:
        ws.delete_rows(linha)

    ws_log = wb[SHEET_PROCESSOS_JUDICIAIS_LOG]
    for row in range(ws_log.max_row, 1, -1):
        if ws_log.cell(row=row, column=2).value == processo_id:
            ws_log.delete_rows(row)

    salvar_workbook(wb)


# ── Inserção em lote (seed / migração) ────────────────────────────────


def inserir_em_lote(registros: Iterable[dict], usuario: str = "sistema") -> list[int]:
    """Versão otimizada de criação em massa — salva o workbook uma única vez.

    Cada registro pode incluir ``comentarios_iniciais``: lista de dicts com
    chaves ``data_hora`` (str ISO ou datetime), ``usuario`` e ``texto``.
    """
    wb = carregar_workbook()
    ws = wb[SHEET_PROCESSOS_JUDICIAIS]
    headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS]

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
            registro["status"] = "Análise/Triagem"

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
                ws_log = wb[SHEET_PROCESSOS_JUDICIAIS_LOG]
                log_headers = HEADERS[SHEET_PROCESSOS_JUDICIAIS_LOG]
                linha_log = ws_log.max_row + 1
                _escrever_linha(ws_log, log_headers, {
                    "id": proximo_id(ws_log),
                    "processo_id": novo_id,
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
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, float):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)
