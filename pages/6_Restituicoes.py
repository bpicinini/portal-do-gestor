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
    criar_restituicao,
    intimacoes_pendentes,
    listar_restituicoes,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


garantir_autenticado()
aplicar_estilos_globais()


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
    details.rst-section {
        background: var(--surface, #fffdf8);
        border: 1px solid var(--line, #e3d8c5);
        border-radius: 18px;
        padding: 0.2rem 1rem 0.4rem 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow, 0 8px 22px rgba(35,64,85,0.06));
    }
    details.rst-section[open] {
        padding-top: 0.7rem;
    }
    details.rst-section > summary {
        list-style: none;
        cursor: pointer;
        user-select: none;
    }
    details.rst-section > summary::-webkit-details-marker { display: none; }
    details.rst-section > summary::marker { content: ""; }
    .rst-section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.55rem 0.1rem 0.55rem 0.1rem;
    }
    details.rst-section[open] .rst-section-header {
        padding-bottom: 0.7rem;
        border-bottom: 1px dashed var(--line, #e3d8c5);
        margin-bottom: 0.55rem;
    }
    .rst-chevron {
        color: var(--muted, #6f7a84);
        font-size: 0.75rem;
        transition: transform 0.15s ease;
        flex: 0 0 auto;
        width: 12px;
        display: inline-block;
    }
    details.rst-section[open] .rst-chevron { transform: rotate(90deg); }
    .rst-section-dot {
        width: 10px; height: 10px; border-radius: 50%;
        flex: 0 0 auto;
    }
    .rst-section-title {
        font-weight: 800;
        font-size: 0.98rem;
        color: var(--navy, #234055);
        letter-spacing: -0.01em;
    }
    .rst-section-count {
        background: rgba(35,64,85,0.07);
        color: var(--navy, #234055);
        border-radius: 999px;
        padding: 0.08rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 800;
    }
    .rst-section-total {
        margin-left: auto;
        color: var(--muted, #6f7a84);
        font-size: 0.82rem;
        font-weight: 700;
    }
    .rst-section-total strong { color: var(--navy, #234055); }

    .rst-row {
        display: grid;
        grid-template-columns: 1.4fr 2.2fr 1fr;
        gap: 0.85rem;
        padding: 0.55rem 0.2rem;
        border-bottom: 1px solid rgba(227,216,197,0.4);
        align-items: center;
    }
    .rst-row:last-child { border-bottom: none; }

    .rst-cliente { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
    .rst-cliente-nome {
        color: var(--navy, #234055);
        font-weight: 700;
        font-size: 0.92rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .rst-cliente-proc {
        color: var(--muted, #6f7a84);
        font-size: 0.74rem;
        font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
        letter-spacing: -0.01em;
    }
    .rst-cliente-proc span + span::before {
        content: "·";
        margin: 0 0.35rem;
        color: var(--line, #e3d8c5);
    }

    .rst-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; }
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

    .rst-tag-div-leader  { background: #223645; color: #f4e8ca; border-color: #1a2a37; }
    .rst-tag-div-winning { background: #6e2935; color: #f4d6dc; border-color: #4f1c24; }

    .rst-tag-desc-3s {
        background: linear-gradient(135deg, #d59a2b 0%, #bf7f16 100%);
        color: #fff;
        border-color: #a96b0f;
        text-transform: uppercase;
        box-shadow: 0 2px 6px rgba(191,127,22,0.25);
    }
    .rst-tag-desc-cliente { background: #eef1f4; color: #6f7a84; border-color: #dce1e7; }

    .rst-meta {
        display: flex; flex-direction: column; gap: 0.15rem;
        align-items: flex-end;
        text-align: right;
        min-width: 0;
    }
    .rst-valor {
        color: var(--navy, #234055);
        font-weight: 800;
        font-size: 0.95rem;
        letter-spacing: -0.01em;
    }
    .rst-datas {
        color: var(--muted, #6f7a84);
        font-size: 0.72rem;
        font-weight: 600;
    }
    .rst-datas.warn { color: #a2322a; font-weight: 800; }

    @media (max-width: 900px) {
        .rst-row {
            grid-template-columns: 1fr;
            gap: 0.4rem;
            padding: 0.6rem 0.1rem;
        }
        .rst-meta { align-items: flex-start; text-align: left; }
        .rst-section-total { font-size: 0.76rem; }
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


def _render_row(r: dict) -> str:
    cliente_raw = r.get("cliente") or "—"
    cliente = escape(str(cliente_raw).upper() if cliente_raw != "—" else "—")
    numero = r.get("numero_processo") or "—"
    ecac = r.get("processo_ecac")
    cnpj = r.get("cnpj")

    proc_parts = [f'<span>Nº {escape(str(numero))}</span>']
    if ecac and str(ecac).strip():
        proc_parts.append(f'<span>e-CAC {escape(str(ecac))}</span>')
    if cnpj and str(cnpj).strip():
        proc_parts.append(f'<span>CNPJ {escape(str(cnpj))}</span>')

    status = r.get("status") or "—"
    tags = (
        _tag_status(status)
        + _tag_divisao(r.get("divisao"))
        + _tag_desencaixe(r.get("desencaixe"))
    )

    valor = _br_moeda(_valor_exibicao(r))
    data_prot = _br_data(r.get("data_protocolo"))

    prazo = r.get("prazo_fatal")
    prazo_html = ""
    if prazo:
        prazo_txt = _br_data(prazo)
        cls = " warn" if status == "Intimação Pendente" else ""
        label = "Prazo fatal" if status == "Intimação Pendente" else "Prazo"
        prazo_html = f'<div class="rst-datas{cls}">{label}: {escape(prazo_txt)}</div>'

    data_html = ""
    if data_prot != "—":
        data_html = f'<div class="rst-datas">Protocolo: {escape(data_prot)}</div>'

    return (
        '<div class="rst-row">'
        f'<div class="rst-cliente">'
        f'<div class="rst-cliente-nome">{cliente}</div>'
        f'<div class="rst-cliente-proc">{"".join(proc_parts)}</div>'
        '</div>'
        f'<div class="rst-tags">{tags}</div>'
        f'<div class="rst-meta">'
        f'<div class="rst-valor">{valor}</div>'
        f'{data_html}{prazo_html}'
        '</div>'
        '</div>'
    )


def _render_secao(status: str, registros_status: list[dict], aberto: bool = True) -> str:
    cores = STATUS_CORES.get(status, {"bg": "#eef1f4", "fg": "#4a5866", "bd": "#d8dee5"})
    qtd = len(registros_status)
    total_valor = sum(
        float(r.get("valor_corrigido") or r.get("valor_principal") or 0)
        for r in registros_status
    )
    total_txt = _br_moeda(total_valor)
    rows_html = "".join(_render_row(r) for r in registros_status)
    open_attr = " open" if aberto else ""
    return (
        f'<details class="rst-section"{open_attr}>'
        '<summary><div class="rst-section-header">'
        '<span class="rst-chevron">▶</span>'
        f'<span class="rst-section-dot" style="background:{cores["fg"]};"></span>'
        f'<span class="rst-section-title">{escape(status)}</span>'
        f'<span class="rst-section-count">{qtd}</span>'
        f'<span class="rst-section-total">Total: <strong>{total_txt}</strong></span>'
        '</div></summary>'
        f'{rows_html}'
        '</details>'
    )


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


def _render_grupo(lista: list[dict], status_permitidos) -> None:
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
        st.markdown(_render_secao(status, subset), unsafe_allow_html=True)
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
    _render_grupo(_filtros(ativos, "ativos"), STATUS_ATIVO)

with tab_concluidos:
    _render_grupo(_filtros(concluidos, "concluidos"), STATUS_CONCLUIDO)

with tab_indeferidos:
    _render_grupo(_filtros(indeferidos, "indeferidos"), STATUS_INDEFERIDO)

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
                user = obter_usuario_atual() or {}
                user_nome = user.get("nome") or user.get("email") or "desconhecido"
                try:
                    novo_id = criar_restituicao(dados, user_nome)
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
    "Edição inline na tabela e timeline de comentários chegam nos próximos passos."
)
