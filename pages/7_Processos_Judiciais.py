"""Módulo de Processos Judiciais & Administrativos.

Gestão de processos judiciais, administrativos e extrajudiciais para a 3S Corporate.
"""
from __future__ import annotations

from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado, obter_usuario_atual
from utils.processos_judiciais import (
    TIPOS_PROCESSO,
    STATUS,
    STATUS_ATIVO,
    STATUS_FINALIZADA,
    STATUS_CONCLUIDO,
    STATUS_INDEFERIDO,
    TIPO_LOG_COMENTARIO,
    TIPO_LOG_CRIACAO,
    TIPO_LOG_EDICAO,
    TIPO_LOG_STATUS,
    adicionar_comentario,
    atualizar_processo,
    criar_processo,
    intimacoes_pendentes,
    listar_log,
    listar_processos,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


garantir_autenticado()
aplicar_estilos_globais()

_usuario = obter_usuario_atual() or {}
USER_EMAIL = _usuario.get("email") or ""
USER_NOME = _usuario.get("nome") or _usuario.get("email") or "desconhecido"

# Restrição de acesso — apenas 2 usuários
USUARIOS_AUTORIZADOS = {"bruno.picinini@3scorporate.com", "gabriel.spohr@3scorporate.com"}

if USER_EMAIL not in USUARIOS_AUTORIZADOS:
    st.error("⛔ Acesso restrito. Este módulo é disponível apenas para usuários autorizados.")
    st.stop()


# ── Paleta por status ────────────────────────────────────────────────

STATUS_CORES = {
    "Análise/Triagem":      {"bg": "#eef1f4", "fg": "#4a5866", "bd": "#d8dee5"},
    "Intimação Pendente":   {"bg": "#fbe1de", "fg": "#a2322a", "bd": "#f2b9b2"},
    "Intimação Respondida": {"bg": "#d9efe9", "fg": "#236b62", "bd": "#b2dfd4"},
    "Judicializado":        {"bg": "#ece3f4", "fg": "#5b3d83", "bd": "#d3c2e5"},
    "Etapa Finalizada":     {"bg": "#e0ecf6", "fg": "#2d5f82", "bd": "#b9d4e8"},
    "Encerrado":            {"bg": "#dcecd7", "fg": "#3d6e43", "bd": "#bad6b1"},
    "Indeferido":           {"bg": "#e6dcda", "fg": "#6e3a34", "bd": "#cfbbb7"},
}

STATUS_EMOJI = {
    "Análise/Triagem":      "⚪",
    "Intimação Pendente":   "🔴",
    "Intimação Respondida": "🟢",
    "Judicializado":        "🟣",
    "Etapa Finalizada":     "🔵",
    "Encerrado":            "✅",
    "Indeferido":           "⚫",
}

ORDEM_STATUS = [
    "Intimação Pendente",
    "Intimação Respondida",
    "Judicializado",
    "Análise/Triagem",
    "Etapa Finalizada",
    "Encerrado",
    "Indeferido",
]


# ── CSS local ────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    div[data-testid="stExpander"] summary {
        font-weight: 700;
    }

    div[class*="st-key-pj-row-"] {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 0.35rem 0.5rem;
        transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[class*="st-key-pj-row-"]:hover {
        border-color: #8E8E93;
        background: rgba(142, 142, 147, 0.07);
        box-shadow: 0 2px 6px rgba(35, 64, 85, 0.08);
    }

    .pj-titulo { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
    .pj-titulo-nome {
        color: var(--navy, #111111);
        font-weight: 700;
        font-size: 0.92rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .pj-titulo-proc {
        color: var(--muted, #6E6E73);
        font-size: 0.74rem;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        letter-spacing: -0.01em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .pj-titulo-proc span { white-space: nowrap; }
    .pj-titulo-proc span + span::before {
        content: "·";
        margin: 0 0.35rem;
        color: var(--line, #E5E5EA);
    }

    .pj-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; justify-content: flex-end; }
    .pj-tag {
        display: inline-flex; align-items: center;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .pj-tag-status { padding-left: 0.45rem; padding-right: 0.7rem; }
    .pj-tag-status::before {
        content: "";
        width: 6px; height: 6px; border-radius: 50%;
        background: currentColor;
        margin-right: 5px;
        opacity: 0.75;
    }

    .pj-tag-tipo-judicial {
        background: #ece3f4;
        color: #5b3d83;
        border-color: #d3c2e5;
        font-weight: 800;
    }
    .pj-tag-tipo-admin {
        background: #f5ecd8;
        color: #a97e2a;
        border-color: #e4d2a0;
        font-weight: 800;
    }

    .pj-meta {
        display: flex; flex-direction: column; gap: 0.15rem;
        align-items: flex-end;
        text-align: right;
        min-width: 0;
    }
    .pj-valor {
        color: var(--navy, #111111);
        font-weight: 800;
        font-size: 0.95rem;
        letter-spacing: -0.01em;
    }
    .pj-datas {
        color: var(--muted, #6E6E73);
        font-size: 0.72rem;
        font-weight: 600;
    }
    .pj-datas.warn { color: #a2322a; font-weight: 800; }

    .pj-log { display: flex; flex-direction: column; gap: 0.45rem; max-height: 260px; overflow-y: auto; }
    .pj-log-item {
        background: var(--surface-soft, #FAFAFA);
        border: 1px solid var(--line, #E5E5EA);
        border-radius: 10px;
        padding: 0.5rem 0.65rem;
    }
    .pj-log-head {
        display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: baseline;
        font-size: 0.72rem;
        color: var(--muted, #6E6E73);
        font-weight: 700;
    }
    .pj-log-icon { font-size: 0.8rem; }
    .pj-log-tipo { color: var(--navy, #111111); text-transform: uppercase; letter-spacing: 0.06em; }
    .pj-log-data { font-family: ui-monospace, Menlo, Consolas, monospace; }
    .pj-log-user { font-style: italic; }
    .pj-log-text {
        margin-top: 0.2rem;
        color: var(--text, #111111);
        font-size: 0.85rem;
        line-height: 1.35;
        word-break: break-word;
        white-space: pre-wrap;
    }

    @media (max-width: 900px) {
        .pj-meta { align-items: flex-start; text-align: left; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Formatação ───────────────────────────────────────────────────────


def _br_moeda(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _br_data(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _soma(registros, campo: str) -> float:
    total = 0.0
    for r in registros:
        v = r.get(campo)
        if v is None:
            continue
        try:
            total += float(v)
        except (TypeError, ValueError):
            continue
    return total


# ── Carregamento ─────────────────────────────────────────────────────

registros = listar_processos()
ativos = [r for r in registros if r.get("status") in STATUS_ATIVO]
finalizados = [r for r in registros if r.get("status") in STATUS_FINALIZADA]
concluidos = [r for r in registros if r.get("status") in STATUS_CONCLUIDO]
indeferidos = [r for r in registros if r.get("status") in STATUS_INDEFERIDO]
pendentes = intimacoes_pendentes()

total_em_questao = _soma(ativos, "valor")
total_encerrado = _soma(concluidos, "valor")


# ── Cabeçalho ────────────────────────────────────────────────────────

renderizar_cabecalho_pagina(
    "Intimações & Jurídico",
    "Gestão de processos judiciais, administrativos e extrajudiciais.",
    badge=f"{len(registros)} processos",
)


# ── Banner de alerta ─────────────────────────────────────────────────

if pendentes:
    qtd = len(pendentes)
    rotulo = "intimação pendente" if qtd == 1 else "intimações pendentes"
    valor = _br_moeda(_soma(pendentes, "valor"))
    st.error(
        f"**⚠ {qtd} {rotulo}** aguardando resposta — total de {valor} em jogo.",
        icon="🚨",
    )


# ── KPIs ─────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Em questão",
    _br_moeda(total_em_questao),
    help=f"{len(ativos)} processos em andamento",
)
c2.metric(
    "Encerrado",
    _br_moeda(total_encerrado),
    help=f"{len(concluidos)} processos encerrados",
)
c3.metric(
    "Indeferido",
    str(len(indeferidos)),
    help=f"{len(indeferidos)} processos indeferidos",
)
c4.metric(
    "Intimações pendentes",
    str(len(pendentes)),
    help="Processos aguardando resposta",
)


# ── Render helpers ──────────────────────────────────────────────────


def _tag_status(status: str) -> str:
    cores = STATUS_CORES.get(status, {"bg": "#eef1f4", "fg": "#4a5866", "bd": "#d8dee5"})
    return (
        f'<span class="pj-tag pj-tag-status" '
        f'style="background:{cores["bg"]};color:{cores["fg"]};border-color:{cores["bd"]};">'
        f'{escape(status)}</span>'
    )


def _tag_tipo(tipo: str) -> str:
    if not tipo:
        return ""
    t = str(tipo).strip()
    if not t:
        return ""
    cls = "pj-tag-tipo-judicial" if t.upper() == "JUDICIAL" else "pj-tag-tipo-admin"
    return f'<span class="pj-tag {cls}">{escape(t)}</span>'


def _html_titulo(r: dict) -> str:
    titulo_raw = r.get("titulo") or "—"
    titulo = escape(str(titulo_raw).upper() if titulo_raw != "—" else "—")
    numero = r.get("numero_processo") or "—"
    cliente = r.get("cliente") or "—"

    proc_parts = [f'<span>Nº {escape(str(numero))}</span>']
    if cliente and str(cliente).strip():
        proc_parts.append(f'<span>{escape(str(cliente))}</span>')

    return (
        '<div class="pj-titulo">'
        f'<div class="pj-titulo-nome">{titulo}</div>'
        f'<div class="pj-titulo-proc">{"".join(proc_parts)}</div>'
        '</div>'
    )


def _html_tags(r: dict) -> str:
    status = r.get("status") or "—"
    tags = (
        _tag_status(status)
        + _tag_tipo(r.get("tipo_processo"))
    )
    return f'<div class="pj-tags">{tags}</div>'


def _html_meta(r: dict) -> str:
    status = r.get("status") or "—"
    valor = _br_moeda(r.get("valor"))
    prazo = r.get("prazo_fatal")

    parts = [f'<div class="pj-valor">{valor}</div>']
    if prazo:
        prazo_txt = _br_data(prazo)
        cls = " warn" if status == "Intimação Pendente" else ""
        label = "Prazo fatal" if status == "Intimação Pendente" else "Prazo"
        parts.append(f'<div class="pj-datas{cls}">{label}: {escape(prazo_txt)}</div>')

    return f'<div class="pj-meta">{"".join(parts)}</div>'


def _fmt_data_hora(dh) -> str:
    if isinstance(dh, datetime):
        return dh.strftime("%d/%m/%Y %H:%M")
    return str(dh) if dh else "—"


LOG_LABELS = {
    TIPO_LOG_CRIACAO: ("✨", "Criação"),
    TIPO_LOG_COMENTARIO: ("💬", "Comentário"),
    TIPO_LOG_STATUS: ("🔁", "Status"),
    TIPO_LOG_EDICAO: ("✎", "Edição"),
}


def _render_timeline(pid: int) -> None:
    logs = listar_log(pid)
    if not logs:
        st.caption("Nenhum histórico ainda.")
        return
    items = []
    for log in logs:
        icon, rotulo = LOG_LABELS.get(log.get("tipo"), ("•", "Evento"))
        data_txt = escape(_fmt_data_hora(log.get("data_hora")))
        usuario = escape(str(log.get("usuario") or "—"))
        texto = escape(str(log.get("texto") or ""))
        items.append(
            '<div class="pj-log-item">'
            f'<div class="pj-log-head">'
            f'<span class="pj-log-icon">{icon}</span>'
            f'<span class="pj-log-tipo">{rotulo}</span>'
            f'<span class="pj-log-data">{data_txt}</span>'
            f'<span class="pj-log-user">por {usuario}</span>'
            '</div>'
            f'<div class="pj-log-text">{texto}</div>'
            '</div>'
        )
    st.markdown(f'<div class="pj-log">{"".join(items)}</div>', unsafe_allow_html=True)


def _render_popover(r: dict, user_nome: str) -> None:
    pid = r.get("id")
    status_atual = r.get("status") or "Análise/Triagem"
    idx = STATUS.index(status_atual) if status_atual in STATUS else 0

    st.markdown(
        f"**{escape(str(r.get('titulo') or '—'))}** · "
        f"Nº {escape(str(r.get('numero_processo') or '—'))}"
    )
    novo_status = st.selectbox(
        "Status", STATUS, index=idx, key=f"edit_st_{pid}"
    )
    comentario = st.text_area(
        "Observação / comentário",
        key=f"edit_cm_{pid}",
        height=90,
    )
    if st.button("Salvar", type="primary", key=f"edit_sv_{pid}", use_container_width=True):
        mudou_algo = False
        if novo_status != status_atual:
            try:
                atualizar_processo(pid, {"status": novo_status}, user_nome)
                mudou_algo = True
            except Exception as e:
                st.error(f"Erro ao atualizar status: {e}")
                return
        texto = (comentario or "").strip()
        if texto:
            try:
                adicionar_comentario(pid, texto, user_nome)
                mudou_algo = True
            except Exception as e:
                st.error(f"Erro ao salvar comentário: {e}")
                return
        if mudou_algo:
            st.rerun()
        else:
            st.info("Nenhuma alteração para salvar.")

    st.markdown("###### Histórico")
    _render_timeline(pid)


def _render_popover_view(r: dict) -> None:
    pid = r.get("id")
    st.markdown(
        f"**{escape(str(r.get('titulo') or '—'))}** · "
        f"Nº {escape(str(r.get('numero_processo') or '—'))}"
    )
    status_atual = r.get("status") or "—"
    st.caption(f"Status atual: {escape(str(status_atual))}")
    st.markdown("###### Histórico")
    _render_timeline(pid)


def _render_linha(r: dict, user_nome: str) -> None:
    pid = r.get("id")
    with st.container(key=f"pj-row-{pid}"):
        c_info, c_tags, c_meta, c_acoes = st.columns([5, 3, 2, 1.2], gap="small")
        with c_info:
            st.markdown(_html_titulo(r), unsafe_allow_html=True)
        with c_tags:
            st.markdown(_html_tags(r), unsafe_allow_html=True)
        with c_meta:
            st.markdown(_html_meta(r), unsafe_allow_html=True)
        with c_acoes:
            c_view, c_edit = st.columns(2, gap="small")
            with c_view:
                with st.popover("👁", use_container_width=True, help="Visualizar histórico"):
                    _render_popover_view(r)
            with c_edit:
                with st.popover("✎", use_container_width=True, help="Editar status / comentário"):
                    _render_popover(r, user_nome)


def _render_secao(status: str, registros_status: list[dict], user_nome: str) -> None:
    emoji = STATUS_EMOJI.get(status, "•")
    qtd = len(registros_status)
    total_valor = sum(
        float(r.get("valor") or 0)
        for r in registros_status
    )
    total_txt = _br_moeda(total_valor)
    label = f"{emoji}  {status}  ·  {qtd} processo{'s' if qtd != 1 else ''}  ·  Total: {total_txt}"
    with st.expander(label, expanded=True):
        for r in registros_status:
            _render_linha(r, user_nome)


def _ordenar(registros_status: list[dict], status: str) -> list[dict]:
    if status == "Intimação Pendente":
        return sorted(
            registros_status,
            key=lambda r: (r.get("prazo_fatal") is None, r.get("prazo_fatal") or ""),
        )
    return sorted(
        registros_status,
        key=lambda r: (r.get("data_maturacao") is None, r.get("data_maturacao") or ""),
        reverse=True,
    )


def _filtros(lista: list[dict], key_prefix: str) -> list[dict]:
    if not lista:
        return lista

    clientes_opts = sorted({str(r.get("cliente")).upper() for r in lista if r.get("cliente")})
    tipos_opts = sorted({str(r.get("tipo_processo")) for r in lista if r.get("tipo_processo")})

    with st.expander("🔍 Filtros", expanded=False):
        col1, col2 = st.columns(2)
        sel_cli = col1.multiselect("Cliente", clientes_opts, key=f"{key_prefix}_cli")
        sel_tipo = col2.multiselect("Tipo de Processo", tipos_opts, key=f"{key_prefix}_tipo")

    filtrados = lista
    if sel_cli:
        sel_up = {c.upper() for c in sel_cli}
        filtrados = [r for r in filtrados if str(r.get("cliente") or "").upper() in sel_up]
    if sel_tipo:
        filtrados = [r for r in filtrados if str(r.get("tipo_processo") or "") in sel_tipo]

    if len(filtrados) != len(lista):
        st.caption(f"Mostrando **{len(filtrados)}** de {len(lista)} processos (filtros ativos)")

    return filtrados


def _render_grupo(lista: list[dict], status_permitidos, user_nome: str) -> None:
    if not lista:
        st.info("Nenhum processo corresponde aos filtros.")
        return
    permitidos = set(status_permitidos)
    algum = False
    for status in ORDEM_STATUS:
        if status not in permitidos:
            continue
        subset = [r for r in lista if r.get("status") == status]
        if not subset:
            continue
        subset = _ordenar(subset, status)
        _render_secao(status, subset, user_nome)
        algum = True
    if not algum:
        st.info("Nenhum processo nesta categoria.")


# ── Abas ─────────────────────────────────────────────────────────────

tab_ativos, tab_finalizada, tab_concluidos, tab_indeferidos, tab_novo = st.tabs(
    [
        f"Ativos ({len(ativos)})",
        f"Etapa Finalizada ({len(finalizados)})",
        f"Encerrados ({len(concluidos)})",
        f"Indeferidos ({len(indeferidos)})",
        "➕ Novo",
    ]
)

with tab_ativos:
    _render_grupo(_filtros(ativos, "ativos"), STATUS_ATIVO, USER_NOME)

with tab_finalizada:
    _render_grupo(_filtros(finalizados, "finalizada"), STATUS_FINALIZADA, USER_NOME)

with tab_concluidos:
    _render_grupo(_filtros(concluidos, "concluidos"), STATUS_CONCLUIDO, USER_NOME)

with tab_indeferidos:
    _render_grupo(_filtros(indeferidos, "indeferidos"), STATUS_INDEFERIDO, USER_NOME)

with tab_novo:
    st.markdown("##### Adicionar novo processo")
    st.caption("Apenas o **título** é obrigatório. Os demais campos podem ser completados depois.")

    with st.form("form_novo_pj", clear_on_submit=True):
        col_a, col_b = st.columns(2)

        with col_a:
            titulo_in = st.text_input("Título *", key="nv_titulo", placeholder="Ex: Ação Trabalhista X vs Y")
            numero_in = st.text_input("Nº do Processo", key="nv_numero", placeholder="Ex: 0001234-56.2024.8.26.0100")
            cliente_in = st.text_input("Cliente", key="nv_cliente", placeholder="Ex: MAHINDRA")
            tipo_in = st.selectbox("Tipo de Processo", TIPOS_PROCESSO, key="nv_tipo")
            status_in = st.selectbox("Status", STATUS, index=STATUS.index("Análise/Triagem"), key="nv_status")
            parte_contraria_in = st.text_input("Parte Contrária", key="nv_parte")

        with col_b:
            valor_in = st.number_input(
                "Valor (R$)", min_value=0.0, step=1000.0, format="%.2f", key="nv_valor"
            )
            prazo_fatal_in = st.date_input(
                "Prazo Fatal", value=None, format="DD/MM/YYYY", key="nv_pf"
            )
            data_maturacao_in = st.date_input(
                "Data de Maturação", value=None, format="DD/MM/YYYY", key="nv_dm"
            )

        enviar = st.form_submit_button("Criar processo", type="primary", use_container_width=True)

        if enviar:
            titulo_limpo = (titulo_in or "").strip()
            if not titulo_limpo:
                st.error("Informe o título.")
            else:
                dados = {
                    "titulo": titulo_limpo,
                    "numero_processo": (numero_in or "").strip() or None,
                    "cliente": (cliente_in or "").strip() or None,
                    "tipo_processo": tipo_in,
                    "status": status_in,
                    "parte_contraria": (parte_contraria_in or "").strip() or None,
                    "valor": valor_in or None,
                    "prazo_fatal": prazo_fatal_in,
                    "data_maturacao": data_maturacao_in,
                }
                try:
                    novo_id = criar_processo(dados, USER_NOME)
                except Exception as e:
                    st.error(f"Erro ao criar processo: {e}")
                else:
                    st.success(
                        f"Processo **{dados['titulo']}** "
                        f"({dados.get('numero_processo') or f'#{novo_id}'}) "
                        f"criado com status **{status_in}**."
                    )
                    st.rerun()


st.caption(
    "Use o botão **✎ Editar** em cada processo para trocar o status ou adicionar uma observação/comentário."
)
