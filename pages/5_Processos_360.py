"""Processos 360 — Dashboard de processos de importação."""

import re
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.processos360 import (
    STATUS_ORDEM,
    _br,
    _br_moeda,
    calcular_alertas,
    carregar_meta,
    dados_existem,
    listar_backups,
    obter_processos,
    salvar_upload,
    validar_csv,
)
from utils.ui import aplicar_estilos_globais, is_dark_mode, renderizar_cabecalho_pagina
from utils import exportacao as exp

_DARK = is_dark_mode()
_BASE_DARK_TEXT = "#d4dae2" if _DARK else "#111111"
_MUTED_TEXT = "#8b949e" if _DARK else "#6E6E73"
_CARD_BG = "linear-gradient(135deg, #1b3245, #213a4f)" if _DARK else "linear-gradient(135deg, rgba(245,245,247,0.96), rgba(250,250,252,0.96))"
_CARD_BORDER = "#30363d" if _DARK else "#E5E5EA"
_CARD_SHADOW = "none" if _DARK else "0 14px 35px rgba(35, 64, 85, 0.08)"

COLOR_NAVY = _BASE_DARK_TEXT
COLOR_NAVY_SOFT = "#36586f"
COLOR_GOLD = "#C9A67A"
COLOR_GREEN = "#5e8668"
COLOR_RED = "#b5423a"

STATUS_CORES = {
    "Pré-embarque": "#7ea6c7",
    "Embarque": "#4a8ab5",
    "Chegada": "#8E8E93",
    "Registrado/Ag.Desembaraço": "#8E8E93",
    "Carregamento": "#5e8668",
    "Encerramento": _BASE_DARK_TEXT,
}

MODALIDADE_CORES = {
    "OCEANFREIGHT / FCL": _BASE_DARK_TEXT,
    "OCEANFREIGHT / LCL": "#4a8ab5",
    "AIRFREIGHT": "#8E8E93",
    "RODOVIÁRIO": "#5e8668",
    "BREAK BULK": "#8b5e3c",
    "MARÍTIMO / RODOVIÁRIO": "#7ea6c7",
    "AÉREO / MARÍTIMO": "#8E8E93",
    "FERROVIÁRIO": "#6E6E73",
}

TIPO_OP_CORES = {
    "Importação Própria": "#4a8ab5",
    "Importação por Conta e Ordem": "#8E8E93",
    "Encomenda": "#111111",
}

# Rótulos e cores para Direto / CO3 / Encomenda (usados em cards e tabelas)
TIPO_LABELS = {
    "Importação Própria": "Direto",
    "Importação por Conta e Ordem": "CO3",
    "Encomenda": "Encomenda",
}
TIPO_CORES = {
    "Direto":    "#4a8ab5",
    "CO3":       "#8E8E93",
    "Encomenda": "#111111",
}
TIPOS_ORDEM = ["Direto", "CO3", "Encomenda"]


def _consolidar_cliente(nome: str) -> str:
    """Remove sufixos de CNPJ, filial e parênteses de referência dos nomes de clientes.

    Exemplos:
        'ANJO TINTAS - 0001-58'      → 'ANJO TINTAS'
        'CALCADOS RAMARIM (FILIAL RS)' → 'CALCADOS RAMARIM'
        'CALCADOS RAMARIM (MATRIZ - BA)' → 'CALCADOS RAMARIM'
        'COFRAG - 0002-55'           → 'COFRAG'
        'INTEXCO 0003-60 (ITAJAÍ)'   → 'INTEXCO'
        'SANKEM FILIAL 02-66'        → 'SANKEM FILIAL'
        'GRUPAR AUTOPECAS (SC)'      → 'GRUPAR AUTOPECAS'
    """
    if not isinstance(nome, str):
        return nome
    # 1. Remove parênteses no final: "(SC)", "(FILIAL RS)", "(MATRIZ - BA)", "(003)"
    nome = re.sub(r'\s*\([^)]*\)\s*$', '', nome)
    # 2. Remove sufixo " - DIGITS" (fragmento de CNPJ): "- 0001-58", "- 0002-55"
    nome = re.sub(r'\s*-\s*\d[\d\-/\.]*\s*$', '', nome)
    # 3. Remove código numérico solto no final: "0003-60", "02-66"
    nome = re.sub(r'\s+\d[\d\-]+\s*$', '', nome)
    return nome.strip()

garantir_autenticado()
aplicar_estilos_globais()

alt.renderers.set_embed_options(
    formatLocale={
        "decimal": ",",
        "thousands": ".",
        "grouping": [3],
        "currency": ["R$ ", ""],
    }
)


# ── Cabeçalho ────────────────────────────────────────────────────────

meta = carregar_meta()
if meta:
    badge_text = f"{meta['total_registros']} processos"
elif dados_existem():
    df_badge = obter_processos()
    badge_text = f"{len(df_badge)} processos" if not df_badge.empty else "Sem dados"
else:
    badge_text = "Sem dados"

renderizar_cabecalho_pagina(
    "Visão 360",
    "Visão consolidada dos processos em andamento por departamento.",
    badge=badge_text,
)


# ── Abas de departamento ──────────────────────────────────────────────

tab_importacao, tab_exportacao, tab_agenciamento = st.tabs(
    ["Importação", "Exportação", "Agenciamento"]
)

with tab_importacao:
    # ── Sub-abas de Importação ────────────────────────────────────────

    _TAB_NAMES = ["Visão Geral", "Analistas", "Clientes", "Alertas e Prazos", "Tabela", "Upload"]
    _qp_aba = st.query_params.get("aba", "")
    _qp_alerta = st.query_params.get("alerta", "")

    tab_geral, tab_analista, tab_clientes, tab_alertas, tab_tabela, tab_upload = st.tabs(
        _TAB_NAMES
    )

    # Deep-link: se veio da home com ?aba=alertas, auto-selecionar a aba via JS
    if _qp_aba == "alertas":
        _tab_idx = _TAB_NAMES.index("Alertas e Prazos")
        st.markdown(
            f"""<script>
            setTimeout(function() {{
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                if (tabs && tabs[{_tab_idx}]) tabs[{_tab_idx}].click();
            }}, 300);
            </script>""",
            unsafe_allow_html=True,
        )


def _msg_sem_dados():
    st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")


st.markdown(
    """
    <style>
    .tag-encomenda-fix {
        background: #111111 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _tag_html(tipo):
    """Gera HTML de tag colorida para tipo de operação (Direto/CO3/Encomenda)."""
    cor = TIPO_CORES.get(tipo, "#6E6E73")
    txt = _tag_text_color(tipo)
    return (
        f'<span class="{_tag_force_class(tipo)}" style="background:{cor};color:{txt};{_tag_force_style(tipo)}border-radius:5px;'
        f'padding:2px 7px;font-size:0.62rem;font-weight:800;'
        f'letter-spacing:0.04em;margin-left:4px;">{tipo}</span>'
    )


def _tag_text_color(tipo: str) -> str:
    return "#ffffff !important"


def _tag_force_style(tipo: str) -> str:
    if str(tipo or "").strip().lower() == "encomenda":
        return "background:#111111 !important;color:#ffffff !important;"
    return ""


def _tag_force_class(tipo: str) -> str:
    return "tag-encomenda-fix" if str(tipo or "").strip().lower() == "encomenda" else ""


def _filtro_multiselect(df, coluna, label, key):
    """Cria multiselect e retorna valores selecionados."""
    opcoes = sorted(df[coluna].dropna().unique().tolist())
    return st.multiselect(label, opcoes, key=key)


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 1: VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════

with tab_geral:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            alertas = calcular_alertas(df)
            total = len(df)

            # ── KPIs: Total + todos os status com percentual ──
            st.markdown(
                f"""
                <div style="
                    background: {_CARD_BG};
                    border: 1px solid {_CARD_BORDER}; border-radius: 20px;
                    padding: 1rem 1.4rem; margin-bottom: 1rem;
                    box-shadow: {_CARD_SHADOW};
                    display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center;
                ">
                    <div style="flex: 0 0 auto; margin-right: 0.8rem;">
                        <span style="color: #6E6E73; font-size: 0.7rem; text-transform: uppercase; font-weight: 800;">Total</span><br/>
                        <span style="color: {_BASE_DARK_TEXT}; font-size: 1.8rem; font-weight: 800;">{total:,}</span>
                    </div>
                    {"".join(f'''
                    <div style="
                        flex: 1 1 0; min-width: 120px;
                        background: rgba(255,255,255,0.06); border: 1px solid {_CARD_BORDER}; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid {STATUS_CORES.get(s, '#ccc')};
                    ">
                        <div style="color: #6E6E73; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{s}</div>
                        <div style="color: {_BASE_DARK_TEXT}; font-size: 1.25rem; font-weight: 800;">{len(df[df["Status"] == s])}</div>
                        <div style="color: {STATUS_CORES.get(s, "#6E6E73")}; font-size: 0.78rem; font-weight: 700;">{len(df[df["Status"] == s]) / total * 100:.1f}%</div>
                    </div>
                    ''' for s in STATUS_ORDEM)}
                </div>
                """.replace(",}", "}").replace("\n                    \n", "\n"),
                unsafe_allow_html=True,
            )

            st.divider()

            # ── Gráficos ──
            col_esq, col_dir = st.columns(2)

            with col_esq:
                # Distribuição por Status
                st.caption("**Distribuição por Status**")
                df_status = df["Status"].value_counts().reset_index()
                df_status.columns = ["Status", "Quantidade"]
                df_status["Status"] = pd.Categorical(df_status["Status"], categories=STATUS_ORDEM, ordered=True)
                df_status = df_status.sort_values("Status")

                chart_status = (
                    alt.Chart(df_status)
                    .mark_bar(cornerRadiusEnd=8)
                    .encode(
                        x=alt.X("Quantidade:Q", title="Processos"),
                        y=alt.Y("Status:N", sort=STATUS_ORDEM, title=None, axis=alt.Axis(labelLimit=250)),
                        color=alt.Color(
                            "Status:N",
                            scale=alt.Scale(domain=list(STATUS_CORES.keys()), range=list(STATUS_CORES.values())),
                            legend=None,
                        ),
                        tooltip=[alt.Tooltip("Status:N"), alt.Tooltip("Quantidade:Q", format=",d")],
                    )
                    .properties(height=220)
                )
                st.altair_chart(chart_status, use_container_width=True)

            with col_dir:
                # Distribuição por Modalidade (cores distintas)
                st.caption("**Distribuição por Modalidade**")
                if "Modalidade" in df.columns:
                    df_mod = df["Modalidade"].value_counts().reset_index()
                    df_mod.columns = ["Modalidade", "Quantidade"]
                    # Top 4 + Outros
                    if len(df_mod) > 4:
                        _top4 = df_mod.head(4)
                        _outros = pd.DataFrame([{"Modalidade": "Outros", "Quantidade": df_mod.iloc[4:]["Quantidade"].sum()}])
                        df_mod = pd.concat([_top4, _outros], ignore_index=True)
                    mod_domain = df_mod["Modalidade"].tolist()
                    mod_range = [MODALIDADE_CORES.get(m, "#6E6E73") for m in mod_domain]
                    _total_mod = df_mod["Quantidade"].sum()
                    df_mod["Pct"] = (df_mod["Quantidade"] / _total_mod * 100).round(1)
                    df_mod["Label"] = df_mod["Pct"].apply(lambda v: f"{v:.1f}%")
                    pie_mod = (
                        alt.Chart(df_mod)
                        .mark_arc(innerRadius=0, outerRadius=90, cornerRadius=3)
                        .encode(
                            theta=alt.Theta("Quantidade:Q", stack=True),
                            color=alt.Color(
                                "Modalidade:N",
                                scale=alt.Scale(domain=mod_domain, range=mod_range),
                                legend=alt.Legend(title=None, orient="bottom", columns=3),
                            ),
                            tooltip=[
                                alt.Tooltip("Modalidade:N"),
                                alt.Tooltip("Quantidade:Q", format=",d"),
                                alt.Tooltip("Pct:Q", title="%", format=".1f"),
                            ],
                        )
                    )
                    text_mod = (
                        alt.Chart(df_mod)
                        .mark_text(radius=110, size=12, fontWeight="bold")
                        .encode(
                            theta=alt.Theta("Quantidade:Q", stack=True),
                            text="Label:N",
                            color=alt.Color(
                                "Modalidade:N",
                                scale=alt.Scale(domain=mod_domain, range=mod_range),
                                legend=None,
                            ),
                        )
                    )
                    st.altair_chart(
                        (pie_mod + text_mod).properties(height=240, padding={"top": 20, "bottom": 10}),
                        use_container_width=True,
                    )

            col_esq2, col_dir2 = st.columns(2)

            with col_esq2:
                # Distribuição por Account
                st.caption("**Distribuição por Account**")
                df_acc = df["Account"].value_counts().reset_index()
                df_acc.columns = ["Account", "Quantidade"]
                # Gerar cores alternando entre palette
                acc_palette = [_BASE_DARK_TEXT, "#4a8ab5", "#C9A67A", "#5e8668", "#8E8E93", "#7ea6c7", "#8b5e3c", "#b5423a", "#6E6E73", "#36586f"]
                acc_domain = df_acc["Account"].tolist()
                acc_range = [acc_palette[i % len(acc_palette)] for i in range(len(acc_domain))]
                chart_acc = (
                    alt.Chart(df_acc)
                    .mark_bar(cornerRadiusEnd=8)
                    .encode(
                        x=alt.X("Quantidade:Q", title="Processos"),
                        y=alt.Y("Account:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                        color=alt.Color(
                            "Account:N",
                            scale=alt.Scale(domain=acc_domain, range=acc_range),
                            legend=None,
                        ),
                        tooltip=[alt.Tooltip("Account:N"), alt.Tooltip("Quantidade:Q", format=",d")],
                    )
                    .properties(height=max(220, len(acc_domain) * 22))
                )
                st.altair_chart(chart_acc, use_container_width=True)

            with col_dir2:
                # Distribuição por Tipo de Operação (cores distintas)
                st.caption("**Distribuição por Tipo de Operação**")
                if "Tipo de Operação" in df.columns:
                    df_tipo = df["Tipo de Operação"].value_counts().reset_index()
                    df_tipo.columns = ["Tipo", "Quantidade"]
                    # Top 4 + Outros
                    if len(df_tipo) > 4:
                        _top4t = df_tipo.head(4)
                        _outrost = pd.DataFrame([{"Tipo": "Outros", "Quantidade": df_tipo.iloc[4:]["Quantidade"].sum()}])
                        df_tipo = pd.concat([_top4t, _outrost], ignore_index=True)
                    tipo_domain = df_tipo["Tipo"].tolist()
                    tipo_range = [TIPO_OP_CORES.get(t, "#6E6E73") for t in tipo_domain]
                    _total_tipo = df_tipo["Quantidade"].sum()
                    df_tipo["Pct"] = (df_tipo["Quantidade"] / _total_tipo * 100).round(1)
                    df_tipo["Label"] = df_tipo["Pct"].apply(lambda v: f"{v:.1f}%")
                    pie_tipo = (
                        alt.Chart(df_tipo)
                        .mark_arc(innerRadius=0, outerRadius=90, cornerRadius=3)
                        .encode(
                            theta=alt.Theta("Quantidade:Q"),
                            color=alt.Color(
                                "Tipo:N",
                                scale=alt.Scale(domain=tipo_domain, range=tipo_range),
                                legend=alt.Legend(title=None, orient="bottom"),
                            ),
                            tooltip=[alt.Tooltip("Tipo:N"), alt.Tooltip("Quantidade:Q", format=",d"), alt.Tooltip("Pct:Q", format=".1f", title="%")],
                        )
                    )
                    text_tipo = (
                        alt.Chart(df_tipo)
                        .mark_text(radius=110, size=12, fontWeight="bold")
                        .encode(
                            theta=alt.Theta("Quantidade:Q", stack=True),
                            text="Label:N",
                            color=alt.Color("Tipo:N", scale=alt.Scale(domain=tipo_domain, range=tipo_range), legend=None),
                        )
                    )
                    st.altair_chart(
                        (pie_tipo + text_tipo).properties(height=240, padding={"top": 20, "bottom": 10}),
                        use_container_width=True,
                    )

            # Timeline de aberturas por mês
            if "Abertura" in df.columns:
                st.divider()
                st.caption("**Processos abertos por mês**")
                df_ab = df[df["Abertura"].notna()].copy()
                df_ab["Mês"] = df_ab["Abertura"].dt.to_period("M").astype(str)
                df_timeline = df_ab["Mês"].value_counts().sort_index().reset_index()
                df_timeline.columns = ["Mês", "Aberturas"]

                chart_timeline = (
                    alt.Chart(df_timeline)
                    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=COLOR_NAVY)
                    .encode(
                        x=alt.X("Mês:N", sort=None, title=None, axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y("Aberturas:Q", title="Processos Abertos"),
                        tooltip=[alt.Tooltip("Mês:N"), alt.Tooltip("Aberturas:Q", format=",d")],
                    )
                    .properties(height=220)
                )
                st.altair_chart(chart_timeline, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 2: VISÃO POR ANALISTA
# ══════════════════════════════════════════════════════════════════════

with tab_analista:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            # Coluna Tipo mapeada (Direto / CO3 / Encomenda)
            _tem_tipo = "Tipo de Operação" in df.columns
            df = df.copy()
            if _tem_tipo:
                df["_Tipo"] = df["Tipo de Operação"].map(TIPO_LABELS).fillna("Outro")

            # ── Filtro por tipo (tags clicáveis) ─────────────────────────
            # Renderizar filtro ANTES de qualquer agregação
            _col_hdr, _col_filt = st.columns([2, 3])
            with _col_filt:
                if _tem_tipo:
                    _fcols = st.columns(len(TIPOS_ORDEM) + 1)
                    filtro_tipo = []
                    for _fi, _ft in enumerate(TIPOS_ORDEM):
                        with _fcols[_fi]:
                            _cor_tag = TIPO_CORES[_ft]
                            if st.checkbox(
                                _ft,
                                key=f"filtro_tag_{_ft}",
                                value=False,
                            ):
                                filtro_tipo.append(_ft)
                            st.markdown(
                                f'<div style="background:{_cor_tag};height:4px;border-radius:2px;margin-top:-10px;"></div>',
                                unsafe_allow_html=True,
                            )
                else:
                    filtro_tipo = []

            # Aplicar filtro no DataFrame inteiro (tudo reflete o filtro)
            if filtro_tipo:
                df = df[df["_Tipo"].isin(filtro_tipo)]

            # Agregar com dados já filtrados
            analistas = df.groupby("Account").agg(
                processos=("Processo", "count"),
                clientes=("Cliente", "nunique"),
                valor_aduaneiro=("Valor Aduaneiro", "sum"),
            ).reset_index().sort_values("processos", ascending=False)

            # Separar analistas normais (cards) dos que vão para auditoria
            _LIMIAR_AUDITORIA = 10
            _analistas_normais = analistas[analistas["processos"] >= _LIMIAR_AUDITORIA]
            _analistas_baixo   = analistas[analistas["processos"] <  _LIMIAR_AUDITORIA]

            with _col_hdr:
                _lbl_filtro = f" ({' + '.join(filtro_tipo)})" if filtro_tipo else ""
                st.markdown(f"#### {len(_analistas_normais)} Analistas{_lbl_filtro}")

            # ── Métricas resumo — baseadas apenas nos analistas com cards ─
            _total_proc   = int(_analistas_normais["processos"].sum())
            _media_proc   = round(_total_proc / len(_analistas_normais), 1) if len(_analistas_normais) else 0
            _mediana_proc = round(_analistas_normais["processos"].median(), 1) if len(_analistas_normais) else 0
            _max_proc     = int(_analistas_normais["processos"].max()) if len(_analistas_normais) else 0

            _mc1, _mc2, _mc3, _mc4, _mc5 = st.columns(5)
            _mc1.metric("Total de processos", _total_proc)
            _mc2.metric("Média por analista", _media_proc)
            _mc3.metric("Mediana", _mediana_proc)
            _mc4.metric("Maior carteira", _max_proc)
            _mc5.metric("Menor carteira (≥10)", int(_analistas_normais["processos"].min()) if len(_analistas_normais) else 0)


            _hoje = pd.Timestamp.now().normalize()
            _status_ativos_sempre = {"Encerramento", "Carregamento", "Registrado/Ag.Desembaraço", "Chegada"}
            _mask_ativos = df["Status"].isin(_status_ativos_sempre)
            if "Prev. Chegada" in df.columns:
                _dias_chegada = (df["Prev. Chegada"] - _hoje).dt.days
                _mask_embarque_ativo = (
                    (df["Status"] == "Embarque")
                    & _dias_chegada.notna()
                    & (_dias_chegada >= 0)
                    & (_dias_chegada <= 10)
                )
            else:
                _mask_embarque_ativo = pd.Series(False, index=df.index)
            _df_ativos = df[_mask_ativos | _mask_embarque_ativo]
            _ativos_por_analista = _df_ativos.groupby("Account").size().rename("ativos")

            # Tipos por analista (para tags)
            if _tem_tipo:
                _tipos_por_analista = (
                    df.groupby("Account")["_Tipo"]
                    .apply(lambda s: set(s) & set(TIPOS_ORDEM))
                    .to_dict()
                )
            else:
                _tipos_por_analista = {}

            _analistas_filtrados = _analistas_normais

            # ── Cards (analistas com ≥ 10 processos) ──────────────────────
            cols_por_linha = 3
            for i in range(0, len(_analistas_filtrados), cols_por_linha):
                cols = st.columns(cols_por_linha)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx >= len(_analistas_filtrados):
                        break
                    row = _analistas_filtrados.iloc[idx]
                    with col:
                        df_an = df[df["Account"] == row["Account"]]
                        status_counts = df_an["Status"].value_counts()
                        status_pills = " | ".join(
                            f"{s}: {status_counts.get(s, 0)}"
                            for s in STATUS_ORDEM
                            if status_counts.get(s, 0) > 0
                        )
                        n_ativos = int(_ativos_por_analista.get(row["Account"], 0))
                        tipos_an = _tipos_por_analista.get(row["Account"], set())
                        tags_html = "".join(
                            _tag_html(t) for t in TIPOS_ORDEM if t in tipos_an
                        )

                        st.markdown(
                            f"""
                            <div style="
                                background: {_CARD_BG};
                                border: 1px solid {_CARD_BORDER};
                                border-radius: 18px;
                                padding: 1rem 1.2rem;
                                margin-bottom: 0.2rem;
                                box-shadow: {_CARD_SHADOW};
                            ">
                                <div style="font-weight: 800; color: {_BASE_DARK_TEXT}; font-size: 1.05rem;
                                            margin-bottom: 0.4rem; display:flex; align-items:center; flex-wrap:wrap; gap:2px;">
                                    {row['Account']}{tags_html}
                                </div>
                                <div style="display: flex; gap: 1.2rem; margin-bottom: 0.5rem;">
                                    <div>
                                        <span style="color: {_MUTED_TEXT}; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Processos</span><br/>
                                        <span style="color: {_BASE_DARK_TEXT}; font-size: 1.3rem; font-weight: 800;">{int(row['processos'])}</span>
                                    </div>
                                    <div>
                                        <span style="color: {_MUTED_TEXT}; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Ativos</span><br/>
                                        <span style="color: {_BASE_DARK_TEXT}; font-size: 1.3rem; font-weight: 800;">{n_ativos}</span>
                                    </div>
                                    <div>
                                        <span style="color: {_MUTED_TEXT}; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Clientes</span><br/>
                                        <span style="color: #5e8668; font-size: 1.3rem; font-weight: 800;">{int(row['clientes'])}</span>
                                    </div>
                                    <div>
                                        <span style="color: {_MUTED_TEXT}; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Valor Aduaneiro</span><br/>
                                        <span style="color: {_BASE_DARK_TEXT}; font-size: 1rem; font-weight: 700;">{_br_moeda(row['valor_aduaneiro'], 0)}</span>
                                    </div>
                                </div>
                                <div style="font-size: 0.75rem; color: {_MUTED_TEXT};">{status_pills}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Expander com breakdown por cliente e tipo
                        with st.expander("Ver clientes", expanded=False):
                            # df_an já está filtrado pelo tipo (filtro aplicado no df global)
                            df_an_f = df_an.copy()
                            df_an_f["_ClienteBase"] = df_an_f["Cliente"].apply(_consolidar_cliente)

                            # Agregar: processos + conjunto de tipos por cliente consolidado
                            if _tem_tipo:
                                df_cl_agg = (
                                    df_an_f.groupby("_ClienteBase")
                                    .agg(
                                        processos=("Processo", "count"),
                                        tipos=("_Tipo", lambda s: [
                                            t for t in TIPOS_ORDEM if t in set(s)
                                        ]),
                                    )
                                    .reset_index()
                                    .sort_values("processos", ascending=False)
                                )
                            else:
                                df_cl_agg = (
                                    df_an_f.groupby("_ClienteBase")
                                    .size()
                                    .reset_index(name="processos")
                                    .sort_values("processos", ascending=False)
                                )
                                df_cl_agg["tipos"] = [[]] * len(df_cl_agg)

                            # Renderizar como tabela HTML com tags coloridas
                            rows_html = ""
                            for _, cl_row in df_cl_agg.iterrows():
                                tags_cl = " ".join(
                                    f'<span class="{_tag_force_class(t)}" style="background:{TIPO_CORES[t]};color:{_tag_text_color(t)};{_tag_force_style(t)}'
                                    f'border-radius:4px;padding:1px 6px;font-size:0.6rem;'
                                    f'font-weight:800;letter-spacing:0.03em;">{t}</span>'
                                    for t in cl_row["tipos"]
                                )
                                rows_html += (
                                    f'<tr style="border-bottom:1px solid #E5E5EA;">'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;color:#111111;">'
                                    f'{cl_row["_ClienteBase"]}</td>'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;text-align:center;'
                                    f'color:#111111;font-weight:700;">{int(cl_row["processos"])}</td>'
                                    f'<td style="padding:5px 8px;">{tags_cl}</td>'
                                    f'</tr>'
                                )
                            st.markdown(
                                f'<table style="width:100%;border-collapse:collapse;">'
                                f'<thead><tr style="background:#FAFAFA;">'
                                f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6E6E73;text-transform:uppercase;font-weight:700;">Cliente</th>'
                                f'<th style="text-align:center;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6E6E73;text-transform:uppercase;font-weight:700;">Proc.</th>'
                                f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6E6E73;text-transform:uppercase;font-weight:700;">Tipo</th>'
                                f'</tr></thead><tbody>{rows_html}</tbody></table>',
                                unsafe_allow_html=True,
                            )

            # ── Analistas com < 10 processos — lista para auditoria ───────
            if not _analistas_baixo.empty:
                st.divider()
                st.markdown(
                    f"**⚠ {len(_analistas_baixo)} analista(s) com menos de {_LIMIAR_AUDITORIA} processos** "
                    "— provável preenchimento incorreto. Verifique os números abaixo:",
                    unsafe_allow_html=False,
                )
                for _, _ab_row in _analistas_baixo.iterrows():
                    _procs_list = sorted(
                        df[df["Account"] == _ab_row["Account"]]["Processo"].dropna().astype(str).tolist()
                    )
                    _procs_str = " · ".join(_procs_list) if _procs_list else "—"
                    st.markdown(
                        f"- **{_ab_row['Account']}** — {int(_ab_row['processos'])} processo(s): "
                        f"`{_procs_str}`"
                    )

            st.divider()

            n_analistas = df["Account"].nunique()
            _sort_desc = alt.EncodingSortField(field="Quantidade", op="sum", order="descending")

            # ── Gráfico 1: por Status ─────────────────────────────────────
            st.caption("**Distribuição de processos por Analista e Status**")
            df_pivot = df.groupby(["Account", "Status"]).size().reset_index(name="Quantidade")
            df_pivot["Status"] = pd.Categorical(df_pivot["Status"], categories=STATUS_ORDEM, ordered=True)

            chart_analista = (
                alt.Chart(df_pivot)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("Quantidade:Q", title="Processos", stack="zero"),
                    y=alt.Y("Account:N", sort=_sort_desc, title=None, axis=alt.Axis(labelLimit=250)),
                    color=alt.Color(
                        "Status:N",
                        scale=alt.Scale(domain=list(STATUS_CORES.keys()), range=list(STATUS_CORES.values())),
                        legend=alt.Legend(title="Status"),
                    ),
                    tooltip=[
                        alt.Tooltip("Account:N", title="Analista"),
                        alt.Tooltip("Status:N"),
                        alt.Tooltip("Quantidade:Q", format=",d"),
                    ],
                )
                .properties(height=max(350, n_analistas * 28))
            )
            st.altair_chart(chart_analista, use_container_width=True)

            # ── Gráfico 2: por Tipo de Operação ──────────────────────────
            if _tem_tipo:
                st.caption("**Distribuição por Tipo de Operação por Analista**")

                # Reutiliza coluna _Tipo já calculada e constantes do módulo
                df_tipo_piv = df.groupby(["Account", "_Tipo"]).size().reset_index(name="Quantidade")
                df_tipo_piv = df_tipo_piv[df_tipo_piv["_Tipo"].isin(TIPOS_ORDEM)]
                df_tipo_piv = df_tipo_piv.rename(columns={"_Tipo": "Tipo"})

                tipo_domain = TIPOS_ORDEM
                tipo_range  = [TIPO_CORES[t] for t in TIPOS_ORDEM]

                chart_tipo = (
                    alt.Chart(df_tipo_piv)
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("Quantidade:Q", title="Processos", stack="zero"),
                        y=alt.Y("Account:N", sort=_sort_desc, title=None, axis=alt.Axis(labelLimit=250)),
                        color=alt.Color(
                            "Tipo:N",
                            scale=alt.Scale(domain=tipo_domain, range=tipo_range),
                            legend=alt.Legend(title="Tipo"),
                        ),
                        tooltip=[
                            alt.Tooltip("Account:N", title="Analista"),
                            alt.Tooltip("Tipo:N", title="Tipo"),
                            alt.Tooltip("Quantidade:Q", format=",d", title="Processos"),
                        ],
                    )
                    .properties(height=max(350, n_analistas * 28))
                )
                st.altair_chart(chart_tipo, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 3: VISÃO POR CLIENTES
# ══════════════════════════════════════════════════════════════════════

with tab_clientes:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            # ── Preparação de dados ──────────────────────────────────────
            df_cli = df.copy()
            df_cli["_ClienteBase"] = df_cli["Cliente"].apply(_consolidar_cliente)

            _tem_tipo_cli = "Tipo de Operação" in df_cli.columns
            if _tem_tipo_cli:
                df_cli["_Tipo"] = df_cli["Tipo de Operação"].map(TIPO_LABELS).fillna("Outro")

            total_clientes = df_cli["_ClienteBase"].nunique()
            total_processos_cli = len(df_cli)

            # Clientes por tipo
            if _tem_tipo_cli:
                _cli_direto = df_cli[df_cli["_Tipo"] == "Direto"]["_ClienteBase"].nunique()
                _cli_co3 = df_cli[df_cli["_Tipo"] == "CO3"]["_ClienteBase"].nunique()
                _cli_encomenda = df_cli[df_cli["_Tipo"] == "Encomenda"]["_ClienteBase"].nunique()
            else:
                _cli_direto = _cli_co3 = _cli_encomenda = 0

            _val_total = df_cli["Valor Aduaneiro"].sum() if "Valor Aduaneiro" in df_cli.columns else 0

            # ── Seção A: KPIs ────────────────────────────────────────────
            st.markdown(
                f"""
                <div style="
                    background: {_CARD_BG};
                    border: 1px solid {_CARD_BORDER}; border-radius: 20px;
                    padding: 1rem 1.4rem; margin-bottom: 1rem;
                    box-shadow: {_CARD_SHADOW};
                    display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center;
                ">
                    <div style="flex: 0 0 auto; margin-right: 0.8rem;">
                        <span style="color: #6E6E73; font-size: 0.7rem; text-transform: uppercase; font-weight: 800;">Clientes</span><br/>
                        <span style="color: #5e8668; font-size: 1.8rem; font-weight: 800;">{total_clientes}</span>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.06); border: 1px solid {_CARD_BORDER}; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #4a8ab5;
                    ">
                        <div style="color: #6E6E73; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Direto</div>
                        <div style="color: #4a8ab5; font-size: 1.25rem; font-weight: 800;">{_cli_direto}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.06); border: 1px solid {_CARD_BORDER}; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #111111;
                    ">
                        <div style="color: #6E6E73; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">CO3</div>
                        <div style="color: {_BASE_DARK_TEXT}; font-size: 1.25rem; font-weight: 800;">{_cli_co3}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.06); border: 1px solid {_CARD_BORDER}; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #C9A67A;
                    ">
                        <div style="color: #6E6E73; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Encomenda</div>
                        <div style="color: #C9A67A; font-size: 1.25rem; font-weight: 800;">{_cli_encomenda}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 150px;
                        background: rgba(255,255,255,0.06); border: 1px solid {_CARD_BORDER}; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #111111;
                    ">
                        <div style="color: #6E6E73; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Valor Aduaneiro</div>
                        <div style="color: {_BASE_DARK_TEXT}; font-size: 1.05rem; font-weight: 800;">{_br_moeda(_val_total, 0)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ── Seção B: Representatividade por Tipo ─────────────────────
            if _tem_tipo_cli:
                st.caption("**Representatividade por Tipo de Operação**")

                df_repr = (
                    df_cli[df_cli["_Tipo"].isin(TIPOS_ORDEM)]
                    .groupby("_Tipo")
                    .size()
                    .reset_index(name="Processos")
                )
                df_repr = df_repr.rename(columns={"_Tipo": "Tipo"})
                _total_repr = df_repr["Processos"].sum()
                df_repr["Percentual"] = (df_repr["Processos"] / _total_repr * 100).round(1)

                # Cards visuais com barra de progresso (3 tipos apenas)
                _repr_html = '<div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:0.5rem;">'
                for _, _rr in df_repr.sort_values("Processos", ascending=False).iterrows():
                    _cor = TIPO_CORES.get(_rr["Tipo"], "#6E6E73")
                    _num_color = "#ffffff" if str(_rr["Tipo"]).strip().lower() == "encomenda" else _cor
                    _pct = _rr["Percentual"]
                    _n = int(_rr["Processos"])
                    _repr_html += (
                        f'<div style="flex:1 1 0;min-width:180px;'
                        f'background:rgba(245,245,247,0.5);'
                        f'border:1px solid #E5E5EA;border-radius:14px;padding:0.8rem 1rem;'
                        f'border-left:5px solid {_cor};">'
                        f'<div style="font-size:0.72rem;color:#6E6E73;text-transform:uppercase;'
                        f'font-weight:700;margin-bottom:0.3rem;">{_rr["Tipo"]}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:0.5rem;">'
                        f'<span style="font-size:1.6rem;font-weight:800;color:{_num_color};">{_n}</span>'
                        f'<span style="font-size:0.85rem;font-weight:700;color:#6E6E73;">'
                        f'{_pct:.1f}%</span>'
                        f'</div>'
                        f'<div style="background:#F2F2F7;border-radius:4px;height:8px;'
                        f'margin-top:0.4rem;overflow:hidden;">'
                        f'<div style="background:{_cor};height:100%;width:{_pct}%;'
                        f'border-radius:4px;"></div>'
                        f'</div>'
                        f'</div>'
                    )
                _repr_html += '</div>'
                st.markdown(_repr_html, unsafe_allow_html=True)

            st.divider()

            # ── Seção C: Top 10 geral ────────────────────────────────────
            if _tem_tipo_cli:
                st.caption("**Top 10 Clientes — Volume de Processos**")
                df_top10 = (
                    df_cli.groupby("_ClienteBase")
                    .agg(Processos=("Processo", "count"))
                    .reset_index()
                    .sort_values("Processos", ascending=False)
                    .head(10)
                )
                df_top10 = df_top10.rename(columns={"_ClienteBase": "Cliente"})

                _tipo_predominante = (
                    df_cli[df_cli["_Tipo"].isin(TIPOS_ORDEM)]
                    .groupby("_ClienteBase")["_Tipo"]
                    .agg(lambda s: s.value_counts().index[0])
                    .to_dict()
                )
                df_top10["Tipo"] = df_top10["Cliente"].map(_tipo_predominante).fillna("Outro")

                chart_top10 = (
                    alt.Chart(df_top10)
                    .mark_bar(cornerRadiusEnd=8)
                    .encode(
                        x=alt.X("Processos:Q", title="Processos"),
                        y=alt.Y("Cliente:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                        color=alt.Color(
                            "Tipo:N",
                            scale=alt.Scale(
                                domain=TIPOS_ORDEM,
                                range=[TIPO_CORES[t] for t in TIPOS_ORDEM],
                            ),
                            legend=alt.Legend(title="Tipo predominante", orient="right"),
                        ),
                        tooltip=[
                            alt.Tooltip("Cliente:N"),
                            alt.Tooltip("Processos:Q", format=",d"),
                            alt.Tooltip("Tipo:N", title="Tipo predominante"),
                        ],
                    )
                    .properties(height=360)
                )
                st.altair_chart(chart_top10, use_container_width=True)

            st.divider()

            # ── Seção D: Top 10 por Tipo (empilhados verticalmente) ──────
            if _tem_tipo_cli:
                st.caption("**Top 10 Clientes por Tipo de Operação**")

                for _tipo_label, _tipo_cor in [
                    ("Direto", TIPO_CORES["Direto"]),
                    ("CO3", TIPO_CORES["CO3"]),
                    ("Encomenda", TIPO_CORES["Encomenda"]),
                ]:
                    df_tipo_top = (
                        df_cli[df_cli["_Tipo"] == _tipo_label]
                        .groupby("_ClienteBase")
                        .agg(Processos=("Processo", "count"))
                        .reset_index()
                        .sort_values("Processos", ascending=False)
                        .head(10)
                        .rename(columns={"_ClienteBase": "Cliente"})
                    )

                    if len(df_tipo_top) == 0:
                        continue

                    st.markdown(
                        f'<div style="margin:0.6rem 0 0.2rem;">'
                        f'<span class="{_tag_force_class(_tipo_label)}" style="background:{_tipo_cor};color:{_tag_text_color(_tipo_label)};{_tag_force_style(_tipo_label)}border-radius:6px;'
                        f'padding:3px 14px;font-size:0.78rem;font-weight:800;">{_tipo_label}</span>'
                        f' <span style="color:#6E6E73;font-size:0.78rem;font-weight:600;">'
                        f'{len(df_cli[df_cli["_Tipo"] == _tipo_label])} processos</span></div>',
                        unsafe_allow_html=True,
                    )

                    chart_tipo_top = (
                        alt.Chart(df_tipo_top)
                        .mark_bar(cornerRadiusEnd=8, color=_tipo_cor)
                        .encode(
                            x=alt.X("Processos:Q", title="Processos"),
                            y=alt.Y("Cliente:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                            tooltip=[
                                alt.Tooltip("Cliente:N"),
                                alt.Tooltip("Processos:Q", format=",d"),
                            ],
                        )
                        .properties(height=max(220, len(df_tipo_top) * 28))
                    )
                    st.altair_chart(chart_tipo_top, use_container_width=True)

                st.divider()

            # ── Seção E: Distribuição por Modalidade (Top 15) ────────────
            if "Modalidade" in df_cli.columns:
                st.caption("**Distribuição por Modalidade — Top 15 Clientes**")
                # Pegar top 15 clientes por volume
                _top15_nomes = (
                    df_cli.groupby("_ClienteBase")
                    .size()
                    .sort_values(ascending=False)
                    .head(15)
                    .index.tolist()
                )
                df_mod_cli = (
                    df_cli[df_cli["_ClienteBase"].isin(_top15_nomes)]
                    .groupby(["_ClienteBase", "Modalidade"])
                    .size()
                    .reset_index(name="Processos")
                )
                df_mod_cli = df_mod_cli.rename(columns={"_ClienteBase": "Cliente"})

                _mod_domain = list(MODALIDADE_CORES.keys())
                _mod_range = list(MODALIDADE_CORES.values())
                # Adicionar modalidades não mapeadas
                _mods_extra = set(df_mod_cli["Modalidade"].unique()) - set(_mod_domain)
                _palette_extra = ["#6E6E73", "#a1887f", "#78909c", "#8d6e63", "#90a4ae"]
                for i, m in enumerate(_mods_extra):
                    _mod_domain.append(m)
                    _mod_range.append(_palette_extra[i % len(_palette_extra)])

                _sort_mod = alt.EncodingSortField(field="Processos", op="sum", order="descending")

                chart_mod_cli = (
                    alt.Chart(df_mod_cli)
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("Processos:Q", title="Processos", stack="zero"),
                        y=alt.Y("Cliente:N", sort=_sort_mod, title=None, axis=alt.Axis(labelLimit=250)),
                        color=alt.Color(
                            "Modalidade:N",
                            scale=alt.Scale(domain=_mod_domain, range=_mod_range),
                            legend=alt.Legend(title="Modalidade", orient="bottom", columns=3),
                        ),
                        tooltip=[
                            alt.Tooltip("Cliente:N"),
                            alt.Tooltip("Modalidade:N"),
                            alt.Tooltip("Processos:Q", format=",d"),
                        ],
                    )
                    .properties(height=max(380, len(_top15_nomes) * 32))
                )
                st.altair_chart(chart_mod_cli, use_container_width=True)

                st.divider()

            # ── Seção F: Concentração de Carteira (Pareto) ───────────────
            st.caption("**Concentração de Carteira**")

            df_pareto = (
                df_cli.groupby("_ClienteBase")
                .agg(Processos=("Processo", "count"))
                .reset_index()
                .sort_values("Processos", ascending=False)
                .reset_index(drop=True)
                .rename(columns={"_ClienteBase": "Cliente"})
            )
            df_pareto["Acumulado"] = df_pareto["Processos"].cumsum()
            df_pareto["% Acumulado"] = (df_pareto["Acumulado"] / df_pareto["Processos"].sum() * 100).round(1)
            df_pareto["Rank"] = range(1, len(df_pareto) + 1)

            # Encontrar quantos clientes = 80% dos processos
            _idx_80 = (df_pareto["% Acumulado"] >= 80).idxmax()
            _n_80 = int(df_pareto.loc[_idx_80, "Rank"])
            _pct_80 = df_pareto.loc[_idx_80, "% Acumulado"]

            st.markdown(
                f'<div style="background:rgba(142, 142, 147, 0.08);border:1px solid #E5E5EA;'
                f'border-radius:12px;padding:0.7rem 1rem;margin-bottom:0.8rem;'
                f'font-size:0.88rem;color:#111111;">'
                f'📊 Os <b>top {_n_80} clientes</b> ({(_n_80 / total_clientes * 100):.0f}% da base) '
                f'representam <b>{_pct_80:.1f}%</b> dos processos.'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Gráfico top 20 + curva acumulativa
            df_pareto_20 = df_pareto.head(20).copy()
            df_pareto_20["ClienteLabel"] = df_pareto_20["Rank"].astype(str) + ". " + df_pareto_20["Cliente"]
            _ordem_pareto = df_pareto_20["ClienteLabel"].tolist()

            barras = (
                alt.Chart(df_pareto_20)
                .mark_bar(cornerRadiusEnd=6, color=COLOR_NAVY)
                .encode(
                    x=alt.X("Processos:Q", title="Processos"),
                    y=alt.Y("ClienteLabel:N", sort=_ordem_pareto, title=None, axis=alt.Axis(labelLimit=250)),
                    tooltip=[
                        alt.Tooltip("Cliente:N"),
                        alt.Tooltip("Processos:Q", format=",d"),
                        alt.Tooltip("% Acumulado:Q", format=".1f", title="% acumulado"),
                    ],
                )
            )

            linha = (
                alt.Chart(df_pareto_20)
                .mark_line(color=COLOR_GOLD, strokeWidth=3, point=alt.OverlayMarkDef(size=50, color=COLOR_GOLD))
                .encode(
                    x=alt.X("% Acumulado:Q", title="% Acumulado", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("ClienteLabel:N", sort=_ordem_pareto, title=None, axis=alt.Axis(labelLimit=250)),
                    tooltip=[
                        alt.Tooltip("Cliente:N"),
                        alt.Tooltip("% Acumulado:Q", format=".1f"),
                    ],
                )
            )

            chart_pareto = alt.layer(barras, linha).resolve_scale(x="independent").properties(
                height=max(420, len(df_pareto_20) * 30)
            )
            st.altair_chart(chart_pareto, use_container_width=True)

            st.divider()

            # ── Seção G: Tabela completa de clientes ─────────────────────
            st.caption("**Todos os Clientes**")

            # Busca por nome
            _busca_cli = st.text_input(
                "Buscar cliente", key="busca_cliente_tab", placeholder="Digite o nome do cliente..."
            )

            # Agregar dados por cliente consolidado
            agg_dict = {"Processo": "count"}
            if "Valor Aduaneiro" in df_cli.columns:
                agg_dict["Valor Aduaneiro"] = "sum"
            if "Qtd. Container" in df_cli.columns:
                agg_dict["Qtd. Container"] = "sum"

            df_tabela_cli = (
                df_cli.groupby("_ClienteBase")
                .agg(**{
                    "Processos": ("Processo", "count"),
                    **({
                        "Valor Aduaneiro": ("Valor Aduaneiro", "sum"),
                    } if "Valor Aduaneiro" in df_cli.columns else {}),
                    **({
                        "Containers": ("Qtd. Container", "sum"),
                    } if "Qtd. Container" in df_cli.columns else {}),
                })
                .reset_index()
                .rename(columns={"_ClienteBase": "Cliente"})
                .sort_values("Processos", ascending=False)
            )

            # Tags por cliente
            if _tem_tipo_cli:
                _tipos_por_cliente = (
                    df_cli.groupby("_ClienteBase")["_Tipo"]
                    .apply(lambda s: [t for t in TIPOS_ORDEM if t in set(s)])
                    .to_dict()
                )
            else:
                _tipos_por_cliente = {}

            # Status por cliente
            _status_por_cliente = (
                df_cli.groupby("_ClienteBase")["Status"]
                .apply(lambda s: " | ".join(
                    f"{st_name}: {cnt}" for st_name in STATUS_ORDEM
                    if (cnt := s.value_counts().get(st_name, 0)) > 0
                ))
                .to_dict()
            )

            # Filtrar por busca
            if _busca_cli:
                df_tabela_cli = df_tabela_cli[
                    df_tabela_cli["Cliente"].str.contains(_busca_cli, case=False, na=False)
                ]

            st.caption(f"**{len(df_tabela_cli)}** clientes")

            # Renderizar como tabela HTML com tags
            _rows_html_cli = ""
            for _, _r in df_tabela_cli.iterrows():
                _tags_cli = " ".join(
                    f'<span class="{_tag_force_class(t)}" style="background:{TIPO_CORES[t]};color:{_tag_text_color(t)};{_tag_force_style(t)}'
                    f'border-radius:4px;padding:1px 6px;font-size:0.6rem;'
                    f'font-weight:800;letter-spacing:0.03em;">{t}</span>'
                    for t in _tipos_por_cliente.get(_r["Cliente"], [])
                )
                _val_ad = _br_moeda(_r["Valor Aduaneiro"], 0) if "Valor Aduaneiro" in _r.index and pd.notna(_r.get("Valor Aduaneiro")) else "—"
                _cnt = int(_r["Containers"]) if "Containers" in _r.index and pd.notna(_r.get("Containers")) else "—"
                _st_info = _status_por_cliente.get(_r["Cliente"], "")

                _rows_html_cli += (
                    f'<tr style="border-bottom:1px solid #E5E5EA;">'
                    f'<td style="padding:6px 8px;font-size:0.82rem;color:#111111;font-weight:600;">{_r["Cliente"]}</td>'
                    f'<td style="padding:6px 8px;font-size:0.82rem;text-align:center;color:#111111;font-weight:800;">{int(_r["Processos"])}</td>'
                    f'<td style="padding:6px 8px;font-size:0.8rem;color:#111111;">{_val_ad}</td>'
                    f'<td style="padding:6px 8px;font-size:0.8rem;text-align:center;color:#111111;">{_cnt}</td>'
                    f'<td style="padding:6px 8px;">{_tags_cli}</td>'
                    f'<td style="padding:6px 8px;font-size:0.7rem;color:#6E6E73;">{_st_info}</td>'
                    f'</tr>'
                )

            st.markdown(
                f'<div style="max-height:500px;overflow-y:auto;border:1px solid #E5E5EA;border-radius:12px;">'
                f'<table style="width:100%;border-collapse:collapse;">'
                f'<thead><tr style="background:#FAFAFA;position:sticky;top:0;">'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Cliente</th>'
                f'<th style="text-align:center;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Proc.</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Valor Aduaneiro</th>'
                f'<th style="text-align:center;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Cnt.</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Tipo</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Status</th>'
                f'</tr></thead><tbody>{_rows_html_cli}</tbody></table></div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 4: ALERTAS E PRAZOS
# ══════════════════════════════════════════════════════════════════════

with tab_alertas:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            with st.expander("Filtros", expanded=False):
                _ac1, _ac2, _ac3, _ac4 = st.columns(4)
                with _ac1:
                    _fa_account = st.multiselect("Account", sorted(df["Account"].dropna().unique().tolist()), key="al_account") if "Account" in df.columns else []
                with _ac2:
                    _fa_cliente = st.multiselect("Cliente", sorted(df["Cliente"].dropna().unique().tolist()), key="al_cliente")
                with _ac3:
                    _fa_importador = st.multiselect("Importador", sorted(df["Importador"].dropna().unique().tolist()), key="al_importador") if "Importador" in df.columns else []
                with _ac4:
                    _fa_busca = st.text_input("Buscar processo", key="al_busca", placeholder="Ex: 4458/25")
            if _fa_account:
                df = df[df["Account"].isin(_fa_account)]
            if _fa_cliente:
                df = df[df["Cliente"].isin(_fa_cliente)]
            if _fa_importador:
                df = df[df["Importador"].isin(_fa_importador)]
            if _fa_busca:
                df = df[df["Processo"].str.contains(_fa_busca, case=False, na=False)]

            alertas = calcular_alertas(df)

            # Resumo compacto no topo (inline HTML, sem st.metric grande)
            items = [
                ("Cnt. Vencido", len(alertas.get("container_vencido", [])), COLOR_RED),
                ("Perdimento", len(alertas["perdimento_proximo"]), COLOR_RED),
                ("Cnt. Vencendo", len(alertas["container_vencendo"]), "#8b5e3c"),
                ("Canal Vermelho", len(alertas["canal_vermelho"]), COLOR_RED),
                ("Canal Amarelo", len(alertas["canal_amarelo"]), "#8E8E93"),
                ("Saldo Negativo", len(alertas["saldo_negativo"]), COLOR_RED),
                ("Proc. Parado", len(alertas.get("processo_parado", [])), "#6E6E73"),
                ("Follow > 10d", len(alertas["follow_desatualizado"]), "#b58c23"),
                ("Valor > R$ 1M", len(alertas["valor_alto"]), "#8E8E93"),
                ("LI Indeferida", len(alertas["li_indeferida"]), "#6E6E73"),
            ]
            pills_html = "".join(
                f'<div style="'
                f"flex: 1 1 0; min-width: 100px; text-align: center;"
                f"background: rgba(255,255,255,0.6); border: 1px solid #E5E5EA; border-radius: 12px;"
                f"padding: 0.45rem 0.5rem; border-top: 3px solid {cor};"
                f'">'
                f'<div style="color: #6E6E73; font-size: 0.6rem; text-transform: uppercase; font-weight: 700; white-space: nowrap;">{label}</div>'
                f'<div style="color: {cor if n > 0 else "#111111"}; font-size: 1.3rem; font-weight: 800;">{n}</div>'
                f"</div>"
                for label, n, cor in items
            )
            st.markdown(
                f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">{pills_html}</div>',
                unsafe_allow_html=True,
            )

            def _render_alerta(titulo, df_alerta, colunas, formato_cols=None, icon="⚠️", alerta_key="", column_config=None):
                n = len(df_alerta)
                if n == 0:
                    return
                auto_expand = bool(_qp_alerta and _qp_alerta == alerta_key)
                with st.expander(f"{icon} {titulo} ({n})", expanded=auto_expand):
                    cols_existentes = [c for c in colunas if c in df_alerta.columns]
                    df_show = df_alerta[cols_existentes].copy()
                    fmt = {}
                    if formato_cols:
                        for col, fn in formato_cols.items():
                            if col in df_show.columns:
                                fmt[col] = fn
                    if fmt:
                        styled = df_show.style.format(fmt)
                        st.dataframe(styled, use_container_width=True, hide_index=True, column_config=column_config)
                    else:
                        st.dataframe(df_show, use_container_width=True, hide_index=True, column_config=column_config)

            fmt_moeda = lambda v: _br_moeda(v) if pd.notna(v) else ""
            fmt_data = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""

            def _safe_sort(df_a, col, **kwargs):
                if len(df_a) > 0 and col in df_a.columns:
                    return df_a.sort_values(col, **kwargs)
                return df_a

            # Container VENCIDO (mais crítico — data limite já passou)
            _render_alerta(
                "Container Vencido — Prazo Expirado",
                _safe_sort(alertas.get("container_vencido", pd.DataFrame()), "Dias Vencido", ascending=False),
                ["Processo", "Account", "Cliente", "Limite Dev. Container", "Dias Vencido", "Data do Follow", "Follow"],
                {"Limite Dev. Container": fmt_data, "Data do Follow": fmt_data},
                icon="🚨", alerta_key="container_vencido",
                column_config={
                    "Processo": st.column_config.Column(width=85),
                    "Account": st.column_config.Column(width=140),
                    "Cliente": st.column_config.Column(width=150),
                    "Limite Dev. Container": st.column_config.Column("Dev. Container", width=100),
                    "Dias Vencido": st.column_config.Column("Vencido", width=75),
                    "Data do Follow": st.column_config.Column("Últ. Follow", width=100),
                    "Follow": st.column_config.Column("Follow-up"),
                },
            )

            # Perdimento próximo — ordenado por dias restantes
            _render_alerta(
                "Limite para Perdimento (< 10 dias)",
                _safe_sort(alertas["perdimento_proximo"], "Dias Restantes"),
                ["Processo", "Account", "Cliente", "Limite para Perdimento", "Dias Restantes"],
                {"Limite para Perdimento": fmt_data},
                icon="⏰", alerta_key="perdimento_proximo",
            )

            # Container vencendo — ordenado por dias restantes (mais urgente primeiro)
            _render_alerta(
                "Container Vencendo (< 5 dias)",
                _safe_sort(alertas["container_vencendo"], "Dias Restantes"),
                ["Processo", "Account", "Cliente", "Limite Dev. Container", "Dias Restantes", "Data do Follow", "Follow"],
                {"Limite Dev. Container": fmt_data, "Data do Follow": fmt_data},
                icon="📦", alerta_key="container_vencendo",
                column_config={
                    "Processo": st.column_config.Column(width=85),
                    "Account": st.column_config.Column(width=140),
                    "Cliente": st.column_config.Column(width=150),
                    "Limite Dev. Container": st.column_config.Column("Dev. Container", width=100),
                    "Dias Restantes": st.column_config.Column("Restantes", width=75),
                    "Data do Follow": st.column_config.Column("Últ. Follow", width=100),
                    "Follow": st.column_config.Column("Follow-up"),
                },
            )

            # Canal Vermelho — ordenado pela data de registro (mais antigo primeiro)
            _render_alerta(
                "Canal Vermelho",
                _safe_sort(alertas["canal_vermelho"], "Registro da DI", na_position="first"),
                ["Processo", "Account", "Cliente", "Registro da DI", "Data do Follow", "Follow"],
                {"Registro da DI": fmt_data, "Data do Follow": fmt_data},
                icon="🔴", alerta_key="canal_vermelho",
            )

            # Canal Amarelo — ordenado pela data de registro (mais antigo primeiro)
            _render_alerta(
                "Canal Amarelo",
                _safe_sort(alertas["canal_amarelo"], "Registro da DI", na_position="first"),
                ["Processo", "Account", "Cliente", "Registro da DI", "Data do Follow", "Follow"],
                {"Registro da DI": fmt_data, "Data do Follow": fmt_data},
                icon="🟡", alerta_key="canal_amarelo",
            )

            # Saldo negativo — ordenado por saldo (mais negativo primeiro)
            _render_alerta(
                "Saldo Negativo",
                _safe_sort(alertas["saldo_negativo"], "Saldo"),
                ["Processo", "Account", "Cliente", "Saldo", "Valor Aduaneiro"],
                {"Saldo": fmt_moeda, "Valor Aduaneiro": fmt_moeda},
                icon="🔻", alerta_key="saldo_negativo",
            )

            # Processo parado (Pré-embarque > 30 dias sem previsão de embarque)
            _render_alerta(
                "Processo Parado — Pré-embarque sem previsão (> 30 dias)",
                _safe_sort(alertas.get("processo_parado", pd.DataFrame()), "Dias Parado", ascending=False),
                ["Processo", "Account", "Cliente", "Abertura", "Dias Parado", "Data do Follow", "Follow"],
                {"Abertura": fmt_data, "Data do Follow": fmt_data},
                icon="💤", alerta_key="processo_parado",
                column_config={
                    "Processo": st.column_config.Column(width=85),
                    "Account": st.column_config.Column(width=140),
                    "Cliente": st.column_config.Column(width=150),
                    "Abertura": st.column_config.Column(width=90),
                    "Dias Parado": st.column_config.Column("Parado", width=75),
                    "Data do Follow": st.column_config.Column("Últ. Follow", width=100),
                    "Follow": st.column_config.Column("Follow-up"),
                },
            )

            # Valor aduaneiro alto — ordenado por valor (maior primeiro)
            _render_alerta(
                "Valor Aduaneiro > R$ 1M",
                _safe_sort(alertas["valor_alto"], "Valor Aduaneiro", ascending=False),
                ["Processo", "Account", "Cliente", "Valor Aduaneiro", "Canal"],
                {"Valor Aduaneiro": fmt_moeda},
                icon="💰", alerta_key="valor_alto",
            )

            # Follow desatualizado — ordenado por dias sem follow (mais dias primeiro)
            _render_alerta(
                "Follow-up desatualizado (> 10 dias)",
                _safe_sort(alertas["follow_desatualizado"], "Dias sem Follow", ascending=False),
                ["Processo", "Account", "Cliente", "Data do Follow", "Dias sem Follow", "Follow"],
                {"Data do Follow": fmt_data},
                icon="📅", alerta_key="follow_desatualizado",
                column_config={
                    "Processo": st.column_config.Column(width=85),
                    "Account": st.column_config.Column(width=140),
                    "Cliente": st.column_config.Column(width=150),
                    "Data do Follow": st.column_config.Column("Últ. Follow", width=100),
                    "Dias sem Follow": st.column_config.Column("s/ Follow", width=75),
                    "Follow": st.column_config.Column("Follow-up"),
                },
            )

            # LI indeferida
            _render_alerta(
                "LI/LPCO Indeferida",
                alertas["li_indeferida"],
                ["Processo", "Account", "Cliente", "Situação", "LPCO Data"],
                {"LPCO Data": fmt_data},
                icon="🚫", alerta_key="li_indeferida",
            )


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 5: TABELA DE PROCESSOS
# ══════════════════════════════════════════════════════════════════════

with tab_tabela:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            with st.expander("Filtros", expanded=False):
                _tc1, _tc2, _tc3, _tc4 = st.columns(4)
                with _tc1:
                    f_account = _filtro_multiselect(df, "Account", "Account", "f_account") if "Account" in df.columns else []
                with _tc2:
                    f_cliente = _filtro_multiselect(df, "Cliente", "Cliente", "f_cliente")
                with _tc3:
                    f_tipo = _filtro_multiselect(df, "Tipo de Operação", "Tipo de Operação", "f_tipo") if "Tipo de Operação" in df.columns else []
                with _tc4:
                    f_processo = st.text_input("Buscar Processo", key="f_processo", placeholder="Ex: 4458/25")

            # Aplicar filtros
            df_f = df.copy()
            if f_account:
                df_f = df_f[df_f["Account"].isin(f_account)]
            if f_cliente:
                df_f = df_f[df_f["Cliente"].isin(f_cliente)]
            if f_tipo:
                df_f = df_f[df_f["Tipo de Operação"].isin(f_tipo)]
            if f_processo:
                df_f = df_f[df_f["Processo"].str.contains(f_processo, case=False, na=False)]

            st.caption(f"**{len(df_f)}** processos encontrados")

            # Colunas a exibir
            colunas_exibir = [
                c for c in [
                    "Status", "Processo", "Account", "Cliente", "Importador",
                    "Classificação", "Modalidade", "Saldo", "Tipo de Operação",
                    "Valor Aduaneiro", "Canal", "Abertura", "Data do Follow", "Follow",
                ]
                if c in df_f.columns
            ]

            df_show = df_f[colunas_exibir].copy()

            # Formatação
            formato = {}
            if "Saldo" in df_show.columns:
                formato["Saldo"] = lambda v: _br_moeda(v) if pd.notna(v) else ""
            if "Valor Aduaneiro" in df_show.columns:
                formato["Valor Aduaneiro"] = lambda v: _br_moeda(v, 0) if pd.notna(v) else ""
            if "Abertura" in df_show.columns:
                formato["Abertura"] = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""
            if "Data do Follow" in df_show.columns:
                formato["Data do Follow"] = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""

            def _estilo_saldo(val):
                if pd.notna(val) and isinstance(val, (int, float)) and val < 0:
                    return "color: #b5423a; font-weight: bold"
                return ""

            def _estilo_canal(val):
                if val == "Vermelho":
                    return "color: #b5423a; font-weight: bold"
                if val == "Amarelo":
                    return "color: #b58c23; font-weight: bold"
                return ""

            styled = df_show.style.format(formato)
            if "Saldo" in df_show.columns:
                styled = styled.map(_estilo_saldo, subset=["Saldo"])
            if "Canal" in df_show.columns:
                styled = styled.map(_estilo_canal, subset=["Canal"])

            height = min(38 + len(df_show) * 35 + 6, 700)
            st.dataframe(styled, use_container_width=True, hide_index=True, height=height)

            # Download filtrado
            csv_download = df_f.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Baixar dados filtrados (CSV)",
                csv_download,
                f"processos_filtrados_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
            )


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 6: UPLOAD
# ══════════════════════════════════════════════════════════════════════

with tab_upload:
    # Info do último upload
    if meta:
        dt = datetime.fromisoformat(meta["ultimo_upload"])
        st.info(
            f"**Último upload:** {dt.strftime('%d/%m/%Y %H:%M')} — "
            f"{meta['total_registros']} registros — "
            f"Arquivo: {meta['arquivo_original']}"
        )
    else:
        st.info("Nenhum upload realizado ainda.")

    st.markdown("#### Enviar nova planilha")
    uploaded = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="upload_csv")

    if uploaded is not None:
        try:
            df_preview = pd.read_csv(uploaded, encoding="utf-8-sig", dtype=str, nrows=10)
            uploaded.seek(0)
            df_full = pd.read_csv(uploaded, encoding="utf-8-sig", dtype=str)
            uploaded.seek(0)

            st.caption(f"**Preview** — {len(df_full)} registros, {len(df_full.columns)} colunas")
            st.dataframe(df_preview, use_container_width=True, hide_index=True)

            # Validação
            valido, avisos = validar_csv(df_full)
            for aviso in avisos:
                st.warning(aviso)

            if not valido:
                st.error("O arquivo não passou na validação. Corrija os problemas acima.")
            else:
                # Resumo dos status
                if "Status" in df_full.columns:
                    st.caption("**Distribuição por Status:**")
                    status_counts = df_full["Status"].value_counts()
                    cols = st.columns(min(len(status_counts), 6))
                    for i, (status, count) in enumerate(status_counts.items()):
                        with cols[i % len(cols)]:
                            st.metric(status, count)

                if st.button("Confirmar Upload", type="primary"):
                    total, avisos_upload = salvar_upload(uploaded)
                    if total > 0:
                        st.success(f"Upload concluído! {total} registros importados.")
                        for aviso in avisos_upload:
                            st.warning(aviso)
                        st.rerun()
                    else:
                        for aviso in avisos_upload:
                            st.error(aviso)

        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

    # Histórico de backups
    st.divider()
    st.markdown("#### Histórico de Uploads")
    backups = listar_backups()
    if not backups:
        st.caption("Nenhum backup disponível.")
    else:
        for bk in backups[:20]:
            col1, col2 = st.columns([3, 1])
            with col1:
                tamanho_kb = bk["tamanho"] / 1024
                st.caption(f"**{bk['nome']}** — {bk['data'].strftime('%d/%m/%Y %H:%M')} — {tamanho_kb:.0f} KB")
            with col2:
                with open(bk["caminho"], "rb") as f:
                    st.download_button(
                        "Baixar",
                        f.read(),
                        bk["nome"],
                        "text/csv",
                        key=f"bk_{bk['nome']}",
                    )


# ══════════════════════════════════════════════════════════════════════
# DEPARTAMENTO: EXPORTAÇÃO
# ══════════════════════════════════════════════════════════════════════

_EXP_STATUS_ORDEM = exp.STATUS_ORDEM_EXP
_EXP_STATUS_CORES = {
    "Ag.Instruções":  "#7ea6c7",
    "Pré-Embarque":   "#C9A67A",
    "Embarque":       "#5e8668",
    "Ag.Desembaraço": "#4a8ab5",
    "Sem etapa":      "#8E8E93",
}
_EXP_ACC_PALETTE = [_BASE_DARK_TEXT, "#4a8ab5", "#C9A67A", "#5e8668", "#8E8E93",
                    "#7ea6c7", "#8b5e3c", "#b5423a", "#6E6E73", "#36586f"]

with tab_exportacao:
    tab_exp_geral, tab_exp_analist, tab_exp_clientes, tab_exp_alertas, tab_exp_tabela, tab_exp_upload = st.tabs(
        ["Visão Geral", "Analistas", "Clientes", "Alertas e Prazos", "Tabela", "Upload"]
    )

    with tab_exp_geral:
        if not exp.dados_360_existem():
            st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
        else:
            _df360 = exp.obter_processos_360()
            if _df360.empty:
                st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
            else:
                _total360 = len(_df360)
                st.markdown(
                    f"""<div style="background:{_CARD_BG};border:1px solid {_CARD_BORDER};border-radius:20px;
                    padding:1rem 1.4rem;margin-bottom:1rem;box-shadow:{_CARD_SHADOW};
                    display:flex;flex-wrap:wrap;gap:0.6rem;align-items:center;">
                    <div style="flex:0 0 auto;margin-right:0.8rem;">
                        <span style="color:#6E6E73;font-size:0.7rem;text-transform:uppercase;font-weight:800;">Total</span><br/>
                        <span style="color:{_BASE_DARK_TEXT};font-size:1.8rem;font-weight:800;">{_total360:,}</span>
                    </div>
                    {"".join(f'''<div style="flex:1 1 0;min-width:120px;background:rgba(255,255,255,0.06);
                        border:1px solid {_CARD_BORDER};border-radius:14px;padding:0.55rem 0.75rem;text-align:center;
                        border-left:4px solid {_EXP_STATUS_CORES.get(s,'#ccc')};">
                        <div style="color:#6E6E73;font-size:0.65rem;text-transform:uppercase;font-weight:700;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{s}</div>
                        <div style="color:{_BASE_DARK_TEXT};font-size:1.25rem;font-weight:800;">{len(_df360[_df360["Status"]==s])}</div>
                        <div style="color:{_EXP_STATUS_CORES.get(s,"#6E6E73")};font-size:0.78rem;font-weight:700;">
                            {len(_df360[_df360["Status"]==s])/_total360*100:.1f}%</div>
                    </div>''' for s in _EXP_STATUS_ORDEM)}
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.divider()
                _c1, _c2 = st.columns(2)
                with _c1:
                    st.caption("**Distribuição por Status**")
                    import altair as _alt
                    _ds = _df360["Status"].value_counts().reset_index()
                    _ds.columns = ["Status", "Quantidade"]
                    _ds["Status"] = pd.Categorical(_ds["Status"], categories=_EXP_STATUS_ORDEM, ordered=True)
                    _ds = _ds.sort_values("Status")
                    _ch = (_alt.Chart(_ds).mark_bar(cornerRadiusEnd=8).encode(
                        x=_alt.X("Quantidade:Q", title="Processos"),
                        y=_alt.Y("Status:N", sort=_EXP_STATUS_ORDEM, title=None, axis=_alt.Axis(labelLimit=250)),
                        color=_alt.Color("Status:N", scale=_alt.Scale(
                            domain=list(_EXP_STATUS_CORES.keys()), range=list(_EXP_STATUS_CORES.values())), legend=None),
                        tooltip=[_alt.Tooltip("Status:N"), _alt.Tooltip("Quantidade:Q", format=",d")],
                    ).properties(height=220))
                    st.altair_chart(_ch, use_container_width=True)
                with _c2:
                    st.caption("**Distribuição por Modalidade**")
                    if "Modalidade" in _df360.columns:
                        _dm = _df360["Modalidade"].value_counts().reset_index()
                        _dm.columns = ["Modalidade", "Quantidade"]
                        if len(_dm) > 5:
                            _dm = pd.concat([_dm.head(5), pd.DataFrame([{"Modalidade": "Outros", "Quantidade": _dm.iloc[5:]["Quantidade"].sum()}])], ignore_index=True)
                        _dm_total = _dm["Quantidade"].sum()
                        _dm["Pct"] = (_dm["Quantidade"] / _dm_total * 100).round(1)
                        _dm["Label"] = _dm["Pct"].apply(lambda v: f"{v:.1f}%")
                        _mod_pal = [_BASE_DARK_TEXT, "#4a8ab5", "#C9A67A", "#5e8668", "#8E8E93", "#7ea6c7"]
                        _dm_dom = _dm["Modalidade"].tolist()
                        _dm_rng = [_mod_pal[i % len(_mod_pal)] for i in range(len(_dm_dom))]
                        _pie = (_alt.Chart(_dm).mark_arc(innerRadius=0, outerRadius=90, cornerRadius=3).encode(
                            theta=_alt.Theta("Quantidade:Q", stack=True),
                            color=_alt.Color("Modalidade:N", scale=_alt.Scale(domain=_dm_dom, range=_dm_rng),
                                             legend=_alt.Legend(title=None, orient="bottom", columns=3)),
                            tooltip=[_alt.Tooltip("Modalidade:N"), _alt.Tooltip("Quantidade:Q", format=",d"), _alt.Tooltip("Pct:Q", title="%", format=".1f")],
                        ))
                        _txt = (_alt.Chart(_dm).mark_text(radius=110, size=12, fontWeight="bold").encode(
                            theta=_alt.Theta("Quantidade:Q", stack=True), text="Label:N",
                            color=_alt.Color("Modalidade:N", scale=_alt.Scale(domain=_dm_dom, range=_dm_rng), legend=None),
                        ))
                        st.altair_chart((_pie + _txt).properties(height=240, padding={"top": 20, "bottom": 10}), use_container_width=True)
                _c3, _c4 = st.columns(2)
                with _c3:
                    st.caption("**Distribuição por Account**")
                    _da = _df360["Account Responsável"].value_counts().reset_index()
                    _da.columns = ["Account", "Quantidade"]
                    _da_dom = _da["Account"].tolist()
                    _da_rng = [_EXP_ACC_PALETTE[i % len(_EXP_ACC_PALETTE)] for i in range(len(_da_dom))]
                    _ch_acc = (_alt.Chart(_da).mark_bar(cornerRadiusEnd=8).encode(
                        x=_alt.X("Quantidade:Q", title="Processos"),
                        y=_alt.Y("Account:N", sort="-x", title=None, axis=_alt.Axis(labelLimit=350)),
                        color=_alt.Color("Account:N", scale=_alt.Scale(domain=_da_dom, range=_da_rng), legend=None),
                        tooltip=[_alt.Tooltip("Account:N"), _alt.Tooltip("Quantidade:Q", format=",d")],
                    ).properties(height=max(220, len(_da_dom) * 32)))
                    st.altair_chart(_ch_acc, use_container_width=True)
                with _c4:
                    st.caption("**Distribuição por Tipo**")
                    if "Tipo" in _df360.columns:
                        _dt = _df360["Tipo"].value_counts().reset_index()
                        _dt.columns = ["Tipo", "Quantidade"]
                        if len(_dt) > 6:
                            _dt = pd.concat([_dt.head(6), pd.DataFrame([{"Tipo": "Outros", "Quantidade": _dt.iloc[6:]["Quantidade"].sum()}])], ignore_index=True)
                        _dt_total = _dt["Quantidade"].sum()
                        _dt["Pct"] = (_dt["Quantidade"] / _dt_total * 100).round(1)
                        _dt["Label"] = _dt["Pct"].apply(lambda v: f"{v:.1f}%")
                        _tp_pal = ["#4a8ab5", "#C9A67A", "#5e8668", "#8E8E93", _BASE_DARK_TEXT, "#7ea6c7", "#8b5e3c"]
                        _dt_dom = _dt["Tipo"].tolist()
                        _dt_rng = [_tp_pal[i % len(_tp_pal)] for i in range(len(_dt_dom))]
                        _pie_t = (_alt.Chart(_dt).mark_arc(innerRadius=0, outerRadius=90, cornerRadius=3).encode(
                            theta=_alt.Theta("Quantidade:Q", stack=True),
                            color=_alt.Color("Tipo:N", scale=_alt.Scale(domain=_dt_dom, range=_dt_rng),
                                             legend=_alt.Legend(title=None, orient="bottom", columns=1, labelLimit=0)),
                            tooltip=[_alt.Tooltip("Tipo:N"), _alt.Tooltip("Quantidade:Q", format=",d"), _alt.Tooltip("Pct:Q", title="%", format=".1f")],
                        ))
                        _txt_t = (_alt.Chart(_dt).mark_text(radius=110, size=11, fontWeight="bold").encode(
                            theta=_alt.Theta("Quantidade:Q", stack=True), text="Label:N",
                            color=_alt.Color("Tipo:N", scale=_alt.Scale(domain=_dt_dom, range=_dt_rng), legend=None),
                        ))
                        st.altair_chart((_pie_t + _txt_t).properties(height=240, padding={"top": 20, "bottom": 10}), use_container_width=True)

    with tab_exp_analist:
        if not exp.dados_360_existem():
            st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
        else:
            _df_an = exp.obter_processos_360()
            if _df_an.empty:
                st.info("Nenhum dado carregado.")
            else:
                import altair as _alt

                _EXP_TIPO_CORES = {
                    "Frete": "#4a8ab5",
                    "Documentos": "#C9A67A",
                    "Desembaraço": "#5e8668",
                    "Trading": "#8E8E93",
                }
                _EXP_TIPO_ORDEM = ["Frete", "Documentos", "Desembaraço", "Trading"]
                _THRESHOLD_AN = 5

                def _tipo_tags_html(df_sub):
                    tipos = set()
                    if "Tipo" in df_sub.columns:
                        for v in df_sub["Tipo"].dropna():
                            for p in str(v).split("+"):
                                p = p.strip()
                                if p in _EXP_TIPO_CORES:
                                    tipos.add(p)
                    parts = []
                    for t in _EXP_TIPO_ORDEM:
                        if t not in tipos:
                            continue
                        c = _EXP_TIPO_CORES[t]
                        parts.append(
                            f'<span style="display:inline-block;padding:2px 8px;border-radius:20px;'
                            f'background:{c}22;border:1px solid {c};color:{c};'
                            f'font-size:0.65rem;font-weight:700;margin-right:4px;">{t}</span>'
                        )
                    return "".join(parts)

                _an_agg = (
                    _df_an.groupby("Account Responsável")
                    .agg(processos=("Processo", "count"), clientes=("Cliente", "nunique"))
                    .reset_index()
                    .sort_values("processos", ascending=False)
                )
                _an_cards = _an_agg[_an_agg["processos"] >= _THRESHOLD_AN]
                _an_audit = _an_agg[_an_agg["processos"] < _THRESHOLD_AN]

                _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                _mc1.metric("Analistas", len(_an_agg))
                _mc2.metric("Total processos", int(_an_agg["processos"].sum()))
                _mc3.metric("Média por analista", round(_an_agg["processos"].mean(), 1) if len(_an_agg) else 0)
                _mc4.metric("Maior carteira", int(_an_agg["processos"].max()) if len(_an_agg) else 0)

                for _i in range(0, len(_an_cards), 3):
                    _cols = st.columns(3)
                    for _j, _col in enumerate(_cols):
                        _idx = _i + _j
                        if _idx >= len(_an_cards):
                            break
                        _row = _an_cards.iloc[_idx]
                        _df_an_fil = _df_an[_df_an["Account Responsável"] == _row["Account Responsável"]]
                        _sc = _df_an_fil["Status"].value_counts()
                        _pills = " | ".join(f"{s}: {_sc.get(s,0)}" for s in _EXP_STATUS_ORDEM if _sc.get(s, 0) > 0)
                        _tags_html = _tipo_tags_html(_df_an_fil)
                        with _col:
                            st.markdown(
                                f"""<div style="background:{_CARD_BG};border:1px solid {_CARD_BORDER};
                                border-radius:18px;padding:1rem 1.2rem;margin-bottom:0.2rem;box-shadow:{_CARD_SHADOW};">
                                <div style="font-weight:800;color:{_BASE_DARK_TEXT};font-size:1.05rem;margin-bottom:0.4rem;">
                                    {_row['Account Responsável']}</div>
                                <div style="display:flex;gap:1.2rem;margin-bottom:0.5rem;">
                                    <div><span style="color:{_MUTED_TEXT};font-size:0.75rem;text-transform:uppercase;font-weight:700;">Processos</span><br/>
                                    <span style="color:{_BASE_DARK_TEXT};font-size:1.3rem;font-weight:800;">{int(_row['processos'])}</span></div>
                                    <div><span style="color:{_MUTED_TEXT};font-size:0.75rem;text-transform:uppercase;font-weight:700;">Clientes</span><br/>
                                    <span style="color:#5e8668;font-size:1.3rem;font-weight:800;">{int(_row['clientes'])}</span></div>
                                </div>
                                <div style="margin-bottom:0.4rem;">{_tags_html}</div>
                                <div style="font-size:0.75rem;color:{_MUTED_TEXT};">{_pills}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )
                            with st.expander("Ver clientes", expanded=False):
                                _cl_agg = (
                                    _df_an_fil.groupby("Cliente").size()
                                    .reset_index(name="Processos")
                                    .sort_values("Processos", ascending=False)
                                )
                                _rows_h = "".join(
                                    f'<tr style="border-bottom:1px solid #E5E5EA;">'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;color:#111111;">{r["Cliente"]}</td>'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;text-align:center;color:#111111;font-weight:700;">{int(r["Processos"])}</td>'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;">'
                                    f'{_tipo_tags_html(_df_an_fil[_df_an_fil["Cliente"] == r["Cliente"]])}'
                                    f'</td>'
                                    f'</tr>'
                                    for _, r in _cl_agg.iterrows()
                                )
                                st.markdown(
                                    f'<table style="width:100%;border-collapse:collapse;">'
                                    f'<thead><tr style="background:#FAFAFA;">'
                                    f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Cliente</th>'
                                    f'<th style="text-align:center;padding:6px 8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Proc.</th>'
                                    f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;color:#6E6E73;text-transform:uppercase;font-weight:700;">Tipos</th>'
                                    f'</tr></thead><tbody>{_rows_h}</tbody></table>',
                                    unsafe_allow_html=True,
                                )

                if len(_an_audit) > 0:
                    st.divider()
                    with st.expander(
                        f"Log de auditoria — {len(_an_audit)} analista(s) com menos de {_THRESHOLD_AN} processos",
                        expanded=False,
                    ):
                        _audit_rows = []
                        for _, _ar in _an_audit.iterrows():
                            _df_aud = _df_an[_df_an["Account Responsável"] == _ar["Account Responsável"]]
                            for _, _pr in _df_aud.iterrows():
                                _tipo_parts = [p.strip() for p in str(_pr.get("Tipo", "")).split("+") if p.strip()]
                                _audit_rows.append({
                                    "Analista": _ar["Account Responsável"],
                                    "Processo": _pr.get("Processo", ""),
                                    "Cliente": _pr.get("Cliente", ""),
                                    "Status": _pr.get("Status", ""),
                                    "Tipo": " + ".join(_tipo_parts) if _tipo_parts else "",
                                })
                        if _audit_rows:
                            _df_audit_tbl = pd.DataFrame(_audit_rows)
                            from utils.ui import renderizar_dataframe
                            renderizar_dataframe(_df_audit_tbl, use_container_width=True, hide_index=True)

                st.divider()
                st.caption("**Distribuição por Analista e Status**")
                _df_piv = _df_an.groupby(["Account Responsável", "Status"]).size().reset_index(name="Quantidade")
                _df_piv["Status"] = pd.Categorical(_df_piv["Status"], categories=_EXP_STATUS_ORDEM, ordered=True)
                _ch_an = (_alt.Chart(_df_piv).mark_bar(cornerRadiusEnd=4).encode(
                    x=_alt.X("Quantidade:Q", title="Processos", stack="zero"),
                    y=_alt.Y("Account Responsável:N", sort=_alt.EncodingSortField(field="Quantidade", op="sum", order="descending"),
                              title=None, axis=_alt.Axis(labelLimit=350)),
                    color=_alt.Color("Status:N", scale=_alt.Scale(
                        domain=list(_EXP_STATUS_CORES.keys()), range=list(_EXP_STATUS_CORES.values())),
                        legend=_alt.Legend(title="Status", labelLimit=0)),
                    tooltip=[_alt.Tooltip("Account Responsável:N", title="Analista"),
                              _alt.Tooltip("Status:N"), _alt.Tooltip("Quantidade:Q", format=",d")],
                ).properties(height=max(320, len(_an_agg) * 36)))
                st.altair_chart(_ch_an, use_container_width=True)

    with tab_exp_clientes:
        if not exp.dados_360_existem():
            st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
        else:
            _df_cli = exp.obter_processos_360()
            if _df_cli.empty:
                st.info("Nenhum dado carregado.")
            else:
                import altair as _alt
                _total_cli = _df_cli["Cliente"].nunique()
                _mc1, _mc2, _mc3 = st.columns(3)
                _mc1.metric("Clientes únicos", _total_cli)
                _mc2.metric("Total processos", len(_df_cli))
                _mc3.metric("Média proc./cliente", round(len(_df_cli) / _total_cli, 1) if _total_cli else 0)
                st.divider()

                st.caption("**Top 15 Clientes — Volume de Processos**")
                _df_top = (_df_cli.groupby("Cliente").size().reset_index(name="Processos")
                           .sort_values("Processos", ascending=False).head(15))
                _ch_top = (_alt.Chart(_df_top).mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY).encode(
                    x=_alt.X("Processos:Q", title="Processos"),
                    y=_alt.Y("Cliente:N", sort="-x", title=None, axis=_alt.Axis(labelLimit=250)),
                    tooltip=[_alt.Tooltip("Cliente:N"), _alt.Tooltip("Processos:Q", format=",d")],
                ).properties(height=max(360, len(_df_top) * 28)))
                st.altair_chart(_ch_top, use_container_width=True)
                st.divider()

                st.caption("**Concentração de Carteira (Pareto)**")
                _df_pareto = (_df_cli.groupby("Cliente").size().reset_index(name="Processos")
                              .sort_values("Processos", ascending=False).reset_index(drop=True))
                _df_pareto["Acumulado"] = _df_pareto["Processos"].cumsum()
                _df_pareto["% Acumulado"] = (_df_pareto["Acumulado"] / _df_pareto["Processos"].sum() * 100).round(1)
                _df_pareto["Rank"] = range(1, len(_df_pareto) + 1)
                _idx_80 = (_df_pareto["% Acumulado"] >= 80).idxmax()
                _n_80 = int(_df_pareto.loc[_idx_80, "Rank"])
                _pct_80 = _df_pareto.loc[_idx_80, "% Acumulado"]
                st.markdown(
                    f'<div style="background:rgba(142,142,147,0.08);border:1px solid #E5E5EA;border-radius:12px;'
                    f'padding:0.7rem 1rem;margin-bottom:0.8rem;font-size:0.88rem;color:#111111;">'
                    f'Os <b>top {_n_80} clientes</b> ({(_n_80/_total_cli*100):.0f}% da base) representam <b>{_pct_80:.1f}%</b> dos processos.</div>',
                    unsafe_allow_html=True,
                )
                _df_p20 = _df_pareto.head(20).copy()
                _df_p20["Lbl"] = _df_p20["Rank"].astype(str) + ". " + _df_p20["Cliente"]
                _ordem_p = _df_p20["Lbl"].tolist()
                _barras = (_alt.Chart(_df_p20).mark_bar(cornerRadiusEnd=6, color=COLOR_NAVY).encode(
                    x=_alt.X("Processos:Q"), y=_alt.Y("Lbl:N", sort=_ordem_p, title=None, axis=_alt.Axis(labelLimit=250)),
                    tooltip=[_alt.Tooltip("Cliente:N"), _alt.Tooltip("Processos:Q", format=",d")],
                ))
                _linha = (_alt.Chart(_df_p20).mark_line(color=COLOR_GOLD, strokeWidth=3,
                    point=_alt.OverlayMarkDef(size=50, color=COLOR_GOLD)).encode(
                    x=_alt.X("% Acumulado:Q", scale=_alt.Scale(domain=[0, 100])),
                    y=_alt.Y("Lbl:N", sort=_ordem_p, title=None),
                    tooltip=[_alt.Tooltip("Cliente:N"), _alt.Tooltip("% Acumulado:Q", format=".1f")],
                ))
                st.altair_chart(
                    _alt.layer(_barras, _linha).resolve_scale(x="independent").properties(height=max(420, len(_df_p20) * 30)),
                    use_container_width=True,
                )
                st.divider()
                _busca_exp = st.text_input("Buscar cliente", key="busca_cli_exp", placeholder="Digite o nome...")
                _df_tab_cli = _df_cli.groupby("Cliente").size().reset_index(name="Processos").sort_values("Processos", ascending=False)
                if _busca_exp:
                    _df_tab_cli = _df_tab_cli[_df_tab_cli["Cliente"].str.contains(_busca_exp, case=False, na=False)]
                st.caption(f"**{len(_df_tab_cli)}** clientes")
                from utils.ui import renderizar_dataframe
                renderizar_dataframe(_df_tab_cli, use_container_width=True, hide_index=True,
                                     height=min(38 + len(_df_tab_cli) * 35, 600))

    with tab_exp_alertas:
        if not exp.dados_360_existem():
            st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
        else:
            _df_al = exp.obter_processos_360()
            if _df_al.empty:
                st.info("Nenhum dado carregado.")
            else:
                with st.expander("Filtros", expanded=False):
                    _ea1, _ea2, _ea3, _ea4 = st.columns(4)
                    with _ea1:
                        _ea_account = st.multiselect("Account", sorted(_df_al["Account Responsável"].dropna().unique().tolist()), key="ea_account") if "Account Responsável" in _df_al.columns else []
                    with _ea2:
                        _ea_cliente = st.multiselect("Cliente", sorted(_df_al["Cliente"].dropna().unique().tolist()), key="ea_cliente")
                    with _ea3:
                        _ea_exportador = st.multiselect("Exportador", sorted(_df_al["Exportador"].dropna().unique().tolist()), key="ea_exportador") if "Exportador" in _df_al.columns else []
                    with _ea4:
                        _ea_busca = st.text_input("Buscar processo", key="ea_busca", placeholder="Ex: EXP-2025/001")
                if _ea_account:
                    _df_al = _df_al[_df_al["Account Responsável"].isin(_ea_account)]
                if _ea_cliente:
                    _df_al = _df_al[_df_al["Cliente"].isin(_ea_cliente)]
                if _ea_exportador:
                    _df_al = _df_al[_df_al["Exportador"].isin(_ea_exportador)]
                if _ea_busca:
                    _df_al = _df_al[_df_al["Processo"].str.contains(_ea_busca, case=False, na=False)]

                _alertas = exp.calcular_alertas_360(_df_al)
                _itens_al = [
                    ("Dead Draft", len(_alertas["dead_draft"]), COLOR_RED),
                    ("Dead Carga", len(_alertas["dead_carga"]), COLOR_RED),
                    ("Dead VGM", len(_alertas["dead_vgm"]), COLOR_RED),
                    ("Prev. Embarque", len(_alertas["prev_embarque_vencida"]), "#8b5e3c"),
                    ("DUE s/ Averb.", len(_alertas["due_sem_avercacao"]), "#b58c23"),
                    ("Sem Etapa", len(_alertas["sem_etapa"]), "#8E8E93"),
                    ("Follow > 10d", len(_alertas["follow_desatualizado"]), "#b58c23"),
                ]
                _pills_al = "".join(
                    f'<div style="flex:1 1 0;min-width:100px;text-align:center;background:rgba(255,255,255,0.6);'
                    f'border:1px solid #E5E5EA;border-radius:12px;padding:0.45rem 0.5rem;border-top:3px solid {cor};">'
                    f'<div style="color:#6E6E73;font-size:0.6rem;text-transform:uppercase;font-weight:700;white-space:nowrap;">{lbl}</div>'
                    f'<div style="color:{cor if n > 0 else "#111111"};font-size:1.3rem;font-weight:800;">{n}</div></div>'
                    for lbl, n, cor in _itens_al
                )
                st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">{_pills_al}</div>', unsafe_allow_html=True)

                _fmt_dt = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""

                def _exp_alerta(titulo, df_a, colunas, fmt=None, icon="⚠️"):
                    if len(df_a) == 0:
                        return
                    with st.expander(f"{icon} {titulo} ({len(df_a)})", expanded=False):
                        _cols_ok = [c for c in colunas if c in df_a.columns]
                        _df_s = df_a[_cols_ok].copy()
                        if fmt:
                            _styled = _df_s.style.format({k: v for k, v in fmt.items() if k in _df_s.columns})
                            st.dataframe(_styled, use_container_width=True, hide_index=True)
                        else:
                            st.dataframe(_df_s, use_container_width=True, hide_index=True)

                _exp_alerta("Dead Draft vencido sem confirmação",
                    _alertas["dead_draft"],
                    ["Processo", "Account Responsável", "Cliente", "Dead Draft", "Dead Draft Confirmado", "Data do follow", "Follow"],
                    {"Dead Draft": _fmt_dt, "Dead Draft Confirmado": _fmt_dt, "Data do follow": _fmt_dt}, "🚨")
                _exp_alerta("Dead Carga vencida sem confirmação",
                    _alertas["dead_carga"],
                    ["Processo", "Account Responsável", "Cliente", "Dead Carga", "Dead Carga Confirmada", "Data do follow", "Follow"],
                    {"Dead Carga": _fmt_dt, "Dead Carga Confirmada": _fmt_dt, "Data do follow": _fmt_dt}, "🚨")
                _exp_alerta("Dead VGM vencido sem confirmação",
                    _alertas["dead_vgm"],
                    ["Processo", "Account Responsável", "Cliente", "Dead VGM", "VGM Confirmado", "Data do follow", "Follow"],
                    {"Dead VGM": _fmt_dt, "VGM Confirmado": _fmt_dt, "Data do follow": _fmt_dt}, "⚓")
                _exp_alerta("Previsão de embarque vencida sem data real",
                    _alertas["prev_embarque_vencida"],
                    ["Processo", "Account Responsável", "Cliente", "Previsão de embarque", "Data de embarque", "Data do follow", "Follow"],
                    {"Previsão de embarque": _fmt_dt, "Data de embarque": _fmt_dt, "Data do follow": _fmt_dt}, "⏰")
                _exp_alerta("DUE registrada sem averbação",
                    _alertas["due_sem_avercacao"],
                    ["Processo", "Account Responsável", "Cliente", "Data de Registro DUE", "Data averbação", "Data do follow"],
                    {"Data de Registro DUE": _fmt_dt, "Data averbação": _fmt_dt, "Data do follow": _fmt_dt}, "📋")
                _exp_alerta("Processos sem etapa",
                    _alertas["sem_etapa"],
                    ["Processo", "Account Responsável", "Cliente", "Tipo", "Modalidade", "Data do follow", "Follow"],
                    {"Data do follow": _fmt_dt}, "❓")
                _al_follow = _alertas["follow_desatualizado"]
                if len(_al_follow) > 0:
                    _al_follow = _al_follow.sort_values("Dias sem Follow", ascending=False)
                _exp_alerta("Follow-up desatualizado (> 10 dias)",
                    _al_follow,
                    ["Processo", "Account Responsável", "Cliente", "Data do follow", "Dias sem Follow", "Follow"],
                    {"Data do follow": _fmt_dt}, "📅")

    with tab_exp_tabela:
        if not exp.dados_360_existem():
            st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")
        else:
            _df_tab = exp.obter_processos_360()
            if _df_tab.empty:
                st.info("Nenhum dado carregado.")
            else:
                from utils.ui import renderizar_dataframe
                with st.expander("Filtros", expanded=False):
                    _fc1, _fc2, _fc3, _fc4 = st.columns(4)
                    with _fc1:
                        _f_st = st.multiselect("Status", sorted(_df_tab["Status"].dropna().unique()), key="exp_f_st")
                    with _fc2:
                        _f_ac = st.multiselect("Account", sorted(_df_tab["Account Responsável"].dropna().unique()), key="exp_f_ac")
                    with _fc3:
                        _f_mo = st.multiselect("Modalidade", sorted(_df_tab["Modalidade"].dropna().unique()) if "Modalidade" in _df_tab.columns else [], key="exp_f_mo")
                    with _fc4:
                        _f_tp = st.multiselect("Tipo", sorted(_df_tab["Tipo"].dropna().unique()) if "Tipo" in _df_tab.columns else [], key="exp_f_tp")
                    _f_proc = st.text_input("Buscar Processo", key="exp_f_proc", placeholder="Ex: 2643/26")
                _df_tf = _df_tab.copy()
                if _f_st:
                    _df_tf = _df_tf[_df_tf["Status"].isin(_f_st)]
                if _f_ac:
                    _df_tf = _df_tf[_df_tf["Account Responsável"].isin(_f_ac)]
                if _f_mo:
                    _df_tf = _df_tf[_df_tf["Modalidade"].isin(_f_mo)]
                if _f_tp:
                    _df_tf = _df_tf[_df_tf["Tipo"].isin(_f_tp)]
                if _f_proc:
                    _df_tf = _df_tf[_df_tf["Processo"].str.contains(_f_proc, case=False, na=False)]
                st.caption(f"**{len(_df_tf)}** processos")
                _cols_tab = [c for c in ["Status", "Processo", "Account Responsável", "Cliente", "Tipo", "Modalidade",
                                          "Booking", "Previsão de embarque", "Data de embarque", "Data do follow", "Follow"]
                             if c in _df_tf.columns]
                _fmt_tab = {}
                for _dc in ["Previsão de embarque", "Data de embarque", "Data do follow"]:
                    if _dc in _df_tf.columns:
                        _fmt_tab[_dc] = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""
                _df_show_tab = _df_tf[_cols_tab].copy()
                _styled_tab = _df_show_tab.style.format(_fmt_tab)
                renderizar_dataframe(_styled_tab, use_container_width=True, hide_index=True,
                                     height=min(38 + len(_df_show_tab) * 35, 700))
                _csv_exp = _df_tf.to_csv(index=False).encode("utf-8-sig")
                st.download_button("Baixar filtrados (CSV)", _csv_exp,
                    f"exportacao_filtrado_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

    with tab_exp_upload:
        _meta_exp = exp.carregar_meta_360()
        if _meta_exp:
            _dt_exp = datetime.fromisoformat(_meta_exp["ultimo_upload"])
            st.info(
                f"**Último upload:** {_dt_exp.strftime('%d/%m/%Y %H:%M')} — "
                f"{_meta_exp['total_registros']} registros — "
                f"Arquivo: {_meta_exp['arquivo_original']}"
            )
        else:
            st.info("Nenhum upload realizado ainda.")
        st.markdown("#### Enviar nova planilha")
        st.caption("Arquivo CSV exportado do sistema operacional de Exportação. Colunas obrigatórias: **Processo, Status, Account Responsável, Cliente, Tipo, Modalidade**.")
        _up_exp = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="up_exp_360")
        if _up_exp is not None:
            try:
                _df_prev = pd.read_csv(_up_exp, encoding="utf-8-sig", dtype=str, nrows=5)
                _up_exp.seek(0)
                _df_full_up = pd.read_csv(_up_exp, encoding="utf-8-sig", dtype=str)
                _up_exp.seek(0)
                st.caption(f"**Preview** — {len(_df_full_up)} registros, {len(_df_full_up.columns)} colunas")
                st.dataframe(_df_prev, use_container_width=True, hide_index=True)
                _valido_up, _avisos_up = exp.validar_360_csv(_df_full_up)
                for _av in _avisos_up:
                    st.warning(_av)
                if not _valido_up:
                    st.error("O arquivo não passou na validação.")
                else:
                    if "Status" in _df_full_up.columns:
                        _sc_up = _df_full_up["Status"].value_counts()
                        _cols_st = st.columns(min(len(_sc_up), 5))
                        for _i, (_s, _n) in enumerate(_sc_up.items()):
                            with _cols_st[_i % len(_cols_st)]:
                                st.metric(_s, _n)
                    if st.button("Confirmar Upload", type="primary", key="btn_exp_upload"):
                        _total_up, _av2 = exp.salvar_upload_360(_up_exp)
                        if _total_up > 0:
                            st.success(f"Upload concluído! {_total_up} registros importados.")
                            for _av in _av2:
                                st.warning(_av)
                            st.rerun()
                        else:
                            for _av in _av2:
                                st.error(_av)
            except Exception as _e:
                st.error(f"Erro ao ler o arquivo: {_e}")
        st.divider()
        st.markdown("#### Histórico de Uploads")
        _bks = exp.listar_backups_360()
        if not _bks:
            st.caption("Nenhum backup disponível.")
        else:
            for _bk in _bks[:20]:
                _bc1, _bc2 = st.columns([3, 1])
                with _bc1:
                    st.caption(f"**{_bk['nome']}** — {_bk['data'].strftime('%d/%m/%Y %H:%M')} — {_bk['tamanho']/1024:.0f} KB")
                with _bc2:
                    with open(_bk["caminho"], "rb") as _f:
                        st.download_button("Baixar", _f.read(), _bk["nome"], "text/csv", key=f"bk_exp_{_bk['nome']}")


# ══════════════════════════════════════════════════════════════════════
# DEPARTAMENTO: AGENCIAMENTO
# ══════════════════════════════════════════════════════════════════════

with tab_agenciamento:
    st.markdown(
        """
        <div style="padding: 2rem 0 1rem; text-align: center; color: #6E6E73;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🤝</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #111111;">Agenciamento — Em breve</div>
            <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                Esta seção receberá o acompanhamento de processos, analistas, clientes e alertas
                do departamento de Agenciamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    tab_ag_geral, tab_ag_analist, tab_ag_clientes, tab_ag_alertas, tab_ag_tabela, tab_ag_upload = st.tabs(
        ["Visão Geral", "Analistas", "Clientes", "Alertas e Prazos", "Tabela", "Upload"]
    )

    with tab_ag_geral:
        st.info("Em construção — dados de volume e status de Agenciamento serão exibidos aqui.")

    with tab_ag_analist:
        st.info("Em construção — distribuição de carteira por analista de Agenciamento.")

    with tab_ag_clientes:
        st.info("Em construção — concentração e análise de clientes de Agenciamento.")

    with tab_ag_alertas:
        st.info("Em construção — alertas e prazos críticos de Agenciamento.")

    with tab_ag_tabela:
        st.info("Em construção — tabela completa de processos de Agenciamento.")

    with tab_ag_upload:
        st.info("Em construção — upload da planilha de processos de Agenciamento.")
