"""Processos 360 — Dashboard de processos de importação."""

import re
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.processos360 import (
    STATUS_ORDEM,
    _br_moeda,
    calcular_alertas,
    carregar_meta,
    dados_existem,
    listar_backups,
    obter_processos,
    salvar_upload,
    validar_csv,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina, renderizar_dataframe

COLOR_NAVY = "#234055"
COLOR_NAVY_SOFT = "#36586f"
COLOR_GOLD = "#c79536"
COLOR_GREEN = "#5e8668"
COLOR_RED = "#b5423a"

STATUS_CORES = {
    "Pré-embarque": "#7ea6c7",
    "Embarque": "#4a8ab5",
    "Chegada": "#c79536",
    "Registrado/Ag.Desembaraço": "#e6a832",
    "Carregamento": "#5e8668",
    "Encerramento": "#234055",
}

MODALIDADE_CORES = {
    "OCEANFREIGHT / FCL": "#234055",
    "OCEANFREIGHT / LCL": "#4a8ab5",
    "AIRFREIGHT": "#c79536",
    "RODOVIÁRIO": "#5e8668",
    "BREAK BULK": "#8b5e3c",
    "MARÍTIMO / RODOVIÁRIO": "#7ea6c7",
    "AÉREO / MARÍTIMO": "#e6a832",
    "FERROVIÁRIO": "#6f7a84",
}

TIPO_OP_CORES = {
    "Importação Própria": "#4a8ab5",
    "Importação por Conta e Ordem": "#234055",
    "Encomenda": "#c79536",
}

# Rótulos e cores para Direto / CO3 / Encomenda (usados em cards e tabelas)
TIPO_LABELS = {
    "Importação Própria": "Direto",
    "Importação por Conta e Ordem": "CO3",
    "Encomenda": "Encomenda",
}
TIPO_CORES = {
    "Direto":    "#4a8ab5",
    "CO3":       "#234055",
    "Encomenda": "#c79536",
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
    "Processos 360",
    "Visão consolidada dos processos de importação em andamento.",
    badge=badge_text,
)


# ── Sub-abas ─────────────────────────────────────────────────────────

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


def _tag_html(tipo):
    """Gera HTML de tag colorida para tipo de operação (Direto/CO3/Encomenda)."""
    cor = TIPO_CORES.get(tipo, "#6f7a84")
    return (
        f'<span style="background:{cor};color:#fff;border-radius:5px;'
        f'padding:2px 7px;font-size:0.62rem;font-weight:800;'
        f'letter-spacing:0.04em;margin-left:4px;">{tipo}</span>'
    )


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
            total = len(df)

            # ── KPIs: Total + todos os status com percentual ──
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, rgba(255,253,248,0.96), rgba(243,237,226,0.96));
                    border: 1px solid #e3d8c5; border-radius: 20px;
                    padding: 1rem 1.4rem; margin-bottom: 1rem;
                    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
                    display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center;
                ">
                    <div style="flex: 0 0 auto; margin-right: 0.8rem;">
                        <span style="color: #6f7a84; font-size: 0.7rem; text-transform: uppercase; font-weight: 800;">Total</span><br/>
                        <span style="color: #234055; font-size: 1.8rem; font-weight: 800;">{total:,}</span>
                    </div>
                    {"".join(f'''
                    <div style="
                        flex: 1 1 0; min-width: 120px;
                        background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid {STATUS_CORES.get(s, '#ccc')};
                    ">
                        <div style="color: #6f7a84; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{s}</div>
                        <div style="color: #234055; font-size: 1.25rem; font-weight: 800;">{len(df[df["Status"] == s])}</div>
                        <div style="color: {STATUS_CORES.get(s, "#6f7a84")}; font-size: 0.78rem; font-weight: 700;">{len(df[df["Status"] == s]) / total * 100:.1f}%</div>
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
                    mod_range = [MODALIDADE_CORES.get(m, "#6f7a84") for m in mod_domain]
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
                acc_palette = ["#234055", "#4a8ab5", "#c79536", "#5e8668", "#e6a832", "#7ea6c7", "#8b5e3c", "#b5423a", "#6f7a84", "#36586f"]
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
                    tipo_range = [TIPO_OP_CORES.get(t, "#6f7a84") for t in tipo_domain]
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
            filtro_tipo = []
            _col_hdr, _col_filt = st.columns([2, 3])
            with _col_filt:
                if _tem_tipo:
                    _fcols = st.columns(len(TIPOS_ORDEM) + 1)
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

            # Aplicar filtro no DataFrame inteiro (tudo reflete o filtro)
            if filtro_tipo:
                df = df[df["_Tipo"].isin(filtro_tipo)]

            # Agregar com dados já filtrados
            analistas = df.groupby("Account").agg(
                processos=("Processo", "count"),
                clientes=("Cliente", "nunique"),
                valor_aduaneiro=("Valor Aduaneiro", "sum"),
            ).reset_index().sort_values("processos", ascending=False)

            with _col_hdr:
                _lbl_filtro = f" ({' + '.join(filtro_tipo)})" if filtro_tipo else ""
                st.markdown(f"#### {len(analistas)} Analistas{_lbl_filtro}")

            # Processos ativos por analista
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

            # ── Cards ─────────────────────────────────────────────────────
            if analistas.empty:
                st.info("Nenhum analista encontrado para o filtro selecionado.")
            cols_por_linha = 3
            for i in range(0, len(analistas), cols_por_linha):
                cols = st.columns(cols_por_linha)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx >= len(analistas):
                        break
                    row = analistas.iloc[idx]
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
                                background: linear-gradient(135deg, rgba(255,253,248,0.96), rgba(243,237,226,0.96));
                                border: 1px solid #e3d8c5;
                                border-radius: 18px;
                                padding: 1rem 1.2rem;
                                margin-bottom: 0.2rem;
                                box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
                            ">
                                <div style="font-weight: 800; color: #234055; font-size: 1.05rem;
                                            margin-bottom: 0.4rem; display:flex; align-items:center; flex-wrap:wrap; gap:2px;">
                                    {row['Account']}{tags_html}
                                </div>
                                <div style="display: flex; gap: 1.2rem; margin-bottom: 0.5rem;">
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Processos</span><br/>
                                        <span style="color: #234055; font-size: 1.3rem; font-weight: 800;">{int(row['processos'])}</span>
                                    </div>
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Ativos</span><br/>
                                        <span style="color: #234055; font-size: 1.3rem; font-weight: 800;">{n_ativos}</span>
                                    </div>
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Clientes</span><br/>
                                        <span style="color: #5e8668; font-size: 1.3rem; font-weight: 800;">{int(row['clientes'])}</span>
                                    </div>
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Valor Aduaneiro</span><br/>
                                        <span style="color: #234055; font-size: 1rem; font-weight: 700;">{_br_moeda(row['valor_aduaneiro'], 0)}</span>
                                    </div>
                                </div>
                                <div style="font-size: 0.75rem; color: #6f7a84;">{status_pills}</div>
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
                                df_cl_agg["tipos"] = [[] for _ in range(len(df_cl_agg))]

                            # Renderizar como tabela HTML com tags coloridas
                            rows_html = ""
                            for _, cl_row in df_cl_agg.iterrows():
                                tags_cl = " ".join(
                                    f'<span style="background:{TIPO_CORES[t]};color:#fff;'
                                    f'border-radius:4px;padding:1px 6px;font-size:0.6rem;'
                                    f'font-weight:800;letter-spacing:0.03em;">{t}</span>'
                                    for t in cl_row["tipos"]
                                )
                                rows_html += (
                                    f'<tr style="border-bottom:1px solid #f0e8d8;">'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;color:#234055;">'
                                    f'{cl_row["_ClienteBase"]}</td>'
                                    f'<td style="padding:5px 8px;font-size:0.8rem;text-align:center;'
                                    f'color:#234055;font-weight:700;">{int(cl_row["processos"])}</td>'
                                    f'<td style="padding:5px 8px;">{tags_cl}</td>'
                                    f'</tr>'
                                )
                            st.markdown(
                                f'<table style="width:100%;border-collapse:collapse;">'
                                f'<thead><tr style="background:#f6f0e4;">'
                                f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6f7a84;text-transform:uppercase;font-weight:700;">Cliente</th>'
                                f'<th style="text-align:center;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6f7a84;text-transform:uppercase;font-weight:700;">Proc.</th>'
                                f'<th style="text-align:left;padding:6px 8px;font-size:0.67rem;'
                                f'color:#6f7a84;text-transform:uppercase;font-weight:700;">Tipo</th>'
                                f'</tr></thead><tbody>{rows_html}</tbody></table>',
                                unsafe_allow_html=True,
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
                    background: linear-gradient(135deg, rgba(255,253,248,0.96), rgba(243,237,226,0.96));
                    border: 1px solid #e3d8c5; border-radius: 20px;
                    padding: 1rem 1.4rem; margin-bottom: 1rem;
                    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
                    display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center;
                ">
                    <div style="flex: 0 0 auto; margin-right: 0.8rem;">
                        <span style="color: #6f7a84; font-size: 0.7rem; text-transform: uppercase; font-weight: 800;">Clientes</span><br/>
                        <span style="color: #5e8668; font-size: 1.8rem; font-weight: 800;">{total_clientes}</span>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #4a8ab5;
                    ">
                        <div style="color: #6f7a84; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Direto</div>
                        <div style="color: #4a8ab5; font-size: 1.25rem; font-weight: 800;">{_cli_direto}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #234055;
                    ">
                        <div style="color: #6f7a84; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">CO3</div>
                        <div style="color: #234055; font-size: 1.25rem; font-weight: 800;">{_cli_co3}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 110px;
                        background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #c79536;
                    ">
                        <div style="color: #6f7a84; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Encomenda</div>
                        <div style="color: #c79536; font-size: 1.25rem; font-weight: 800;">{_cli_encomenda}</div>
                    </div>
                    <div style="
                        flex: 1 1 0; min-width: 150px;
                        background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 14px;
                        padding: 0.55rem 0.75rem; text-align: center;
                        border-left: 4px solid #234055;
                    ">
                        <div style="color: #6f7a84; font-size: 0.65rem; text-transform: uppercase; font-weight: 700;">Valor Aduaneiro</div>
                        <div style="color: #234055; font-size: 1.05rem; font-weight: 800;">{_br_moeda(_val_total, 0)}</div>
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
                    _cor = TIPO_CORES.get(_rr["Tipo"], "#6f7a84")
                    _pct = _rr["Percentual"]
                    _n = int(_rr["Processos"])
                    _repr_html += (
                        f'<div style="flex:1 1 0;min-width:180px;'
                        f'background:linear-gradient(135deg,rgba(255,253,248,0.96),rgba(243,237,226,0.96));'
                        f'border:1px solid #e3d8c5;border-radius:14px;padding:0.8rem 1rem;'
                        f'border-left:5px solid {_cor};">'
                        f'<div style="font-size:0.72rem;color:#6f7a84;text-transform:uppercase;'
                        f'font-weight:700;margin-bottom:0.3rem;">{_rr["Tipo"]}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:0.5rem;">'
                        f'<span style="font-size:1.6rem;font-weight:800;color:{_cor};">{_n}</span>'
                        f'<span style="font-size:0.85rem;font-weight:700;color:#6f7a84;">'
                        f'{_pct:.1f}%</span>'
                        f'</div>'
                        f'<div style="background:#e8e0d4;border-radius:4px;height:8px;'
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
                        f'<span style="background:{_tipo_cor};color:#fff;border-radius:6px;'
                        f'padding:3px 14px;font-size:0.78rem;font-weight:800;">{_tipo_label}</span>'
                        f' <span style="color:#6f7a84;font-size:0.78rem;font-weight:600;">'
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
                _palette_extra = ["#6f7a84", "#a1887f", "#78909c", "#8d6e63", "#90a4ae"]
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
                f'<div style="background:rgba(199,149,54,0.08);border:1px solid #e3d8c5;'
                f'border-radius:12px;padding:0.7rem 1rem;margin-bottom:0.8rem;'
                f'font-size:0.88rem;color:#234055;">'
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
                    f'<span style="background:{TIPO_CORES[t]};color:#fff;'
                    f'border-radius:4px;padding:1px 6px;font-size:0.6rem;'
                    f'font-weight:800;letter-spacing:0.03em;">{t}</span>'
                    for t in _tipos_por_cliente.get(_r["Cliente"], [])
                )
                _val_ad = _br_moeda(_r["Valor Aduaneiro"], 0) if "Valor Aduaneiro" in _r.index and pd.notna(_r.get("Valor Aduaneiro")) else "—"
                _cnt = int(_r["Containers"]) if "Containers" in _r.index and pd.notna(_r.get("Containers")) else "—"
                _st_info = _status_por_cliente.get(_r["Cliente"], "")

                _rows_html_cli += (
                    f'<tr style="border-bottom:1px solid #f0e8d8;">'
                    f'<td style="padding:6px 8px;font-size:0.82rem;color:#234055;font-weight:600;">{_r["Cliente"]}</td>'
                    f'<td style="padding:6px 8px;font-size:0.82rem;text-align:center;color:#234055;font-weight:800;">{int(_r["Processos"])}</td>'
                    f'<td style="padding:6px 8px;font-size:0.8rem;color:#234055;">{_val_ad}</td>'
                    f'<td style="padding:6px 8px;font-size:0.8rem;text-align:center;color:#234055;">{_cnt}</td>'
                    f'<td style="padding:6px 8px;">{_tags_cli}</td>'
                    f'<td style="padding:6px 8px;font-size:0.7rem;color:#6f7a84;">{_st_info}</td>'
                    f'</tr>'
                )

            st.markdown(
                f'<div style="max-height:500px;overflow-y:auto;border:1px solid #e3d8c5;border-radius:12px;">'
                f'<table style="width:100%;border-collapse:collapse;">'
                f'<thead><tr style="background:#f6f0e4;position:sticky;top:0;">'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Cliente</th>'
                f'<th style="text-align:center;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Proc.</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Valor Aduaneiro</th>'
                f'<th style="text-align:center;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Cnt.</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Tipo</th>'
                f'<th style="text-align:left;padding:8px;font-size:0.67rem;color:#6f7a84;text-transform:uppercase;font-weight:700;">Status</th>'
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
            alertas = calcular_alertas(df)

            # Resumo compacto no topo (inline HTML, sem st.metric grande)
            items = [
                ("Cnt. Vencido", len(alertas.get("container_vencido", [])), COLOR_RED),
                ("Perdimento", len(alertas["perdimento_proximo"]), COLOR_RED),
                ("Cnt. Vencendo", len(alertas["container_vencendo"]), "#8b5e3c"),
                ("Canal Vermelho", len(alertas["canal_vermelho"]), COLOR_RED),
                ("Canal Amarelo", len(alertas["canal_amarelo"]), COLOR_GOLD),
                ("Saldo Negativo", len(alertas["saldo_negativo"]), COLOR_RED),
                ("Proc. Parado", len(alertas.get("processo_parado", [])), "#6f7a84"),
                ("Follow > 10d", len(alertas["follow_desatualizado"]), "#b58c23"),
                ("Valor > R$ 1M", len(alertas["valor_alto"]), COLOR_GOLD),
                ("LI Indeferida", len(alertas["li_indeferida"]), "#6f7a84"),
            ]
            pills_html = "".join(
                f'<div style="'
                f"flex: 1 1 0; min-width: 100px; text-align: center;"
                f"background: rgba(255,255,255,0.6); border: 1px solid #e3d8c5; border-radius: 12px;"
                f"padding: 0.45rem 0.5rem; border-top: 3px solid {cor};"
                f'">'
                f'<div style="color: #6f7a84; font-size: 0.6rem; text-transform: uppercase; font-weight: 700; white-space: nowrap;">{label}</div>'
                f'<div style="color: {cor if n > 0 else "#234055"}; font-size: 1.3rem; font-weight: 800;">{n}</div>'
                f"</div>"
                for label, n, cor in items
            )
            st.markdown(
                f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">{pills_html}</div>',
                unsafe_allow_html=True,
            )

            def _render_alerta(titulo, df_alerta, colunas, formato_cols=None, icon="⚠️", alerta_key=""):
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
                        renderizar_dataframe(styled, use_container_width=True, hide_index=True)
                    else:
                        renderizar_dataframe(df_show, use_container_width=True, hide_index=True)

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
                ["Processo", "Account", "Cliente", "Limite Dev. Container", "Dias Vencido"],
                {"Limite Dev. Container": fmt_data},
                icon="🚨", alerta_key="container_vencido",
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
                ["Processo", "Account", "Cliente", "Limite Dev. Container", "Dias Restantes"],
                {"Limite Dev. Container": fmt_data},
                icon="📦", alerta_key="container_vencendo",
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
                ["Processo", "Account", "Cliente", "Abertura", "Dias Parado"],
                {"Abertura": fmt_data},
                icon="💤", alerta_key="processo_parado",
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
                ["Processo", "Account", "Cliente", "Data do Follow", "Dias sem Follow"],
                {"Data do Follow": fmt_data},
                icon="📅", alerta_key="follow_desatualizado",
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
                r1c1, r1c2, r1c3, r1c4 = st.columns(4)
                with r1c1:
                    f_status = _filtro_multiselect(df, "Status", "Status", "f_status")
                with r1c2:
                    f_account = _filtro_multiselect(df, "Account", "Account (Analista)", "f_account")
                with r1c3:
                    f_cliente = _filtro_multiselect(df, "Cliente", "Cliente", "f_cliente")
                with r1c4:
                    f_modalidade = _filtro_multiselect(df, "Modalidade", "Modalidade", "f_modalidade") if "Modalidade" in df.columns else []

                r2c1, r2c2, r2c3, r2c4 = st.columns(4)
                with r2c1:
                    f_class = _filtro_multiselect(df, "Classificação", "Classificação", "f_class") if "Classificação" in df.columns else []
                with r2c2:
                    f_tipo = _filtro_multiselect(df, "Tipo de Operação", "Tipo de Operação", "f_tipo") if "Tipo de Operação" in df.columns else []
                with r2c3:
                    f_canal = _filtro_multiselect(df, "Canal", "Canal", "f_canal") if "Canal" in df.columns else []
                with r2c4:
                    f_di_tipo = _filtro_multiselect(df, "DI Tipo", "DI Tipo", "f_di_tipo") if "DI Tipo" in df.columns else []

                r3c1, r3c2, r3c3 = st.columns(3)
                with r3c1:
                    f_destino = _filtro_multiselect(df, "Destino", "Destino", "f_destino") if "Destino" in df.columns else []
                with r3c2:
                    f_situacao = _filtro_multiselect(df, "Situação", "Situação LI", "f_situacao") if "Situação" in df.columns else []
                with r3c3:
                    f_processo = st.text_input("Buscar Processo", key="f_processo", placeholder="Ex: 4458/25")

            # Aplicar filtros
            df_f = df.copy()
            if f_status:
                df_f = df_f[df_f["Status"].isin(f_status)]
            if f_account:
                df_f = df_f[df_f["Account"].isin(f_account)]
            if f_cliente:
                df_f = df_f[df_f["Cliente"].isin(f_cliente)]
            if f_modalidade:
                df_f = df_f[df_f["Modalidade"].isin(f_modalidade)]
            if f_class:
                df_f = df_f[df_f["Classificação"].isin(f_class)]
            if f_tipo:
                df_f = df_f[df_f["Tipo de Operação"].isin(f_tipo)]
            if f_canal:
                df_f = df_f[df_f["Canal"].isin(f_canal)]
            if f_di_tipo:
                df_f = df_f[df_f["DI Tipo"].isin(f_di_tipo)]
            if f_destino:
                df_f = df_f[df_f["Destino"].isin(f_destino)]
            if f_situacao:
                df_f = df_f[df_f["Situação"].isin(f_situacao)]
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
            renderizar_dataframe(styled, use_container_width=True, hide_index=True, height=height)

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
            renderizar_dataframe(df_preview, use_container_width=True, hide_index=True)

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
