"""Módulo de Restituições — gestão de processos de restituição de impostos
junto à Receita Federal, substituindo o antigo controle via ClickUp.
"""
from __future__ import annotations

from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado, obter_usuario_atual
from utils.restituicoes import (
    DESENCAIXES,
    DIVISOES,
    STATUS,
    STATUS_ATIVO,
    STATUS_CONCLUIDO,
    STATUS_INDEFERIDO,
    TIPO_LOG_COMENTARIO,
    TIPO_LOG_CRIACAO,
    TIPO_LOG_EDICAO,
    TIPO_LOG_STATUS,
    adicionar_comentario,
    atualizar_restituicao,
    criar_restituicao,
    intimacoes_pendentes,
    listar_log,
    listar_restituicoes,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


garantir_autenticado()
aplicar_estilos_globais()

_usuario = obter_usuario_atual() or {}
USER_NOME = _usuario.get("nome") or _usuario.get("email") or "desconhecido"


# ── Paleta por status (progressão visual) ────────────────────────────

STATUS_CORES = {
    "Em análise":           {"bg": "#eef1f4", "fg": "#4a5866", "bd": "#d8dee5"},
    "Com Pendências":       {"bg": "#fdf1d8", "fg": "#8a6a1f", "bd": "#f2dea8"},
    "Protocolado":          {"bg": "#e0ecf6", "fg": "#2d5f82", "bd": "#b9d4e8"},
    "Judicializado":        {"bg": "#ece3f4", "fg": "#5b3d83", "bd": "#d3c2e5"},
    "Intimação Pendente":   {"bg": "#fbe1de", "fg": "#a2322a", "bd": "#f2b9b2"},
    "Intimação Respondida": {"bg": "#d9efe9", "fg": "#236b62", "bd": "#b2dfd4"},
    "Deferido":             {"bg": "#dcecd7", "fg": "#3d6e43", "bd": "#bad6b1"},
    "Pago":                 {"bg": "#c8e5c0", "fg": "#2a5a33", "bd": "#a3cf98"},
    "Indeferido":           {"bg": "#e6dcda", "fg": "#6e3a34", "bd": "#cfbbb7"},
}

# Emoji de indicador visual para o header da seção (único cue disponível no label do st.expander)
STATUS_EMOJI = {
    "Em análise":           "⚪",
    "Com Pendências":       "🟡",
    "Protocolado":          "🔵",
    "Judicializado":        "🟣",
    "Intimação Pendente":   "🔴",
    "Intimação Respondida": "🟢",
    "Deferido":             "🟢",
    "Pago":                 "💰",
    "Indeferido":           "⚫",
}

# Ordem de exibição — Deferido no topo (quase ganhos), Com Pendências no fim
ORDEM_STATUS = [
    "Deferido",
    "Intimação Respondida",
    "Intimação Pendente",
    "Judicializado",
    "Protocolado",
    "Em análise",
    "Com Pendências",
    "Pago",
    "Indeferido",
]


# ── CSS local ────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Expander de status (cada seção) */
    div[data-testid="stExpander"] summary {
        font-weight: 700;
    }

    /* Highlight de linha de processo ao passar o mouse */
    div[class*="st-key-rst-row-"] {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 0.35rem 0.5rem;
        transition: border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
    }
    div[class*="st-key-rst-row-"]:hover {
        border-color: #8E8E93;
        background: rgba(142, 142, 147, 0.07);
        box-shadow: 0 2px 6px rgba(35, 64, 85, 0.08);
    }

    .rst-cliente { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
    .rst-cliente-nome {
        color: var(--navy, #111111);
        font-weight: 700;
        font-size: 0.92rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .rst-cliente-proc {
        color: var(--muted, #6E6E73);
        font-size: 0.74rem;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        letter-spacing: -0.01em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .rst-cliente-proc span { white-space: nowrap; }
    .rst-cliente-proc span + span::before {
        content: "·";
        margin: 0 0.35rem;
        color: var(--line, #E5E5EA);
    }

    .rst-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; justify-content: flex-end; }
    .rst-tag {
        display: inline-flex; align-items: center;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .rst-tag-status { padding-left: 0.45rem; padding-right: 0.7rem; }
    .rst-tag-status::before {
        content: "";
        width: 6px; height: 6px; border-radius: 50%;
        background: currentColor;
        margin-right: 5px;
        opacity: 0.75;
    }

    .rst-tag-div-leader  { background: #111111; color: #ece0c8; border-color: #1a2a37; }
    .rst-tag-div-winning { background: #6e2935; color: #f4d6dc; border-color: #4f1c24; }

    .rst-tag-desc-3s {
        background: #f5ecd8;
        color: #a97e2a;
        border-color: #e4d2a0;
        font-weight: 800;
    }
    .rst-tag-desc-cliente { background: #eef1f4; color: #6E6E73; border-color: #dce1e7; }

    .rst-meta {
        display: flex; flex-direction: column; gap: 0.15rem;
        align-items: flex-end;
        text-align: right;
        min-width: 0;
    }
    .rst-valor {
        color: var(--navy, #111111);
        font-weight: 800;
        font-size: 0.95rem;
        letter-spacing: -0.01em;
    }
    .rst-datas {
        color: var(--muted, #6E6E73);
        font-size: 0.72rem;
        font-weight: 600;
    }
    .rst-datas.warn { color: #a2322a; font-weight: 800; }

    /* Timeline dentro do popover */
    .rst-log { display: flex; flex-direction: column; gap: 0.45rem; max-height: 260px; overflow-y: auto; }
    .rst-log-item {
        background: var(--surface-soft, #FAFAFA);
        border: 1px solid var(--line, #E5E5EA);
        border-radius: 10px;
        padding: 0.5rem 0.65rem;
    }
    .rst-log-head {
        display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: baseline;
        font-size: 0.72rem;
        color: var(--muted, #6E6E73);
        font-weight: 700;
    }
    .rst-log-icon { font-size: 0.8rem; }
    .rst-log-tipo { color: var(--navy, #111111); text-transform: uppercase; letter-spacing: 0.06em; }
    .rst-log-data { font-family: ui-monospace, Menlo, Consolas, monospace; }
    .rst-log-user { font-style: italic; }
    .rst-log-text {
        margin-top: 0.2rem;
        color: var(--text, #111111);
        font-size: 0.85rem;
        line-height: 1.35;
        word-break: break-word;
        white-space: pre-wrap;
    }

    @media (max-width: 900px) {
        .rst-meta { align-items: flex-start; text-align: left; }
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


def _valor_exibicao(r: dict):
    """Usa valor_corrigido quando disponível (Deferido/Pago)."""
    status = r.get("status")
    if status in STATUS_CONCLUIDO or status == "Deferido":
        v = r.get("valor_corrigido")
        if v is not None:
            return v
    return r.get("valor_principal")


# ── Carregamento ─────────────────────────────────────────────────────

registros = listar_restituicoes()
ativos = [r for r in registros if r.get("status") in STATUS_ATIVO]
concluidos = [r for r in registros if r.get("status") in STATUS_CONCLUIDO]
indeferidos = [r for r in registros if r.get("status") in STATUS_INDEFERIDO]
pendentes = intimacoes_pendentes()

total_recuperacao = _soma(ativos, "valor_principal")
deferidos = [r for r in ativos if r.get("status") == "Deferido"]
total_deferido = sum(
    float(r.get("valor_corrigido") or r.get("valor_principal") or 0) for r in deferidos
)
total_pago = sum(
    float(r.get("valor_corrigido") or r.get("valor_principal") or 0) for r in concluidos
)


# ── Cabeçalho ────────────────────────────────────────────────────────

renderizar_cabecalho_pagina(
    "Restituições",
    "Gestão dos processos de restituição de impostos junto à Receita Federal.",
    badge=f"{len(registros)} processos",
)


# ── Banner de alerta ─────────────────────────────────────────────────

if pendentes:
    qtd = len(pendentes)
    rotulo = "intimação pendente" if qtd == 1 else "intimações pendentes"
    valor = _br_moeda(_soma(pendentes, "valor_principal"))
    st.error(
        f"**⚠ {qtd} {rotulo}** aguardando resposta — total de {valor} em jogo. "
        f"Abra a aba **Ativos** e role até a seção *Intimação Pendente* para responder.",
        icon="🚨",
    )


# ── KPIs ─────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Em recuperação",
    _br_moeda(total_recuperacao),
    help=f"{len(ativos)} processos em andamento",
)
c2.metric(
    "Aguardando pagamento",
    _br_moeda(total_deferido),
    help=f"{len(deferidos)} deferidos, pagamento pendente",
)
c3.metric(
    "Já recuperado",
    _br_moeda(total_pago),
    help=f"{len(concluidos)} processos pagos",
)
c4.metric(
    "Intimações pendentes",
    str(len(pendentes)),
    help="Processos com resposta em aberto para a RFB",
)


# ── Render helpers ──────────────────────────────────────────────────


def _tag_status(status: str) -> str:
    cores = STATUS_CORES.get(status, {"bg": "#eef1f4", "fg": "#4a5866", "bd": "#d8dee5"})
    return (
        f'<span class="rst-tag rst-tag-status" '
        f'style="background:{cores["bg"]};color:{cores["fg"]};border-color:{cores["bd"]};">'
        f'{escape(status)}</span>'
    )


def _tag_divisao(divisao) -> str:
    if not divisao:
        return ""
    dv = str(divisao).strip()
    if not dv:
        return ""
    cls = "rst-tag-div-leader" if dv.lower().startswith("leader") else "rst-tag-div-winning"
    return f'<span class="rst-tag {cls}">{escape(dv)}</span>'


def _tag_desencaixe(desencaixe) -> str:
    if not desencaixe:
        return ""
    dx = str(desencaixe).strip()
    if not dx:
        return ""
    cls = "rst-tag-desc-3s" if dx.lower() == "3s" else "rst-tag-desc-cliente"
    return f'<span class="rst-tag {cls}">{escape(dx)}</span>'


def _fmt_ecac(raw: str) -> str:
    """Formata processo e-CAC: 12345.123456/1234-12"""
    if not raw:
        return "—"
    s = str(raw).strip().replace(".", "").replace("/", "").replace("-", "")
    if len(s) < 14:
        return str(raw).strip()
    return f"{s[:5]}.{s[5:11]}/{s[11:15]}-{s[15:17]}"


def _fmt_cnpj(raw: str) -> str:
    """Formata CNPJ: números puros sem formatação"""
    if not raw:
        return "—"
    return str(raw).strip().replace(".", "").replace("/", "").replace("-", "")


def _html_cliente(r: dict) -> str:
    cliente_raw = r.get("cliente") or "—"
    cliente = escape(str(cliente_raw).upper() if cliente_raw != "—" else "—")
    numero = r.get("numero_processo") or "—"
    ecac = r.get("processo_ecac")
    cnpj = r.get("cnpj")

    proc_parts = [f'<span>Nº {escape(str(numero))}</span>']
    if ecac and str(ecac).strip():
        ecac_fmt = _fmt_ecac(str(ecac))
        proc_parts.append(f'<span>e-CAC {escape(ecac_fmt)}</span>')
    if cnpj and str(cnpj).strip():
        cnpj_fmt = _fmt_cnpj(str(cnpj))
        proc_parts.append(f'<span>CNPJ {escape(cnpj_fmt)}</span>')

    return (
        '<div class="rst-cliente">'
        f'<div class="rst-cliente-nome">{cliente}</div>'
        f'<div class="rst-cliente-proc">{"".join(proc_parts)}</div>'
        '</div>'
    )


def _html_tags(r: dict) -> str:
    status = r.get("status") or "—"
    tags = (
        _tag_status(status)
        + _tag_divisao(r.get("divisao"))
        + _tag_desencaixe(r.get("desencaixe"))
    )
    return f'<div class="rst-tags">{tags}</div>'


def _html_meta(r: dict) -> str:
    status = r.get("status") or "—"
    valor = _br_moeda(_valor_exibicao(r))
    data_prot = _br_data(r.get("data_protocolo"))
    prazo = r.get("prazo_fatal")

    parts = [f'<div class="rst-valor">{valor}</div>']
    if data_prot != "—":
        parts.append(f'<div class="rst-datas">Protocolo: {escape(data_prot)}</div>')
    if prazo:
        prazo_txt = _br_data(prazo)
        cls = " warn" if status == "Intimação Pendente" else ""
        label = "Prazo fatal" if status == "Intimação Pendente" else "Prazo"
        parts.append(f'<div class="rst-datas{cls}">{label}: {escape(prazo_txt)}</div>')

    return f'<div class="rst-meta">{"".join(parts)}</div>'


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


def _render_timeline(rid: int) -> None:
    logs = listar_log(rid)
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
            '<div class="rst-log-item">'
            f'<div class="rst-log-head">'
            f'<span class="rst-log-icon">{icon}</span>'
            f'<span class="rst-log-tipo">{rotulo}</span>'
            f'<span class="rst-log-data">{data_txt}</span>'
            f'<span class="rst-log-user">por {usuario}</span>'
            '</div>'
            f'<div class="rst-log-text">{texto}</div>'
            '</div>'
        )
    st.markdown(f'<div class="rst-log">{"".join(items)}</div>', unsafe_allow_html=True)


def _render_popover(r: dict, user_nome: str) -> None:
    rid = r.get("id")
    status_atual = r.get("status") or "Em análise"
    idx = STATUS.index(status_atual) if status_atual in STATUS else 0

    st.markdown(
        f"**{escape(str(r.get('cliente') or '—'))}** · "
        f"Nº {escape(str(r.get('numero_processo') or '—'))}"
    )
    novo_status = st.selectbox(
        "Status", STATUS, index=idx, key=f"edit_st_{rid}"
    )
    comentario = st.text_area(
        "Observação / comentário",
        key=f"edit_cm_{rid}",
        placeholder="Ex: Resposta à intimação protocolada em 12/04 via e-CAC.",
        height=90,
    )
    if st.button("Salvar", type="primary", key=f"edit_sv_{rid}", use_container_width=True):
        mudou_algo = False
        if novo_status != status_atual:
            try:
                atualizar_restituicao(rid, {"status": novo_status}, user_nome)
                mudou_algo = True
            except Exception as e:
                st.error(f"Erro ao atualizar status: {e}")
                return
        texto = (comentario or "").strip()
        if texto:
            try:
                adicionar_comentario(rid, texto, user_nome)
                mudou_algo = True
            except Exception as e:
                st.error(f"Erro ao salvar comentário: {e}")
                return
        if mudou_algo:
            st.rerun()
        else:
            st.info("Nenhuma alteração para salvar.")

    st.markdown("###### Histórico")
    _render_timeline(rid)


def _render_popover_view(r: dict) -> None:
    rid = r.get("id")
    st.markdown(
        f"**{escape(str(r.get('cliente') or '—'))}** · "
        f"Nº {escape(str(r.get('numero_processo') or '—'))}"
    )
    status_atual = r.get("status") or "—"
    st.caption(f"Status atual: {escape(str(status_atual))}")
    st.markdown("###### Histórico")
    _render_timeline(rid)


def _render_linha(r: dict, user_nome: str) -> None:
    rid = r.get("id")
    with st.container(key=f"rst-row-{rid}"):
        c_info, c_tags, c_meta, c_acoes = st.columns([5, 3, 2, 1.2], gap="small")
        with c_info:
            st.markdown(_html_cliente(r), unsafe_allow_html=True)
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
        float(r.get("valor_corrigido") or r.get("valor_principal") or 0)
        for r in registros_status
    )
    total_txt = _br_moeda(total_valor)
    label = f"{emoji}  {status}  ·  {qtd} processo{'s' if qtd != 1 else ''}  ·  Total: {total_txt}"
    with st.expander(label, expanded=True):
        for r in registros_status:
            _render_linha(r, user_nome)


def _ordenar(registros_status: list[dict], status: str) -> list[dict]:
    if status == "Intimação Pendente":
        # prazo fatal mais próximo primeiro (None no fim)
        return sorted(
            registros_status,
            key=lambda r: (r.get("prazo_fatal") is None, r.get("prazo_fatal") or ""),
        )
    return sorted(
        registros_status,
        key=lambda r: (r.get("data_protocolo") is None, r.get("data_protocolo") or ""),
        reverse=True,
    )


def _filtros(lista: list[dict], key_prefix: str) -> list[dict]:
    """Renderiza bloco de filtros (cliente / divisão / desencaixe) e
    devolve a lista filtrada."""
    if not lista:
        return lista

    clientes_opts = sorted({str(r.get("cliente")).upper() for r in lista if r.get("cliente")})
    divisoes_opts = sorted({str(r.get("divisao")) for r in lista if r.get("divisao")})
    desencaixes_opts = sorted({str(r.get("desencaixe")) for r in lista if r.get("desencaixe")})

    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        sel_cli = col1.multiselect("Cliente", clientes_opts, key=f"{key_prefix}_cli")
        sel_div = col2.multiselect("Divisão", divisoes_opts, key=f"{key_prefix}_div")
        sel_des = col3.multiselect("Desencaixe", desencaixes_opts, key=f"{key_prefix}_des")

    filtrados = lista
    if sel_cli:
        sel_up = {c.upper() for c in sel_cli}
        filtrados = [r for r in filtrados if str(r.get("cliente") or "").upper() in sel_up]
    if sel_div:
        filtrados = [r for r in filtrados if str(r.get("divisao") or "") in sel_div]
    if sel_des:
        filtrados = [r for r in filtrados if str(r.get("desencaixe") or "") in sel_des]

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

tab_ativos, tab_concluidos, tab_indeferidos, tab_novo = st.tabs(
    [
        f"Ativos ({len(ativos)})",
        f"Concluídos ({len(concluidos)})",
        f"Indeferidos ({len(indeferidos)})",
        "➕ Novo",
    ]
)

with tab_ativos:
    _render_grupo(_filtros(ativos, "ativos"), STATUS_ATIVO, USER_NOME)

with tab_concluidos:
    _render_grupo(_filtros(concluidos, "concluidos"), STATUS_CONCLUIDO, USER_NOME)

with tab_indeferidos:
    _render_grupo(_filtros(indeferidos, "indeferidos"), STATUS_INDEFERIDO, USER_NOME)

with tab_novo:
    st.markdown("##### Adicionar novo processo de restituição")
    st.caption("Apenas o **cliente** é obrigatório. Os demais campos podem ser completados depois.")

    with st.form("form_novo_rst", clear_on_submit=True):
        col_a, col_b = st.columns(2)

        with col_a:
            cliente_in = st.text_input("Cliente *", key="nv_cliente", placeholder="Ex: MAHINDRA")
            numero_in = st.text_input("Nº do Processo", key="nv_numero", placeholder="Ex: OE1234/24")
            cnpj_in = st.text_input("CNPJ", key="nv_cnpj", placeholder="00.000.000/0000-00")
            ecac_in = st.text_input("Processo e-CAC", key="nv_ecac", placeholder="Ex: 13033.000000/2024-00")
            status_in = st.selectbox("Status", STATUS, index=STATUS.index("Em análise"), key="nv_status")
            divisao_in = st.selectbox("Divisão", ["—"] + list(DIVISOES), key="nv_divisao")
            desencaixe_in = st.selectbox("Desencaixe", ["—"] + list(DESENCAIXES), key="nv_desencaixe")

        with col_b:
            valor_principal_in = st.number_input(
                "Valor principal (R$)", min_value=0.0, step=100.0, format="%.2f", key="nv_vp"
            )
            valor_corrigido_in = st.number_input(
                "Valor corrigido (R$)", min_value=0.0, step=100.0, format="%.2f", key="nv_vc"
            )
            responsavel_in = st.text_input("Responsável", key="nv_resp")
            data_protocolo_in = st.date_input(
                "Data de protocolo", value=None, format="DD/MM/YYYY", key="nv_dp"
            )
            prazo_fatal_in = st.date_input(
                "Prazo fatal", value=None, format="DD/MM/YYYY", key="nv_pf"
            )
            termo_assinado_in = st.checkbox("Termo assinado", key="nv_termo")
            motivo_in = st.text_area(
                "Motivo de retificação", key="nv_motivo", height=80
            )

        enviar = st.form_submit_button("Criar processo", type="primary", use_container_width=True)

        if enviar:
            cliente_limpo = (cliente_in or "").strip().upper()
            if not cliente_limpo:
                st.error("Informe o cliente.")
            else:
                dados = {
                    "cliente": cliente_limpo,
                    "numero_processo": (numero_in or "").strip() or None,
                    "cnpj": (cnpj_in or "").strip() or None,
                    "processo_ecac": (ecac_in or "").strip() or None,
                    "status": status_in,
                    "divisao": divisao_in if divisao_in != "—" else None,
                    "desencaixe": desencaixe_in if desencaixe_in != "—" else None,
                    "valor_principal": valor_principal_in or None,
                    "valor_corrigido": valor_corrigido_in or None,
                    "responsavel": (responsavel_in or "").strip() or None,
                    "data_protocolo": data_protocolo_in,
                    "prazo_fatal": prazo_fatal_in,
                    "termo_assinado": bool(termo_assinado_in),
                    "motivo_retificacao": (motivo_in or "").strip() or None,
                }
                try:
                    novo_id = criar_restituicao(dados, USER_NOME)
                except Exception as e:
                    st.error(f"Erro ao criar processo: {e}")
                else:
                    st.success(
                        f"Processo **{dados['cliente']}** "
                        f"({dados.get('numero_processo') or f'#{novo_id}'}) "
                        f"criado com status **{status_in}**."
                    )
                    st.rerun()


st.caption(
    "Use o botão **✎ Editar** em cada processo para trocar o status ou adicionar uma observação/comentário."
)
