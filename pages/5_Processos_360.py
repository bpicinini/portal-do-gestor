"""Processos 360 — Dashboard de processos de importação."""

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
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina

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
    "Importação Própria": "#234055",
    "Importação por Conta e Ordem": "#4a8ab5",
    "Encomenda": "#c79536",
}

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
    pills=["Visão Geral", "Analistas", "Alertas", "Tabela", "Upload"],
)


# ── Sub-abas ─────────────────────────────────────────────────────────

tab_geral, tab_analista, tab_alertas, tab_tabela, tab_upload = st.tabs(
    ["Visão Geral", "Visão por Analista", "Alertas e Prazos", "Tabela de Processos", "Upload"]
)


def _msg_sem_dados():
    st.info("Nenhum dado carregado. Acesse a aba **Upload** para importar a planilha.")


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

            # ── KPIs linha 2: alertas ──
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                n_neg = len(alertas["saldo_negativo"])
                st.metric("Saldo Negativo", n_neg, delta=f"{n_neg} processos" if n_neg else None, delta_color="inverse")
            with c2:
                n_verm = len(alertas["canal_vermelho"])
                st.metric("Canal Vermelho", n_verm, delta=f"{n_verm} processos" if n_verm else None, delta_color="inverse")
            with c3:
                n_follow = len(alertas["follow_desatualizado"])
                st.metric("Follow > 10 dias", n_follow, delta=f"{n_follow} processos" if n_follow else None, delta_color="inverse")
            with c4:
                total_cnt = int(df["Qtd. Container"].sum()) if "Qtd. Container" in df.columns else 0
                st.metric("Containers", f"{total_cnt:,}".replace(",", "."))

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
                        y=alt.Y("Status:N", sort=STATUS_ORDEM, title=None),
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
                    mod_domain = df_mod["Modalidade"].tolist()
                    mod_range = [MODALIDADE_CORES.get(m, "#6f7a84") for m in mod_domain]
                    chart_mod = (
                        alt.Chart(df_mod)
                        .mark_bar(cornerRadiusEnd=8)
                        .encode(
                            x=alt.X("Quantidade:Q", title="Processos"),
                            y=alt.Y("Modalidade:N", sort="-x", title=None),
                            color=alt.Color(
                                "Modalidade:N",
                                scale=alt.Scale(domain=mod_domain, range=mod_range),
                                legend=None,
                            ),
                            tooltip=[alt.Tooltip("Modalidade:N"), alt.Tooltip("Quantidade:Q", format=",d")],
                        )
                        .properties(height=220)
                    )
                    st.altair_chart(chart_mod, use_container_width=True)

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
                        y=alt.Y("Account:N", sort="-x", title=None),
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
                    tipo_domain = df_tipo["Tipo"].tolist()
                    tipo_range = [TIPO_OP_CORES.get(t, "#6f7a84") for t in tipo_domain]
                    chart_tipo = (
                        alt.Chart(df_tipo)
                        .mark_bar(cornerRadiusEnd=8)
                        .encode(
                            x=alt.X("Quantidade:Q", title="Processos"),
                            y=alt.Y("Tipo:N", sort="-x", title=None),
                            color=alt.Color(
                                "Tipo:N",
                                scale=alt.Scale(domain=tipo_domain, range=tipo_range),
                                legend=None,
                            ),
                            tooltip=[alt.Tooltip("Tipo:N"), alt.Tooltip("Quantidade:Q", format=",d")],
                        )
                        .properties(height=180)
                    )
                    st.altair_chart(chart_tipo, use_container_width=True)

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
            analistas = df.groupby("Account").agg(
                processos=("Processo", "count"),
                clientes=("Cliente", "nunique"),
                valor_aduaneiro=("Valor Aduaneiro", "sum"),
            ).reset_index().sort_values("processos", ascending=False)

            st.markdown(f"#### {len(analistas)} Analistas")

            # Cards em grid com expander para clientes
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
                                <div style="font-weight: 800; color: #234055; font-size: 1.05rem; margin-bottom: 0.4rem;">
                                    {row['Account']}
                                </div>
                                <div style="display: flex; gap: 1.2rem; margin-bottom: 0.5rem;">
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Processos</span><br/>
                                        <span style="color: #234055; font-size: 1.3rem; font-weight: 800;">{int(row['processos'])}</span>
                                    </div>
                                    <div>
                                        <span style="color: #6f7a84; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Clientes</span><br/>
                                        <span style="color: #234055; font-size: 1.3rem; font-weight: 800;">{int(row['clientes'])}</span>
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

                        # Expander com breakdown por cliente
                        with st.expander("Ver clientes", expanded=False):
                            df_clientes = (
                                df_an.groupby("Cliente")
                                .agg(
                                    processos=("Processo", "count"),
                                    valor_aduaneiro=("Valor Aduaneiro", "sum"),
                                )
                                .reset_index()
                                .sort_values("processos", ascending=False)
                            )
                            df_clientes_show = df_clientes.rename(columns={
                                "Cliente": "Cliente",
                                "processos": "Processos",
                                "valor_aduaneiro": "Valor Aduaneiro",
                            })
                            styled_cl = df_clientes_show.style.format({
                                "Valor Aduaneiro": lambda v: _br_moeda(v, 0) if pd.notna(v) else "",
                            })
                            h = min(38 + len(df_clientes_show) * 35 + 6, 350)
                            st.dataframe(styled_cl, use_container_width=True, hide_index=True, height=h)

            st.divider()

            # Gráfico empilhado por analista/status
            st.caption("**Distribuição de processos por Analista e Status**")
            df_pivot = df.groupby(["Account", "Status"]).size().reset_index(name="Quantidade")
            df_pivot["Status"] = pd.Categorical(df_pivot["Status"], categories=STATUS_ORDEM, ordered=True)

            ordem_analistas = (
                df_pivot.groupby("Account")["Quantidade"]
                .sum()
                .sort_values(ascending=True)
                .index.tolist()
            )

            chart_analista = (
                alt.Chart(df_pivot)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("Quantidade:Q", title="Processos", stack="zero"),
                    y=alt.Y("Account:N", sort=ordem_analistas, title=None),
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
                .properties(height=max(350, len(ordem_analistas) * 28))
            )
            st.altair_chart(chart_analista, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 3: ALERTAS E PRAZOS CRÍTICOS
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
                ("Saldo Negativo", len(alertas["saldo_negativo"]), COLOR_RED),
                ("Valor > R$ 1M", len(alertas["valor_alto"]), COLOR_GOLD),
                ("Follow > 10d", len(alertas["follow_desatualizado"]), "#b58c23"),
                ("Canal Vermelho", len(alertas["canal_vermelho"]), COLOR_RED),
                ("Container", len(alertas["container_vencendo"]), "#8b5e3c"),
                ("Perdimento", len(alertas["perdimento_proximo"]), COLOR_RED),
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

            def _render_alerta(titulo, df_alerta, colunas, formato_cols=None, critico=False):
                n = len(df_alerta)
                if n == 0:
                    return
                icon = "🔴" if critico else "⚠️"
                with st.expander(f"{icon} {titulo} ({n})", expanded=critico):
                    cols_existentes = [c for c in colunas if c in df_alerta.columns]
                    df_show = df_alerta[cols_existentes].copy()
                    fmt = {}
                    if formato_cols:
                        for col, fn in formato_cols.items():
                            if col in df_show.columns:
                                fmt[col] = fn
                    if fmt:
                        styled = df_show.style.format(fmt)
                        st.dataframe(styled, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_show, use_container_width=True, hide_index=True)

            fmt_moeda = lambda v: _br_moeda(v) if pd.notna(v) else ""
            fmt_data = lambda v: v.strftime("%d/%m/%Y") if pd.notna(v) else ""

            def _safe_sort(df_a, col, **kwargs):
                if len(df_a) > 0 and col in df_a.columns:
                    return df_a.sort_values(col, **kwargs)
                return df_a

            # Perdimento próximo (MAIS CRÍTICO) — ordenado por dias restantes
            if len(alertas["perdimento_proximo"]) > 0:
                st.error(f"⚠️ {len(alertas['perdimento_proximo'])} processo(s) com limite de perdimento nos próximos 10 dias!")
            _render_alerta(
                "Limite para Perdimento (< 10 dias)",
                _safe_sort(alertas["perdimento_proximo"], "Dias Restantes"),
                ["Processo", "Account", "Cliente", "Limite para Perdimento", "Dias Restantes"],
                {"Limite para Perdimento": fmt_data},
                critico=True,
            )

            # Container vencendo — ordenado por dias restantes (mais urgente primeiro)
            _render_alerta(
                "Container Vencendo (< 5 dias)",
                _safe_sort(alertas["container_vencendo"], "Dias Restantes"),
                ["Processo", "Account", "Cliente", "Limite Dev. Container", "Dias Restantes"],
                {"Limite Dev. Container": fmt_data},
                critico=True,
            )

            # Canal Vermelho — ordenado pela data de registro (mais antigo primeiro)
            _render_alerta(
                "Canal Vermelho",
                _safe_sort(alertas["canal_vermelho"], "Registro da DI", na_position="first"),
                ["Processo", "Account", "Cliente", "Registro da DI", "Follow"],
                {"Registro da DI": fmt_data},
            )

            # Saldo negativo — ordenado por saldo (mais negativo primeiro)
            _render_alerta(
                "Saldo Negativo",
                _safe_sort(alertas["saldo_negativo"], "Saldo"),
                ["Processo", "Account", "Cliente", "Saldo", "Valor Aduaneiro"],
                {"Saldo": fmt_moeda, "Valor Aduaneiro": fmt_moeda},
            )

            # Valor aduaneiro alto — ordenado por valor (maior primeiro)
            _render_alerta(
                "Valor Aduaneiro > R$ 1M",
                _safe_sort(alertas["valor_alto"], "Valor Aduaneiro", ascending=False),
                ["Processo", "Account", "Cliente", "Valor Aduaneiro", "Canal"],
                {"Valor Aduaneiro": fmt_moeda},
            )

            # Follow desatualizado — ordenado por dias sem follow (mais dias primeiro)
            _render_alerta(
                "Follow-up desatualizado (> 10 dias)",
                _safe_sort(alertas["follow_desatualizado"], "Dias sem Follow", ascending=False),
                ["Processo", "Account", "Cliente", "Data do Follow", "Dias sem Follow"],
                {"Data do Follow": fmt_data},
            )

            # LI indeferida
            _render_alerta(
                "LI/LPCO Indeferida",
                alertas["li_indeferida"],
                ["Processo", "Account", "Cliente", "Situação", "LPCO Data"],
                {"LPCO Data": fmt_data},
            )


# ══════════════════════════════════════════════════════════════════════
# SUB-ABA 4: TABELA DE PROCESSOS
# ══════════════════════════════════════════════════════════════════════

with tab_tabela:
    if not dados_existem():
        _msg_sem_dados()
    else:
        df = obter_processos()
        if df.empty:
            _msg_sem_dados()
        else:
            with st.expander("Filtros", expanded=True):
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
# SUB-ABA 5: UPLOAD
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
