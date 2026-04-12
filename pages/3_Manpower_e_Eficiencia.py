from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.departamentos import listar_departamentos
from utils.manpower import (
    calcular_manpower_por_departamento,
    listar_performance,
    obter_manpower_para_performance,
    salvar_performance,
)
from utils.pessoas import listar_colaboradores
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina
from utils import agenciamento as ag

DEPARTAMENTO_COM_DADOS = "Importação"
MESES_PT = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_ORDEM = MESES_PT[1:]
COLOR_NAVY = "#31586c"
COLOR_NAVY_DARK = "#234055"
COLOR_GOLD = "#d6b36a"
COLOR_GREEN = "#6d8e65"

garantir_autenticado()
aplicar_estilos_globais()
renderizar_cabecalho_pagina(
    "KPIs",
    "Painel central de eficiencia, manpower e volume score, com leitura por departamento.",
    badge="Estrutura em evolucao",
)

departamentos = listar_departamentos()
departamentos_por_nome = {departamento["nome"]: departamento for departamento in departamentos}
nomes_departamentos = [departamento["nome"] for departamento in departamentos]
# Adicionar Agenciamento se dados existem e não está na lista
if ag.dados_existem() and "Agenciamento" not in nomes_departamentos:
    nomes_departamentos.append("Agenciamento")
indice_padrao = nomes_departamentos.index(DEPARTAMENTO_COM_DADOS) if DEPARTAMENTO_COM_DADOS in nomes_departamentos else 0

st.markdown("#### Departamento")
departamento_selecionado = st.radio(
    "Departamento",
    nomes_departamentos,
    index=indice_padrao,
    horizontal=True,
    label_visibility="collapsed",
    key="kpi_departamento",
)

departamento_atual = departamentos_por_nome.get(departamento_selecionado, {})
departamento_id = departamento_atual.get("id")
_eh_importacao = departamento_selecionado == DEPARTAMENTO_COM_DADOS
_eh_agenciamento = departamento_selecionado == "Agenciamento" and ag.dados_existem()
tem_dados_departamento = _eh_importacao or _eh_agenciamento

if not tem_dados_departamento:
    st.caption(
        f"{departamento_selecionado} ja esta preparado no filtro superior, "
        "mas os dados de KPIs ainda nao foram carregados para esse departamento."
    )

alt.renderers.set_embed_options(
    formatLocale={
        "decimal": ",",
        "thousands": ".",
        "grouping": [3],
        "currency": ["R$ ", ""],
    }
)


def _br(val, dec=2):
    if val is None or (isinstance(val, float) and __import__("math").isnan(val)):
        return "—"
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _br_pct(val, dec=1):
    if val is None or (isinstance(val, float) and __import__("math").isnan(val)):
        return "—"
    return _br(val, dec) + "%"


def _br_int(val):
    return _br(val, 0) if val is not None else "—"


def _nome_mes(val):
    if pd.isna(val):
        return ""
    try:
        return MESES_PT[int(val)]
    except (TypeError, ValueError, IndexError):
        return str(val)


def _yscale(series, pad=0.08):
    serie = series.dropna()
    if serie.empty:
        return alt.Scale(domain=[0, 1])
    lo = serie.min()
    hi = serie.max()
    margin = (hi - lo) * pad if hi != lo else max(abs(hi) * pad, 0.5)
    return alt.Scale(domain=[lo - margin, hi + margin])


def _render_metricas_vazias(metricas):
    cols = st.columns(len(metricas))
    for col, (label, value) in zip(cols, metricas):
        with col:
            st.metric(label, value)


@st.cache_data(show_spinner=False)
def carregar_score_base():
    base_dir = Path(__file__).resolve().parents[1] / "arquivos base"
    arquivos = sorted(base_dir.glob("*performance (2).xlsx"))
    if not arquivos:
        return pd.DataFrame()

    df = pd.read_excel(arquivos[0], sheet_name="Export")
    df = df.rename(columns=lambda col: str(col).strip())
    for coluna in [
        "Score Performance",
        "Média mensal Score",
        "Abertos",
        "Embarcados",
        "Chegadas Confirmadas",
        "Registros",
        "Liberados Fatur.",
    ]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df.dropna(how="all")


def chart_perf_meta(df_chart):
    df = df_chart.reset_index()[["periodo", "performance", "meta"]].dropna(subset=["performance"]).copy()
    df.columns = ["Mês", "Eficiência", "Meta"]
    df_melt = df.melt(id_vars="Mês", var_name="Indicador", value_name="Valor")
    yscale = _yscale(df_melt["Valor"])
    return (
        alt.Chart(df_melt)
        .mark_line(point=alt.OverlayMarkDef(filled=True, size=70))
        .encode(
            x=alt.X("Mês:N", sort=MESES_ORDEM, title=None),
            y=alt.Y("Valor:Q", scale=yscale, title="Eficiência"),
            color=alt.Color(
                "Indicador:N",
                legend=alt.Legend(title=""),
                scale=alt.Scale(range=[COLOR_NAVY_DARK, COLOR_GOLD]),
            ),
            tooltip=[
                alt.Tooltip("Mês:N"),
                alt.Tooltip("Indicador:N"),
                alt.Tooltip("Valor:Q", format=",.1f"),
            ],
        )
        .properties(height=240)
    )


def chart_volume_yoy(df_ano, df_prev, ano):
    cur = df_ano[["mes", "volume_score"]].dropna(subset=["volume_score"]).copy()
    cur["Ano"] = str(int(ano))
    frames = [cur]
    if df_prev is not None and not df_prev.empty:
        prev = df_prev[["mes", "volume_score"]].dropna(subset=["volume_score"]).copy()
        prev["Ano"] = str(int(ano) - 1)
        frames.append(prev)
    df_all = pd.concat(frames, ignore_index=True)
    df_all["Mês"] = df_all["mes"].apply(lambda mes: MESES_PT[int(mes)])
    df_all = df_all.rename(columns={"volume_score": "Volume"})
    return (
        alt.Chart(df_all)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Mês:N", sort=MESES_ORDEM, title=None),
            y=alt.Y("Volume:Q", scale=alt.Scale(zero=True, nice=True), title="Volume (Score)"),
            color=alt.Color(
                "Ano:N",
                legend=alt.Legend(title="Ano"),
                scale=alt.Scale(range=[COLOR_GOLD, COLOR_NAVY]),
            ),
            xOffset=alt.XOffset("Ano:N"),
            tooltip=[
                alt.Tooltip("Mês:N"),
                alt.Tooltip("Ano:N"),
                alt.Tooltip("Volume:Q", format=",d"),
            ],
        )
        .properties(height=240)
    )


def chart_mp_ano(df_chart):
    df = df_chart.reset_index()[["periodo", "manpower"]].dropna().copy()
    yscale = _yscale(df["manpower"])
    return (
        alt.Chart(df)
        .mark_line(
            point=alt.OverlayMarkDef(filled=True, fill=COLOR_GOLD, stroke=COLOR_NAVY_DARK, size=70),
            color=COLOR_NAVY,
            strokeWidth=3,
        )
        .encode(
            x=alt.X("periodo:N", sort=None, title=None),
            y=alt.Y("manpower:Q", scale=yscale, title="Manpower"),
            tooltip=[
                alt.Tooltip("periodo:N", title="Mês"),
                alt.Tooltip("manpower:Q", format=",.2f", title="Manpower"),
            ],
        )
        .properties(height=240)
    )


def chart_mp_historico(df_all):
    df = df_all.sort_values(["ano", "mes"]).copy()
    df["periodo"] = df.apply(lambda row: f"{int(row['ano'])}-{MESES_PT[int(row['mes'])]}", axis=1)
    df = df.dropna(subset=["manpower"])
    yscale = _yscale(df["manpower"])
    return (
        alt.Chart(df)
        .mark_line(
            point=alt.OverlayMarkDef(filled=True, fill="#fffdf8", stroke=COLOR_NAVY_DARK, size=62),
            color=COLOR_NAVY_DARK,
            strokeWidth=3,
        )
        .encode(
            x=alt.X("periodo:N", sort=None, title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y("manpower:Q", scale=yscale, title="Manpower"),
            tooltip=[
                alt.Tooltip("periodo:N", title="Período"),
                alt.Tooltip("manpower:Q", format=",.2f", title="Manpower"),
            ],
        )
        .properties(height=220)
    )


def chart_yoy_line(df_ano, df_prev, ano, col, titulo, fmt=",.1f"):
    cur = df_ano[["mes", col]].copy()
    cur["Ano"] = str(int(ano))
    frames = [cur]
    if df_prev is not None and not df_prev.empty and col in df_prev.columns:
        prev = df_prev[["mes", col]].copy()
        prev["Ano"] = str(int(ano) - 1)
        frames.append(prev)
    df_all = pd.concat(frames, ignore_index=True)
    df_all["Mês"] = df_all["mes"].apply(lambda mes: MESES_PT[int(mes)])
    df_all = df_all.rename(columns={col: titulo})
    df_all = df_all.dropna(subset=[titulo])
    yscale = _yscale(df_all[titulo])
    return (
        alt.Chart(df_all)
        .mark_line(point=alt.OverlayMarkDef(filled=True, size=68), strokeWidth=3)
        .encode(
            x=alt.X("Mês:N", sort=MESES_ORDEM, title=None),
            y=alt.Y(f"{titulo}:Q", scale=yscale, title=titulo),
            color=alt.Color(
                "Ano:N",
                legend=alt.Legend(title="Ano"),
                scale=alt.Scale(range=[COLOR_GOLD, COLOR_NAVY_DARK]),
            ),
            tooltip=[
                alt.Tooltip("Mês:N"),
                alt.Tooltip("Ano:N"),
                alt.Tooltip(f"{titulo}:Q", format=fmt),
            ],
        )
        .properties(height=240)
    )


def chart_score_ranking(df_score):
    return (
        alt.Chart(df_score)
        .mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY)
        .encode(
            x=alt.X("Score Performance:Q", title="Volume (Score)"),
            y=alt.Y("Analista:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300)),
            tooltip=[
                alt.Tooltip("Analista:N"),
                alt.Tooltip("Score Performance:Q", format=",.2f"),
                alt.Tooltip("Média mensal Score:Q", format=",.2f"),
                alt.Tooltip("Registros:Q", format=",.0f"),
            ],
        )
        .properties(height=max(320, len(df_score) * 24))
    )


def cor_meta(val):
    if val is None or not isinstance(val, (int, float)):
        return ""
    return "color: green; font-weight: bold" if val >= 100 else "color: #9a4a32; font-weight: bold"


def render_tabela_performance(df_ano):
    df_show = df_ano[["mes", "volume_score", "manpower", "performance", "meta", "pct_meta"]].copy()
    df_show.columns = ["Mês", "Volume", "Manpower", "Eficiência", "Meta", "% Meta"]
    df_show = df_show[df_show["Volume"].notna() & (df_show["Volume"] > 0)]
    df_show["% Meta"] = df_show["% Meta"].apply(
        lambda val: round(val * 100, 1) if pd.notna(val) and val is not None else None
    )

    styled = (
        df_show.style.map(cor_meta, subset=["% Meta"]).format(
            {
                "Mês": _nome_mes,
                "Volume": lambda val: _br_int(val) if pd.notna(val) else "",
                "Manpower": lambda val: _br(val, 2) if pd.notna(val) else "",
                "Eficiência": lambda val: _br(val, 1) if pd.notna(val) else "",
                "Meta": lambda val: _br(val, 1) if pd.notna(val) else "",
                "% Meta": lambda val: _br_pct(val, 1) if pd.notna(val) and val is not None else "—",
            }
        )
    )
    n_linhas = len(df_show)
    height = min(38 + n_linhas * 37 + 6, 493)
    st.dataframe(styled, use_container_width=True, hide_index=True, height=height)


def resumir_eficiencia_ano(df_ano, df_prev, ano):
    registros = df_ano.to_dict("records")
    volumes = [registro["volume_score"] for registro in registros if registro.get("volume_score")]
    eficiencias = [registro["performance"] for registro in registros if registro.get("performance")]
    manpowers = [registro["manpower"] for registro in registros if registro.get("manpower")]
    pcts = [registro["pct_meta"] for registro in registros if registro.get("pct_meta")]

    resumo = {
        "registros": registros,
        "volume_medio": sum(volumes) / len(volumes) if volumes else None,
        "eficiencia_media": sum(eficiencias) / len(eficiencias) if eficiencias else None,
        "manpower_medio": sum(manpowers) / len(manpowers) if manpowers else None,
        "pct_medio": sum(pcts) / len(pcts) if pcts else None,
        "delta_volume": None,
        "delta_eficiencia": None,
        "delta_mp": None,
        "mp_delta_color": "normal",
    }

    if df_prev is None or df_prev.empty:
        return resumo

    meses_com_volume = set(
        df_ano.loc[
            df_ano["volume_score"].notna() & (df_ano["volume_score"] > 0),
            "mes",
        ].tolist()
    )
    prev_registros = df_prev.to_dict("records")
    prev_volumes = [
        registro["volume_score"]
        for registro in prev_registros
        if registro.get("volume_score") and registro.get("mes") in meses_com_volume
    ]
    prev_eficiencias = [registro["performance"] for registro in prev_registros if registro.get("performance")]
    prev_manpowers = [registro["manpower"] for registro in prev_registros if registro.get("manpower")]

    if prev_volumes and resumo["volume_medio"]:
        prev_volume_medio = sum(prev_volumes) / len(prev_volumes)
        delta_volume_pct = (resumo["volume_medio"] - prev_volume_medio) / prev_volume_medio * 100
        resumo["delta_volume"] = f"{delta_volume_pct:+.1f}% vs {int(ano) - 1}".replace(".", ",")

    if prev_eficiencias and resumo["eficiencia_media"]:
        prev_media = sum(prev_eficiencias) / len(prev_eficiencias)
        delta_pct = (resumo["eficiencia_media"] - prev_media) / prev_media * 100
        resumo["delta_eficiencia"] = f"{delta_pct:+.1f}% vs {int(ano) - 1}".replace(".", ",")

    if prev_manpowers and resumo["manpower_medio"]:
        prev_mp_medio = sum(prev_manpowers) / len(prev_manpowers)
        delta_mp_pct = (resumo["manpower_medio"] - prev_mp_medio) / prev_mp_medio * 100
        resumo["delta_mp"] = f"{delta_mp_pct:+.1f}% vs {int(ano) - 1}".replace(".", ",")
        resumo["mp_delta_color"] = "inverse"

    return resumo


def render_metricas_eficiencia(resumo):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Meses", len(resumo["registros"]))
    with c2:
        st.metric(
            "Volume médio",
            _br_int(resumo["volume_medio"]) if resumo["volume_medio"] else "—",
            delta=resumo["delta_volume"],
        )
    with c3:
        st.metric(
            "MP médio",
            _br(resumo["manpower_medio"], 2) if resumo["manpower_medio"] else "—",
            delta=resumo["delta_mp"],
            delta_color=resumo["mp_delta_color"],
        )
    with c4:
        st.metric(
            "Eficiência média",
            _br(resumo["eficiencia_media"], 1) if resumo["eficiencia_media"] else "—",
            delta=resumo["delta_eficiencia"],
        )
    with c5:
        st.metric("% Meta média", _br_pct(resumo["pct_medio"] * 100, 1) if resumo["pct_medio"] else "—")


# ── Agenciamento ─────────────────────────────────────────────────────


def _ag_totais_mes(chegadas: list[dict]) -> dict[int, int]:
    """Calcula totais mensais a partir dos dados individuais de chegadas."""
    totais: dict[int, int] = {}
    for c in chegadas:
        for m, v in c["meses"].items():
            totais[m] = totais.get(m, 0) + v
    return totais


def _ag_chart_chegadas_mes(resumo, resumo_prev=None, ano=2026):
    """Gráfico de barras: chegadas por mês (com YoY se disponível)."""
    totais = _ag_totais_mes(resumo["chegadas"])
    frames = []
    for m, v in sorted(totais.items()):
        if v > 0:
            frames.append({"Mês": MESES_PT[m], "Chegadas": v, "Ano": str(ano), "mes_n": m})
    if resumo_prev:
        totais_prev = _ag_totais_mes(resumo_prev["chegadas"])
        for m, v in sorted(totais_prev.items()):
            if v > 0:
                frames.append({"Mês": MESES_PT[m], "Chegadas": v, "Ano": str(ano - 1), "mes_n": m})
    if not frames:
        return None
    df = pd.DataFrame(frames)
    has_yoy = resumo_prev is not None
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Mês:N", sort=MESES_ORDEM, title=None),
            y=alt.Y("Chegadas:Q", title="Chegadas"),
            color=alt.Color(
                "Ano:N",
                legend=alt.Legend(title="") if has_yoy else None,
                scale=alt.Scale(range=[COLOR_NAVY_DARK, COLOR_GOLD] if has_yoy else [COLOR_NAVY_DARK]),
            ),
            xOffset=alt.XOffset("Ano:N") if has_yoy else alt.value(0),
            tooltip=[
                alt.Tooltip("Mês:N"),
                alt.Tooltip("Ano:N"),
                alt.Tooltip("Chegadas:Q", format=",d"),
            ],
        )
        .properties(height=260)
    )
    return chart


def _ag_chart_etapas(resumo):
    """Donut chart com distribuição por etapa de andamento."""
    totais_etapa = {e: 0 for e in ag.ETAPAS_ANDAMENTO}
    for a in resumo["andamento"]:
        totais_etapa["Ag booking"] += a["ag_booking"]
        totais_etapa["Ag embarque"] += a["ag_embarque"]
        totais_etapa["Embarcado"] += a["embarcado"]
        totais_etapa["Ag faturamento"] += a["ag_faturamento"]
    df = pd.DataFrame([
        {"Etapa": e, "Processos": v}
        for e, v in totais_etapa.items() if v > 0
    ])
    if df.empty:
        return None
    total = df["Processos"].sum()
    cores = [ag.ETAPAS_CORES.get(e, "#6f7a84") for e in df["Etapa"]]
    donut = (
        alt.Chart(df)
        .mark_arc(innerRadius=55, outerRadius=90, cornerRadius=4)
        .encode(
            theta=alt.Theta("Processos:Q"),
            color=alt.Color(
                "Etapa:N",
                scale=alt.Scale(domain=list(df["Etapa"]), range=cores),
                legend=alt.Legend(title=None, orient="bottom", columns=2),
            ),
            tooltip=[
                alt.Tooltip("Etapa:N"),
                alt.Tooltip("Processos:Q", format=",d"),
            ],
        )
    )
    texto = (
        alt.Chart(pd.DataFrame([{"text": str(total)}]))
        .mark_text(fontSize=22, fontWeight="bold", color=COLOR_NAVY_DARK)
        .encode(text="text:N")
    )
    return alt.layer(donut, texto).properties(height=260, padding={"bottom": 30})


def _ag_chart_carga_analista(resumo):
    """Barras horizontais: carga por analista com indicador de meta."""
    rows = []
    for a in resumo["andamento"]:
        if a["total"] > 0 or a["meta_max"] > 0:
            rows.append({
                "Analista": a["analista"],
                "Total": a["total"],
                "Meta min": a["meta_min"],
                "Meta max": a["meta_max"],
                "Senioridade": a["senioridade"],
            })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY_DARK)
        .encode(
            x=alt.X("Total:Q", title="Processos em andamento"),
            y=alt.Y("Analista:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
            tooltip=[
                alt.Tooltip("Analista:N"),
                alt.Tooltip("Total:Q", format=",d"),
                alt.Tooltip("Senioridade:N"),
                alt.Tooltip("Meta min:Q", format=",d"),
                alt.Tooltip("Meta max:Q", format=",d"),
            ],
        )
    )
    # Meta range ticks
    meta_min = (
        alt.Chart(df[df["Meta min"] > 0])
        .mark_tick(color=COLOR_GOLD, thickness=3, size=20)
        .encode(
            x=alt.X("Meta min:Q"),
            y=alt.Y("Analista:N", sort="-x"),
        )
    )
    meta_max = (
        alt.Chart(df[df["Meta max"] > 0])
        .mark_tick(color="#b5423a", thickness=3, size=20)
        .encode(
            x=alt.X("Meta max:Q"),
            y=alt.Y("Analista:N", sort="-x"),
        )
    )
    return alt.layer(bars, meta_min, meta_max).properties(height=max(200, len(df) * 35))


def _ag_chart_ranking_chegadas(chegadas):
    """Ranking horizontal de chegadas acumuladas por analista."""
    df = pd.DataFrame([
        {"Analista": c["analista"], "Chegadas": c["total"]}
        for c in chegadas if c["total"] > 0
    ]).sort_values("Chegadas", ascending=False)
    if df.empty:
        return None
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY)
        .encode(
            x=alt.X("Chegadas:Q", title="Chegadas confirmadas"),
            y=alt.Y("Analista:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
            tooltip=[
                alt.Tooltip("Analista:N"),
                alt.Tooltip("Chegadas:Q", format=",d"),
            ],
        )
        .properties(height=max(220, len(df) * 32))
    )


def _ag_chart_andamento_stacked(resumo):
    """Stacked bar: processos em andamento por analista e etapa."""
    rows = []
    for a in resumo["andamento"]:
        if a["total"] == 0:
            continue
        for etapa in ag.ETAPAS_ANDAMENTO:
            key = etapa.lower().replace(" ", "_").replace(".", "")
            val = a.get(key, 0)
            if key == "ag_booking":
                val = a["ag_booking"]
            elif key == "ag_embarque":
                val = a["ag_embarque"]
            elif key == "ag_faturamento":
                val = a["ag_faturamento"]
            else:
                val = a.get("embarcado", 0)
            if val > 0:
                rows.append({
                    "Analista": a["analista"],
                    "Etapa": etapa,
                    "Processos": val,
                })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    cores = [ag.ETAPAS_CORES.get(e, "#6f7a84") for e in ag.ETAPAS_ANDAMENTO if e in df["Etapa"].values]
    etapas_presentes = [e for e in ag.ETAPAS_ANDAMENTO if e in df["Etapa"].values]
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Processos:Q", title="Processos", stack="zero"),
            y=alt.Y("Analista:N", sort=alt.EncodingSortField(field="Processos", op="sum", order="descending"),
                     title=None, axis=alt.Axis(labelLimit=250)),
            color=alt.Color(
                "Etapa:N",
                scale=alt.Scale(domain=etapas_presentes, range=cores),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            order=alt.Order("etapa_order:Q"),
            tooltip=[
                alt.Tooltip("Analista:N"),
                alt.Tooltip("Etapa:N"),
                alt.Tooltip("Processos:Q", format=",d"),
            ],
        )
        .transform_calculate(
            etapa_order="indexof(['Ag booking','Ag embarque','Embarcado','Ag faturamento'], datum.Etapa)"
        )
        .properties(height=max(220, len(df["Analista"].unique()) * 35))
    )


def _ag_chart_chegadas_analista_mes(chegadas, ano):
    """Heatmap ou grouped bar: chegadas por analista por mês."""
    rows = []
    for c in chegadas:
        for m, v in c["meses"].items():
            if v > 0:
                rows.append({
                    "Analista": c["analista"],
                    "Mês": MESES_PT[m],
                    "Chegadas": v,
                    "mes_n": m,
                })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    meses_presentes = sorted(df["mes_n"].unique())
    meses_labels = [MESES_PT[m] for m in meses_presentes]
    return (
        alt.Chart(df)
        .mark_rect(cornerRadius=4)
        .encode(
            x=alt.X("Mês:N", sort=meses_labels, title=None),
            y=alt.Y("Analista:N", title=None, axis=alt.Axis(labelLimit=250)),
            color=alt.Color(
                "Chegadas:Q",
                scale=alt.Scale(scheme="blues"),
                legend=alt.Legend(title="Chegadas"),
            ),
            tooltip=[
                alt.Tooltip("Analista:N"),
                alt.Tooltip("Mês:N"),
                alt.Tooltip("Chegadas:Q", format=",d"),
            ],
        )
        .properties(height=max(200, len(df["Analista"].unique()) * 35))
    )


def _ag_card_html(label, valor, cor=COLOR_NAVY_DARK, icone=""):
    """Card HTML estilizado para KPIs."""
    return f"""
    <div style="background:linear-gradient(135deg,{cor}ee,{cor}bb);border-radius:14px;
    padding:1rem 1.2rem;color:white;text-align:center;min-width:120px;">
        <div style="font-size:0.8rem;opacity:0.85;">{icone} {label}</div>
        <div style="font-size:1.6rem;font-weight:700;margin-top:0.2rem;">{valor}</div>
    </div>"""


def _render_agenciamento():
    """Renderiza todo o dashboard de Agenciamento."""
    anos = ag.obter_anos_disponiveis()
    if not anos:
        st.info("Nenhum dado de agenciamento encontrado. Faça upload da planilha na aba Upload.")
        return

    tab_ov, tab_an, tab_vol, tab_up = st.tabs(
        ["Overview", "Analistas", "Volume (Chegadas)", "Upload"]
    )

    # ── Overview ─────────────────────────────────────────────────────
    with tab_ov:
        st.subheader("Overview - Agenciamento")
        ano_ov = st.selectbox("Ano", anos, format_func=lambda x: str(int(x)), key="ag_ov_ano")
        dados = ag.carregar_dados(int(ano_ov))
        if not dados or "resumo" not in dados:
            st.info("Dados não encontrados.")
            return

        resumo = dados["resumo"]
        # Carregar ano anterior para comparativos
        dados_prev = ag.carregar_dados(int(ano_ov) - 1)
        resumo_prev = dados_prev["resumo"] if dados_prev and "resumo" in dados_prev else None

        total_and = resumo["total_andamento"]
        cap_max = resumo["capacidade_max"]
        cap_min = resumo["capacidade_min"]
        pct_cap = round(total_and / cap_max * 100, 1) if cap_max else 0

        analistas_ativos = [a for a in resumo["andamento"] if a["total"] > 0]
        total_chegadas = sum(c["total"] for c in resumo["chegadas"])
        totais_mes = _ag_totais_mes(resumo["chegadas"])
        meses_com_dados = len([v for v in totais_mes.values() if v > 0])
        media_mensal = round(total_chegadas / meses_com_dados) if meses_com_dados else 0

        # KPI Cards HTML
        cards_html = '<div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:1rem;">'
        cards_html += _ag_card_html("Processos em Andamento", _br_int(total_and), COLOR_NAVY_DARK, "📦")
        cards_html += _ag_card_html(
            "Capacidade", f"{_br(pct_cap, 1)}%",
            COLOR_GREEN if pct_cap >= 80 else (COLOR_GOLD if pct_cap >= 60 else "#b5423a"),
            "📊"
        )
        cards_html += _ag_card_html("Faturados YTD", _br_int(total_chegadas), COLOR_NAVY, "✅")
        cards_html += _ag_card_html("Média/mês", _br_int(media_mensal), "#4a8ab5", "📅")
        cards_html += _ag_card_html("Analistas Ativos", str(len(analistas_ativos)), COLOR_GREEN, "👤")
        cards_html += _ag_card_html(
            "Faixa Capacidade", f"{cap_min} - {cap_max}", "#6f7a84", "🎯"
        )
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # YoY delta
        if resumo_prev:
            total_chegadas_prev = sum(c["total"] for c in resumo_prev["chegadas"])
            totais_prev = _ag_totais_mes(resumo_prev["chegadas"])
            # Comparar apenas meses equivalentes
            meses_comp = [m for m in totais_mes if totais_mes[m] > 0]
            vol_comp = sum(totais_mes.get(m, 0) for m in meses_comp)
            vol_prev_comp = sum(totais_prev.get(m, 0) for m in meses_comp)
            if vol_prev_comp > 0:
                delta_pct = (vol_comp - vol_prev_comp) / vol_prev_comp * 100
                sinal = "+" if delta_pct > 0 else ""
                cor_delta = COLOR_GREEN if delta_pct > 0 else "#b5423a"
                st.markdown(
                    f'<p style="color:{cor_delta};font-weight:600;margin:0 0 0.5rem 0;">'
                    f'{sinal}{_br(delta_pct, 1)}% vs mesmo período de {int(ano_ov) - 1} '
                    f'({_br_int(vol_comp)} vs {_br_int(vol_prev_comp)})</p>',
                    unsafe_allow_html=True,
                )

        st.divider()

        # Charts row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("**Chegadas por mês**")
            chart = _ag_chart_chegadas_mes(resumo, resumo_prev, int(ano_ov))
            if chart:
                st.altair_chart(chart, use_container_width=True)

        with col2:
            st.caption("**Processos por etapa**")
            chart = _ag_chart_etapas(resumo)
            if chart:
                st.altair_chart(chart, use_container_width=True)

        with col3:
            st.caption("**Carga por analista vs Meta**")
            chart = _ag_chart_carga_analista(resumo)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            st.caption("🟡 Meta mín. &nbsp; 🔴 Meta máx.")

        # Andamento detalhado
        st.divider()
        st.markdown("#### Processos em andamento por analista")
        chart = _ag_chart_andamento_stacked(resumo)
        if chart:
            st.altair_chart(chart, use_container_width=True)

    # ── Analistas ────────────────────────────────────────────────────
    with tab_an:
        st.subheader("Analistas - Agenciamento")
        ano_an = st.selectbox("Ano", anos, format_func=lambda x: str(int(x)), key="ag_an_ano")
        dados = ag.carregar_dados(int(ano_an))
        if not dados or "resumo" not in dados:
            st.info("Dados não encontrados.")
        else:
            resumo = dados["resumo"]

            # Ranking por chegadas
            st.markdown("#### Ranking por chegadas confirmadas")
            col_rank, col_heat = st.columns([1, 1])
            with col_rank:
                chart = _ag_chart_ranking_chegadas(resumo["chegadas"])
                if chart:
                    st.altair_chart(chart, use_container_width=True)
            with col_heat:
                st.caption("**Chegadas por analista por mês**")
                chart = _ag_chart_chegadas_analista_mes(resumo["chegadas"], int(ano_an))
                if chart:
                    st.altair_chart(chart, use_container_width=True)

            # Tabela de analistas
            st.divider()
            st.markdown("#### Detalhamento por analista")

            # Montar tabela cruzando andamento + chegadas
            and_map = {a["analista"]: a for a in resumo["andamento"]}
            cheg_map = {c["analista"]: c for c in resumo["chegadas"]}
            analistas_todos = list(dict.fromkeys(
                [a["analista"] for a in resumo["andamento"]] +
                [c["analista"] for c in resumo["chegadas"]]
            ))

            totais_m = _ag_totais_mes(resumo["chegadas"])
            n_meses = len([v for v in totais_m.values() if v > 0]) or 1

            table_rows = []
            for nome in analistas_todos:
                a = and_map.get(nome, {})
                c = cheg_map.get(nome, {})
                total_and = a.get("total", 0)
                meta_min = a.get("meta_min", 0)
                meta_max = a.get("meta_max", 0)
                chegadas_total = c.get("total", 0)
                media = round(chegadas_total / n_meses, 1) if n_meses else 0
                pct_meta = round(chegadas_total / n_meses / ((meta_min + meta_max) / 2) * 100, 1) if (meta_min + meta_max) > 0 and n_meses else None

                table_rows.append({
                    "Analista": nome,
                    "Senioridade": a.get("senioridade", "—"),
                    "Em Andamento": total_and,
                    "Meta": f"{meta_min}-{meta_max}" if meta_max > 0 else "—",
                    "Chegadas": chegadas_total,
                    "Média/mês": media,
                    "% Meta (média)": pct_meta,
                })

            df_tab = pd.DataFrame(table_rows)
            if not df_tab.empty:

                def _cor_pct_meta(val):
                    if val is None or not isinstance(val, (int, float)) or pd.isna(val):
                        return ""
                    return "color: green; font-weight: bold" if val >= 100 else "color: #9a4a32; font-weight: bold"

                styled = df_tab.style.map(_cor_pct_meta, subset=["% Meta (média)"]).format({
                    "Em Andamento": lambda v: _br_int(v),
                    "Chegadas": lambda v: _br_int(v),
                    "Média/mês": lambda v: _br(v, 1) if pd.notna(v) else "—",
                    "% Meta (média)": lambda v: _br_pct(v) if v is not None and pd.notna(v) else "—",
                })
                st.dataframe(styled, use_container_width=True, hide_index=True,
                             height=min(38 + len(df_tab) * 37, 500))

            # Chegadas mensais por analista (tabela detalhada)
            st.divider()
            st.markdown("#### Chegadas mensais por analista")
            cheg_rows = []
            for c in resumo["chegadas"]:
                row = {"Analista": c["analista"]}
                for m in range(1, 13):
                    row[MESES_PT[m]] = c["meses"].get(m, "")
                row["Total"] = c["total"]
                cheg_rows.append(row)
            if cheg_rows:
                # Adicionar linha de totais
                totais_m = _ag_totais_mes(resumo["chegadas"])
                total_row = {"Analista": "TOTAL"}
                for m in range(1, 13):
                    total_row[MESES_PT[m]] = totais_m.get(m, "")
                total_row["Total"] = sum(c["total"] for c in resumo["chegadas"])
                cheg_rows.append(total_row)
                df_cheg = pd.DataFrame(cheg_rows)
                st.dataframe(df_cheg, use_container_width=True, hide_index=True,
                             height=min(38 + len(df_cheg) * 37, 500))

    # ── Volume (Chegadas) ────────────────────────────────────────────
    with tab_vol:
        st.subheader("Volume (Chegadas) - Agenciamento")
        ano_vol = st.selectbox("Ano", anos, format_func=lambda x: str(int(x)), key="ag_vol_ano")
        dados = ag.carregar_dados(int(ano_vol))
        if not dados:
            st.info("Dados não encontrados.")
        else:
            resumo = dados.get("resumo", {})
            faturados = dados.get("faturados")

            # KPIs financeiros do Faturados
            if faturados is not None and not faturados.empty:
                lucro_total = faturados["lucro_bruto"].sum() if "lucro_bruto" in faturados.columns else 0
                lucro_est = faturados["lucro_estimado"].sum() if "lucro_estimado" in faturados.columns else 0
                recebimento = faturados["total_recebimento"].sum() if "total_recebimento" in faturados.columns else 0
                pagamento = faturados["total_pagamento"].sum() if "total_pagamento" in faturados.columns else 0
                teus_total = faturados["teus"].sum() if "teus" in faturados.columns else 0
                n_processos = len(faturados)

                st.markdown("#### Resumo financeiro dos faturados")
                fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
                fc1.metric("Processos Faturados", _br_int(n_processos))
                fc2.metric("Lucro Bruto", f"R$ {_br(lucro_total, 0)}")
                fc3.metric("Lucro Estimado", f"R$ {_br(lucro_est, 0)}")
                fc4.metric("Recebimento", f"R$ {_br(recebimento, 0)}")
                fc5.metric("Pagamento", f"R$ {_br(pagamento, 0)}")
                fc6.metric("TEUS", _br(teus_total, 0))

                st.divider()

                # Distribuição por tipo de carga e modal
                col_carga, col_modal = st.columns(2)

                with col_carga:
                    st.caption("**Distribuição por tipo de carga**")
                    if "tipo_carga" in faturados.columns:
                        df_carga = faturados["tipo_carga"].value_counts().reset_index()
                        df_carga.columns = ["Tipo", "Processos"]
                        cores_carga = [ag.CARGA_CORES.get(t, "#6f7a84") for t in df_carga["Tipo"]]
                        chart_carga = (
                            alt.Chart(df_carga)
                            .mark_arc(innerRadius=50, outerRadius=85, cornerRadius=4)
                            .encode(
                                theta=alt.Theta("Processos:Q"),
                                color=alt.Color(
                                    "Tipo:N",
                                    scale=alt.Scale(domain=list(df_carga["Tipo"]), range=cores_carga),
                                    legend=alt.Legend(title=None, orient="bottom"),
                                ),
                                tooltip=[
                                    alt.Tooltip("Tipo:N"),
                                    alt.Tooltip("Processos:Q", format=",d"),
                                ],
                            )
                            .properties(height=250)
                        )
                        st.altair_chart(chart_carga, use_container_width=True)

                with col_modal:
                    st.caption("**Distribuição por modal**")
                    if "modal" in faturados.columns:
                        df_modal = faturados["modal"].value_counts().reset_index()
                        df_modal.columns = ["Modal", "Processos"]
                        cores_modal = [ag.MODAL_CORES.get(m, "#6f7a84") for m in df_modal["Modal"]]
                        chart_modal = (
                            alt.Chart(df_modal)
                            .mark_arc(innerRadius=50, outerRadius=85, cornerRadius=4)
                            .encode(
                                theta=alt.Theta("Processos:Q"),
                                color=alt.Color(
                                    "Modal:N",
                                    scale=alt.Scale(domain=list(df_modal["Modal"]), range=cores_modal),
                                    legend=alt.Legend(title=None, orient="bottom"),
                                ),
                                tooltip=[
                                    alt.Tooltip("Modal:N"),
                                    alt.Tooltip("Processos:Q", format=",d"),
                                ],
                            )
                            .properties(height=250)
                        )
                        st.altair_chart(chart_modal, use_container_width=True)

                st.divider()

                # Top 15 clientes
                st.markdown("#### Top 15 clientes por volume")
                if "cliente" in faturados.columns:
                    df_cli = (
                        faturados.groupby("cliente", as_index=False)
                        .agg(Processos=("cliente", "size"),
                             Lucro=("lucro_estimado", "sum"))
                    )
                    df_cli = df_cli.sort_values("Processos", ascending=False).head(15)
                    chart_cli = (
                        alt.Chart(df_cli)
                        .mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY_DARK)
                        .encode(
                            x=alt.X("Processos:Q", title="Processos faturados"),
                            y=alt.Y("cliente:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                            tooltip=[
                                alt.Tooltip("cliente:N", title="Cliente"),
                                alt.Tooltip("Processos:Q", format=",d"),
                                alt.Tooltip("Lucro:Q", format=",.2f", title="Lucro estimado"),
                            ],
                        )
                        .properties(height=max(300, len(df_cli) * 28))
                    )
                    st.altair_chart(chart_cli, use_container_width=True)

                # Top origens
                st.divider()
                col_orig, col_anal = st.columns(2)
                with col_orig:
                    st.markdown("#### Top 10 origens")
                    if "origem" in faturados.columns:
                        df_orig = faturados["origem"].value_counts().head(10).reset_index()
                        df_orig.columns = ["Origem", "Processos"]
                        chart_orig = (
                            alt.Chart(df_orig)
                            .mark_bar(cornerRadiusEnd=8, color="#4a8ab5")
                            .encode(
                                x=alt.X("Processos:Q", title="Processos"),
                                y=alt.Y("Origem:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                                tooltip=[alt.Tooltip("Origem:N"), alt.Tooltip("Processos:Q", format=",d")],
                            )
                            .properties(height=max(200, len(df_orig) * 28))
                        )
                        st.altair_chart(chart_orig, use_container_width=True)

                with col_anal:
                    st.markdown("#### Volume por analista (faturados)")
                    if "analista" in faturados.columns:
                        df_anal = (
                            faturados.groupby("analista", as_index=False)
                            .agg(Processos=("analista", "size"),
                                 Lucro=("lucro_estimado", "sum"))
                        )
                        df_anal = df_anal.sort_values("Processos", ascending=False)
                        chart_anal = (
                            alt.Chart(df_anal)
                            .mark_bar(cornerRadiusEnd=8, color=COLOR_NAVY)
                            .encode(
                                x=alt.X("Processos:Q", title="Processos faturados"),
                                y=alt.Y("analista:N", sort="-x", title=None, axis=alt.Axis(labelLimit=250)),
                                tooltip=[
                                    alt.Tooltip("analista:N", title="Analista"),
                                    alt.Tooltip("Processos:Q", format=",d"),
                                    alt.Tooltip("Lucro:Q", format=",.2f", title="Lucro estimado"),
                                ],
                            )
                            .properties(height=max(200, len(df_anal) * 28))
                        )
                        st.altair_chart(chart_anal, use_container_width=True)
            else:
                st.info("Dados de faturados não disponíveis para este ano.")

    # ── Upload ───────────────────────────────────────────────────────
    with tab_up:
        st.subheader("Upload - Agenciamento")
        st.caption(
            "Faça upload da planilha de relatório de processos do agenciamento. "
            "O arquivo deve conter sheets 'Resumo YYYY' e opcionalmente 'Faturados YYYY HS'."
        )

        meta = ag.carregar_meta()
        if meta:
            dt = meta.get("ultimo_upload", "")
            if dt:
                try:
                    dt_fmt = pd.Timestamp(dt).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    dt_fmt = dt
                st.info(
                    f"Último upload: **{dt_fmt}** — "
                    f"Arquivo: {meta.get('arquivo_original', '—')} — "
                    f"Sheets: {', '.join(meta.get('sheets', []))}"
                )

        uploaded = st.file_uploader(
            "Planilha de agenciamento (.xlsx)",
            type=["xlsx"],
            key="ag_upload",
        )
        if uploaded:
            if st.button("Processar upload", type="primary", key="ag_upload_btn"):
                with st.spinner("Processando..."):
                    ok, msg = ag.salvar_upload(uploaded)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# ── Renderização condicional ─────────────────────────────────────────

if _eh_agenciamento:
    _render_agenciamento()
else:
    tab_overview, tab_perf, tab_mw, tab_score = st.tabs(["Overview", "Eficiência", "Manpower", "Volume (Score)"])

    with tab_overview:
        st.subheader(f"Overview - {departamento_selecionado}")

        if not tem_dados_departamento:
            _render_metricas_vazias(
                [
                    ("Meses", "0"),
                    ("Volume médio", "0"),
                    ("MP médio", "0,00"),
                    ("Eficiência média", "0,0"),
                    ("% Meta média", "0,0%"),
                ]
            )
            st.info("Esse departamento ainda nao possui base de KPIs carregada.")
        else:
            performance = listar_performance()

            if not performance:
                st.info("Nenhum dado de eficiencia registrado.")
            else:
                df_perf = pd.DataFrame(performance).sort_values(["ano", "mes"], ascending=[True, True]).reset_index(drop=True)
                anos = sorted(df_perf["ano"].unique(), reverse=True)
                ano_overview = st.selectbox(
                    "Ano em destaque",
                    anos,
                    format_func=lambda val: str(int(val)),
                    key="overview_ano",
                )
                df_ano = df_perf[df_perf["ano"] == ano_overview].copy()
                df_prev_full = df_perf[df_perf["ano"] == ano_overview - 1].copy()
                df_prev = df_prev_full if not df_prev_full.empty else None
                resumo = resumir_eficiencia_ano(df_ano, df_prev, ano_overview)

                render_metricas_eficiencia(resumo)
                st.divider()

                df_chart = df_ano.copy()
                df_chart["periodo"] = df_chart["mes"].apply(lambda mes: MESES_PT[int(mes)])
                df_chart = df_chart.set_index("periodo")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption("**Eficiência vs Meta**")
                    st.altair_chart(chart_perf_meta(df_chart), use_container_width=True)
                with col2:
                    label_prev = f" - vs {int(ano_overview) - 1}" if df_prev is not None else ""
                    st.caption(f"**Volume (Score){label_prev}**")
                    st.altair_chart(chart_volume_yoy(df_ano, df_prev, ano_overview), use_container_width=True)
                with col3:
                    st.caption("**Manpower no período**")
                    st.altair_chart(chart_mp_ano(df_chart), use_container_width=True)

                if df_prev is not None:
                    st.divider()
                    st.markdown(f"#### Comparativo {int(ano_overview)} vs {int(ano_overview) - 1}")
                    cy1, cy2 = st.columns(2)
                    with cy1:
                        st.caption("**Eficiência**")
                        st.altair_chart(
                            chart_yoy_line(df_ano, df_prev, ano_overview, "performance", "Eficiência"),
                            use_container_width=True,
                        )
                    with cy2:
                        st.caption("**Manpower**")
                        st.altair_chart(
                            chart_yoy_line(df_ano, df_prev, ano_overview, "manpower", "Manpower", fmt=",.2f"),
                            use_container_width=True,
                        )

                st.divider()
                st.markdown("#### Trajetória do Manpower - histórico completo")
                st.altair_chart(chart_mp_historico(df_perf), use_container_width=True)

    with tab_perf:
        st.subheader(f"Eficiência - {departamento_selecionado}")

        if not tem_dados_departamento:
            _render_metricas_vazias(
                [
                    ("Meses", "0"),
                    ("Volume médio", "0"),
                    ("MP médio", "0,00"),
                    ("Eficiência média", "0,0"),
                    ("% Meta média", "0,0%"),
                ]
            )
            st.info("Esse departamento ainda nao possui base de eficiencia carregada.")
        else:
            performance = listar_performance()

            if not performance:
                st.info("Nenhum dado de eficiencia registrado.")
            else:
                df_perf = pd.DataFrame(performance).sort_values(["ano", "mes"], ascending=[True, True]).reset_index(drop=True)
                anos = sorted(df_perf["ano"].unique(), reverse=True)
                year_tabs = st.tabs([str(int(ano)) for ano in anos])

                for tab_widget, ano in zip(year_tabs, anos):
                    df_ano = df_perf[df_perf["ano"] == ano].copy()
                    resumo = resumir_eficiencia_ano(
                        df_ano,
                        df_perf[df_perf["ano"] == ano - 1].copy(),
                        ano,
                    )

                    with tab_widget:
                        st.caption("Leitura detalhada mês a mês do ano selecionado.")
                        render_tabela_performance(df_ano)
                        st.caption(
                            f"Resumo do ano: volume médio {_br_int(resumo['volume_medio']) if resumo['volume_medio'] else '—'}"
                            f" | eficiência média {_br(resumo['eficiencia_media'], 1) if resumo['eficiencia_media'] else '—'}"
                        )

            st.divider()
            st.subheader("Lançar Eficiência Mensal")
            st.caption(
                f"Registro atual vinculado ao departamento {departamento_selecionado}. "
                "O modelo por departamento ainda esta em consolidacao."
            )

            with st.form("form_performance"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    ano_input = st.number_input("Ano", min_value=2024, max_value=2030, value=date.today().year)
                with c2:
                    mes_input = st.number_input("Mês", min_value=1, max_value=12, value=date.today().month)
                with c3:
                    volume_input = st.number_input("Volume (Score)", min_value=0, value=0, step=100)

                c4, c5 = st.columns(2)
                with c4:
                    mp_auto = obter_manpower_para_performance(ano_input, mes_input)
                    st.info(f"MP calculado: **{_br(mp_auto, 2)}**")
                    mp_manual = st.number_input(
                        "MP (ajustar se necessário)",
                        min_value=0.0,
                        value=float(mp_auto),
                        step=0.05,
                    )
                with c5:
                    meta_sugerida = 361.42 if mes_input <= 6 else 439.59
                    meta_input = st.number_input("Meta", min_value=0.0, value=meta_sugerida, step=1.0)

                if st.form_submit_button("Salvar", type="primary"):
                    if volume_input > 0 and mp_manual > 0:
                        salvar_performance(ano_input, mes_input, volume_input, mp_manual, meta_input)
                        perf_calc = round(volume_input / mp_manual, 1)
                        st.success(
                            f"Eficiência {ano_input}-{mes_input:02d}: **{_br(perf_calc, 1)}** "
                            f"(Volume {_br_int(volume_input)} / MP {_br(mp_manual, 2)})"
                        )
                        st.rerun()
                    else:
                        st.warning("Preencha Volume e MP.")

    with tab_mw:
        st.subheader(f"Manpower - {departamento_selecionado}")

        if not tem_dados_departamento:
            _render_metricas_vazias(
                [
                    ("Manpower atual", "0,00"),
                    ("Ativos", "0"),
                    ("Com peso MP", "0"),
                    ("Peso médio", "0,00"),
                ]
            )
            st.info("Esse departamento ainda nao possui base de manpower publicada na area de KPIs.")
        else:
            mp_dept = calcular_manpower_por_departamento()
            ativos = listar_colaboradores(status="Ativo", departamento_id=departamento_id)
            total_mp = mp_dept.get(departamento_id, 0)
            ativos_com_peso = [colaborador for colaborador in ativos if colaborador.get("peso_manpower") is not None]
            peso_medio = total_mp / len(ativos_com_peso) if ativos_com_peso else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Manpower atual", _br(total_mp, 2))
            with c2:
                st.metric("Ativos", len(ativos))
            with c3:
                st.metric("Com peso MP", len(ativos_com_peso))
            with c4:
                st.metric("Peso médio", _br(peso_medio, 2))

            st.divider()

            if ativos:
                df = pd.DataFrame(ativos)[
                    [
                        "nome",
                        "departamento_nome",
                        "cargo_nome",
                        "cargo_nivel",
                        "peso_manpower",
                        "unidade",
                        "gestor_direto",
                    ]
                ]
                df.columns = ["Nome", "Departamento", "Cargo", "Nível", "Peso MP", "Unidade", "Gestor"]
                df = df.sort_values(["Nível", "Nome"])

                df_conta = df[df["Peso MP"].notna()].copy()
                df_nao_conta = df[df["Peso MP"].isna()].copy()

                for dataset in [df_conta, df_nao_conta]:
                    dataset["Peso MP"] = dataset["Peso MP"].apply(lambda val: _br(val, 2) if pd.notna(val) else "")

                st.markdown(f"**Colaboradores com peso MP** ({len(df_conta)})")
                if not df_conta.empty:
                    st.dataframe(df_conta, use_container_width=True, hide_index=True)
                    st.caption(f"Manpower total: **{_br(total_mp, 2)}**")

                if not df_nao_conta.empty:
                    with st.expander(f"Colaboradores sem peso MP ({len(df_nao_conta)})"):
                        st.dataframe(df_nao_conta, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum colaborador ativo encontrado para o departamento selecionado.")

    with tab_score:
        st.subheader(f"Painel de Volume (Score) - {departamento_selecionado}")
        st.warning(
            "Painel em construção. Esta é uma réplica inicial do resumo que hoje sai do BI, "
            "já aplicada ao padrão visual do portal."
        )

        if not tem_dados_departamento:
            _render_metricas_vazias(
                [
                    ("Analistas", "0"),
                    ("Volume total (Score)", "0,00"),
                    ("Média mensal", "0,00"),
                    ("Registros", "0"),
                ]
            )
            st.info("Esse departamento ainda nao possui carga de dados para o painel de volume score.")
        else:
            df_score = carregar_score_base()

            if df_score.empty:
                st.info("A base de score nao foi localizada em `arquivos base`.")
            else:
                df_score = df_score.sort_values("Score Performance", ascending=False).reset_index(drop=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Analistas", len(df_score))
                with c2:
                    st.metric("Volume total (Score)", _br(df_score["Score Performance"].sum(), 2))
                with c3:
                    st.metric("Média mensal", _br(df_score["Média mensal Score"].mean(), 2))
                with c4:
                    st.metric("Registros", _br_int(df_score["Registros"].sum()))

                st.caption(
                    "Base provisória replicada de `arquivos base/Análise de performance (2).xlsx`, "
                    "mantendo neste momento somente o recorte de Importação."
                )
                st.divider()

                col_chart, col_highlight = st.columns([1.5, 1])
                with col_chart:
                    st.caption("**Ranking atual por Volume (Score)**")
                    st.altair_chart(chart_score_ranking(df_score), use_container_width=True)
                with col_highlight:
                    destaque = df_score.iloc[0]
                    st.metric("Maior volume (score)", _br(destaque["Score Performance"], 2), destaque["Analista"])
                    st.metric("Maior média mensal", _br(df_score["Média mensal Score"].max(), 2))
                    st.metric("Abertos", _br_int(df_score["Abertos"].sum()))
                    st.metric("Liberados faturados", _br_int(df_score["Liberados Fatur."].sum()))

                st.divider()

                df_show = df_score.rename(
                    columns={
                        "Score Performance": "Volume (Score)",
                        "Média mensal Score": "Média mensal",
                        "Liberados Fatur.": "Liberados faturados",
                    }
                )
                styled = df_show.style.format(
                    {
                        "Volume (Score)": lambda val: _br(val, 2),
                        "Média mensal": lambda val: _br(val, 2),
                        "Abertos": lambda val: _br_int(val),
                        "Embarcados": lambda val: _br_int(val),
                        "Chegadas Confirmadas": lambda val: _br_int(val),
                        "Registros": lambda val: _br_int(val),
                        "Liberados faturados": lambda val: _br_int(val),
                    }
                )
                height = min(38 + len(df_show) * 35 + 6, 900)
                st.dataframe(styled, use_container_width=True, hide_index=True, height=height)
