"""Homepage — Command Center do Portal do Gestor."""

import re as _re
from datetime import date

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado, obter_usuario_atual, usuario_admin
from utils.excel_io import ler_bytes_workbook
from utils.departamentos import listar_departamentos, listar_cargos
from utils.pessoas import listar_colaboradores, listar_historico
from utils.manpower import calcular_manpower_por_departamento, listar_performance
from utils.processos360 import (
    STATUS_ORDEM,
    calcular_alertas,
    dados_existem,
    obter_processos,
)
from utils.ui import aplicar_estilos_globais, saudacao_periodo

# ── Dados ──────────────────────────────────────────────────────────────────────
aplicar_estilos_globais()
garantir_autenticado()
usuario_logado = obter_usuario_atual() or {}

ativos = listar_colaboradores(status="Ativo")
inativos = listar_colaboradores(status="Inativo")
departamentos = listar_departamentos()
cargos = listar_cargos()
mp_dept = calcular_manpower_por_departamento()
performance = listar_performance()
historico = listar_historico()

mp_total = sum(mp_dept.values())

ultima_perf = None
if performance:
    ultima_perf = sorted(
        performance, key=lambda p: (p.get("ano", 0), p.get("mes", 0)), reverse=True
    )[0]

# Processos 360 (departamento de Importação)
tem_processos = dados_existem()
df_proc = obter_processos() if tem_processos else pd.DataFrame()
if not df_proc.empty:
    alertas_proc = calcular_alertas(df_proc)
    total_alertas = sum(len(v) for v in alertas_proc.values())
    clientes_unicos = df_proc["Cliente"].nunique() if "Cliente" in df_proc.columns else 0
    # Valores financeiros
    valor_aduaneiro_total = df_proc["Valor Aduaneiro"].sum() if "Valor Aduaneiro" in df_proc.columns else 0
    total_containers = int(df_proc["Qtd. Container"].sum()) if "Qtd. Container" in df_proc.columns else 0
else:
    alertas_proc = {}
    total_alertas = 0
    clientes_unicos = 0
    valor_aduaneiro_total = 0
    total_containers = 0

# Dados do Organograma — hierarquia
cargo_map = {c["id"]: c for c in cargos}
niveis_def = {
    "Gerência": (0, 1),
    "Coordenação": (1.5, 2),
    "Supervisão": (2.5, 2.5),
    "Especialistas": (3, 3),
    "Analistas": (4, 6),
    "Assist./Estag.": (7, 10),
}
nivel_counts = {}
for label, (nmin, nmax) in niveis_def.items():
    count = sum(
        1 for c in ativos
        if cargo_map.get(c.get("cargo_id")) and nmin <= cargo_map[c["cargo_id"]].get("nivel", 99) <= nmax
    )
    nivel_counts[label] = count

# Histórico — entradas/saídas recentes
entradas_total = sum(1 for h in historico if h.get("tipo") == "Entrada")
saidas_total = sum(1 for h in historico if h.get("tipo") == "Saída")

# Cidades / unidades
unidades = {}
for c in ativos:
    cidade = c.get("cidade", "—") or "—"
    unidades[cidade] = unidades.get(cidade, 0) + 1

meses_pt = [
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]


def _br(val, dec=2):
    if val is None:
        return "—"
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _br_moeda_curta(val):
    """Formata moeda abreviada: 1.2M, 500K, etc."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if abs(val) >= 1_000_000:
        return f"R$ {val / 1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(val) >= 1_000:
        return f"R$ {val / 1_000:,.0f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {_br(val, 0)}"


# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.block-container { padding-top: 1rem !important; }

/* ── Banner ── */
.hm-banner {
    background: rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 24px;
    padding: 26px 34px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #223645;
    box-shadow: 0 8px 32px rgba(35, 64, 85, 0.06);
}
.hm-banner-title { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin: 0; color: #234055; }
.hm-banner-sub   { font-size: 13px; color: #6f7a84; margin-top: 5px; }
.hm-banner-date  {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(227, 216, 197, 0.5);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
    color: #234055;
    white-space: nowrap;
}

/* ── Hero KPIs ── */
.hm-kpi-strip {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}
.hm-kpi {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 16px 16px 13px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 0 4px 24px rgba(35, 64, 85, 0.05);
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
    cursor: default;
}
.hm-kpi:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 36px rgba(35, 64, 85, 0.1);
    border-color: rgba(199, 149, 54, 0.4);
    background: rgba(255, 255, 255, 0.65);
}
a.hm-kpi-link {
    text-decoration: none;
    color: inherit;
    display: block;
}
.hm-kpi::after {
    content: attr(data-icon);
    position: absolute;
    right: 12px; top: 10px;
    font-size: 22px; opacity: 0.10;
}
.hm-kpi-label  { font-size: 10px; color: #6f7a84; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
.hm-kpi-value  { font-size: 26px; font-weight: 800; color: #234055; line-height: 1.1; margin: 5px 0 3px; }
.hm-kpi-sub    { font-size: 11px; color: #86909a; }
.hm-kpi.gold   { border-left: 3px solid rgba(199, 149, 54, 0.5); }
.hm-kpi.teal   { border-left: 3px solid rgba(94, 134, 104, 0.5); }
.hm-kpi.blue   { border-left: 3px solid rgba(74, 138, 181, 0.5); }
.hm-kpi.red    { border-left: 3px solid rgba(181, 66, 58, 0.4); }
.hm-kpi-value.green { color: #5e8668; }
.hm-kpi-value.amber { color: #b78328; }

/* ── Pipeline ── */
.hm-pipeline {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 20px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 24px rgba(35, 64, 85, 0.05);
    transition: all 0.2s ease;
}
.hm-pipeline:hover {
    box-shadow: 0 12px 36px rgba(35, 64, 85, 0.1);
    border-color: rgba(199, 149, 54, 0.4);
    background: rgba(255, 255, 255, 0.6);
}
.hm-pipeline-seg {
    transition: opacity 0.2s ease;
}
.hm-pipeline-bar:hover .hm-pipeline-seg {
    opacity: 0.8;
}
.hm-pipeline-bar:hover .hm-pipeline-seg:hover {
    opacity: 1;
    filter: brightness(1.1);
}
.hm-pipeline-header {
    font-size: 11px; font-weight: 800; color: #234055;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 12px;
    display: flex; justify-content: space-between; align-items: center;
}
.hm-pipeline-header a {
    font-size: 11px; color: #c79536; font-weight: 700;
    text-decoration: none; letter-spacing: 0.04em;
    text-transform: none;
}
.hm-pipeline-header a:hover { text-decoration: underline; }
.hm-pipeline-bar {
    display: flex;
    border-radius: 10px;
    overflow: hidden;
    height: 34px;
    margin-bottom: 8px;
}
.hm-pipeline-legend {
    display: flex; flex-wrap: wrap; gap: 8px 16px;
}
.hm-pipeline-leg-item {
    display: flex; align-items: center; gap: 5px;
    font-size: 11px; color: #6f7a84; font-weight: 600;
}
.hm-pipeline-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}

/* ── Section row (2 col) ── */
.hm-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }

/* ── Section cards ── */
.hm-sec {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-radius: 22px;
    padding: 20px 20px 16px;
    box-shadow: 0 4px 24px rgba(35, 64, 85, 0.05);
    display: flex;
    flex-direction: column;
    transition: all 0.25s ease;
}
.hm-sec:hover {
    box-shadow: 0 12px 40px rgba(35, 64, 85, 0.1);
    transform: translateY(-3px);
    border-color: rgba(199, 149, 54, 0.4);
    background: rgba(255, 255, 255, 0.65);
}
.hm-sec-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.hm-sec-icon {
    width: 38px; height: 38px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
}
.hm-sec-icon.org   { background: rgba(74, 138, 181, 0.12); }
.hm-sec-icon.kpi   { background: rgba(199, 149, 54, 0.12); }
.hm-sec-icon.proc  { background: rgba(94, 134, 104, 0.12); }
.hm-sec-icon.pess  { background: rgba(120, 90, 160, 0.12); }
.hm-sec-title  { font-size: 15px; font-weight: 800; color: #234055; }
.hm-sec-desc   { font-size: 11px; color: #7d8790; margin-top: 1px; }
.hm-sec-body   { flex: 1; }

.hm-sec-metrics {
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
    margin-bottom: 12px;
}
.hm-sec-metrics.tri { grid-template-columns: 1fr 1fr 1fr; }
.hm-sec-metric {
    background: rgba(255,255,255,0.45);
    border: 1px solid rgba(227, 216, 197, 0.4);
    border-radius: 12px;
    padding: 9px 11px;
}
.hm-sec-metric-label { font-size: 9px; color: #7d8790; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em; }
.hm-sec-metric-val   { font-size: 18px; font-weight: 800; color: #234055; line-height: 1.2; margin-top: 2px; }
.hm-sec-metric-val.green { color: #5e8668; }
.hm-sec-metric-val.amber { color: #b78328; }
.hm-sec-metric-val.sm    { font-size: 15px; }

.hm-sec-link {
    display: block;
    text-align: center;
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(199, 149, 54, 0.25);
    border-radius: 12px;
    padding: 8px 14px;
    text-decoration: none;
    color: #234055;
    font-weight: 700;
    font-size: 12px;
    margin-top: auto;
    transition: all 0.2s ease;
}
.hm-sec-link:hover {
    background: rgba(199, 149, 54, 0.12);
    border-color: rgba(199, 149, 54, 0.5);
    color: #234055;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(199, 149, 54, 0.12);
}

/* ── Alert badges ── */
.hm-alert-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.hm-alert-badge {
    display: inline-flex; align-items: center; gap: 4px;
    border-radius: 999px;
    padding: 3px 9px;
    font-size: 10px; font-weight: 700;
}
.hm-alert-badge.critical { background: rgba(181, 66, 58, 0.1); color: #b5423a; border: 1px solid rgba(181, 66, 58, 0.2); }
.hm-alert-badge.warning  { background: rgba(183, 131, 40, 0.1); color: #b78328; border: 1px solid rgba(183, 131, 40, 0.2); }
.hm-alert-badge.info     { background: rgba(54, 88, 111, 0.08); color: #36586f; border: 1px solid rgba(54, 88, 111, 0.15); }
.hm-alert-badge { transition: all 0.15s ease; cursor: pointer; }
.hm-alert-badge:hover { transform: scale(1.08); background: rgba(255,255,255,0.5); }
a.hm-alert-link { text-decoration: none; }
.hm-alert-count {
    background: rgba(0,0,0,0.1);
    border-radius: 999px;
    padding: 1px 5px;
    font-size: 9px;
    font-weight: 800;
}

/* ── Hierarchy bar (horizontal stacked) ── */
.hm-hier-bar {
    display: flex;
    border-radius: 8px;
    overflow: hidden;
    height: 24px;
    margin-bottom: 6px;
}
.hm-hier-seg {
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 10px; font-weight: 800;
    min-width: 0; overflow: hidden;
}
.hm-hier-legend {
    display: flex; flex-wrap: wrap; gap: 4px 10px;
    margin-bottom: 10px;
}
.hm-hier-leg-item {
    display: flex; align-items: center; gap: 4px;
    font-size: 10px; color: #6f7a84; font-weight: 600;
}
.hm-hier-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

/* ── Dept cards grid ── */
.hm-dept-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px; margin-bottom: 20px;
}
.hm-dept-card {
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    border-top: 3px solid rgba(199, 149, 54, 0.6);
    border-radius: 16px;
    padding: 14px 16px 12px;
    box-shadow: 0 4px 20px rgba(35, 64, 85, 0.04);
    transition: all 0.2s ease;
}
.hm-dept-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(35, 64, 85, 0.1);
    border-color: rgba(199, 149, 54, 0.4);
    background: rgba(255, 255, 255, 0.65);
}
.hm-dept-card-name {
    font-size: 11px; font-weight: 800; color: #234055;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.hm-dept-card-nums {
    display: flex; gap: 12px; margin-bottom: 8px;
}
.hm-dept-card-num {
    text-align: center;
}
.hm-dept-card-num-val { font-size: 22px; font-weight: 800; color: #234055; line-height: 1; }
.hm-dept-card-num-label { font-size: 9px; color: #7d8790; text-transform: uppercase; font-weight: 700; }
.hm-dept-card-bar-bg {
    height: 5px; background: rgba(35, 64, 85, 0.08); border-radius: 3px;
    overflow: hidden; margin-bottom: 8px;
}
.hm-dept-card-bar-fill {
    height: 100%; border-radius: 3px;
    background: rgba(74, 138, 181, 0.5);
}
.hm-dept-card-people {
    font-size: 10px; color: #6f7a84; line-height: 1.5;
}
.hm-dept-card-people strong { color: #234055; font-weight: 700; }

/* ── Perf highlight ── */
.hm-perf-highlight {
    background: rgba(35, 64, 85, 0.88);
    backdrop-filter: blur(8px);
    border-radius: 14px;
    padding: 13px 15px;
    color: white;
    margin-bottom: 10px;
}
.hm-perf-highlight.below {
    background: rgba(155, 122, 52, 0.85);
}
.hm-perf-label { font-size: 9px; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
.hm-perf-val   { font-size: 30px; font-weight: 800; line-height: 1.1; margin: 3px 0; }
.hm-perf-meta  { font-size: 11px; opacity: 0.8; }

/* ── Movimentações mini ── */
.hm-mov-item {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 0;
    border-bottom: 1px solid #f1ebe1;
    font-size: 11px;
}
.hm-mov-item:last-child { border-bottom: none; }
.hm-mov-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.hm-mov-dot.entrada { background: #2a7d4f; }
.hm-mov-dot.saida   { background: #c0392b; }
.hm-mov-name  { font-weight: 700; color: #223645; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hm-mov-info  { color: #7d8790; font-size: 10px; }
.hm-mov-date  { color: #9ca5ad; font-size: 10px; flex-shrink: 0; }

/* ── Top clientes ── */
.hm-top-item {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 11px; padding: 4px 0; border-bottom: 1px solid #f1ebe1;
}
.hm-top-item:last-child { border-bottom: none; }
.hm-top-name { color: #234055; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.hm-top-val  { color: #6f7a84; font-weight: 700; flex-shrink: 0; margin-left: 8px; }

/* ── Section title ── */
.hm-section-label {
    font-size: 10px; font-weight: 800; color: #6f7a84;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin-bottom: 6px;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .hm-banner { flex-direction: column; align-items: flex-start; gap: 10px; padding: 18px; border-radius: 18px; }
    .hm-banner-title { font-size: 22px; }
    .hm-kpi-strip { grid-template-columns: repeat(2, 1fr); }
    .hm-kpi-value { font-size: 22px; }
    .hm-pipeline-bar { height: 26px; }
    .hm-pipeline-seg { font-size: 9px; }
    .hm-row2 { grid-template-columns: 1fr; }
    .hm-dept-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
    .hm-kpi-strip { grid-template-columns: repeat(2, 1fr); }
    .hm-kpi-value { font-size: 20px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Banner ─────────────────────────────────────────────────────────────────────
hoje = date.today()
data_fmt = hoje.strftime(f"%d {meses_pt[hoje.month]} %Y")

st.markdown(
    f"""
    <div class="hm-banner">
        <div>
            <div class="hm-banner-title">{saudacao_periodo()}, {usuario_logado.get("nome", "Usuário")}</div>
            <div class="hm-banner-sub">Portal do Gestor &middot; operação, pessoas e performance centralizadas em um único painel</div>
        </div>
        <div class="hm-banner-date">{data_fmt}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Hero KPIs (5 cards) ───────────────────────────────────────────────────────
total_proc = len(df_proc)

# Performance % meta
pct_val = None
pct_class = ""
if ultima_perf and ultima_perf.get("pct_meta"):
    pct_val = ultima_perf["pct_meta"] * 100
    pct_class = "green" if pct_val >= 100 else "amber"
pct_display = _br(pct_val, 1) + "%" if pct_val else "—"
perf_ref = ""
if ultima_perf:
    perf_ref = f"{meses_pt[int(ultima_perf['mes'])]}/{str(int(ultima_perf['ano']))[2:]}"

st.markdown(
    f"""
    <div class="hm-kpi-strip">
        <a class="hm-kpi-link" href="/Organograma">
            <div class="hm-kpi" data-icon="👥">
                <div class="hm-kpi-label">Colaboradores Ativos</div>
                <div class="hm-kpi-value">{len(ativos)}</div>
                <div class="hm-kpi-sub">em {len(departamentos)} departamentos</div>
            </div>
        </a>
        <a class="hm-kpi-link" href="/KPIs">
            <div class="hm-kpi gold" data-icon="⚖️">
                <div class="hm-kpi-label">Manpower Total</div>
                <div class="hm-kpi-value">{_br(mp_total, 1)}</div>
                <div class="hm-kpi-sub">soma dos pesos ativos</div>
            </div>
        </a>
        <a class="hm-kpi-link" href="/Processos_360">
            <div class="hm-kpi blue" data-icon="🚢">
                <div class="hm-kpi-label">Processos · Importação</div>
                <div class="hm-kpi-value">{total_proc:,}</div>
                <div class="hm-kpi-sub">{clientes_unicos} clientes</div>
            </div>
        </a>
        <a class="hm-kpi-link" href="/Processos_360">
            <div class="hm-kpi red" data-icon="⚠️">
                <div class="hm-kpi-label">Alertas Ativos</div>
                <div class="hm-kpi-value">{total_alertas}</div>
                <div class="hm-kpi-sub">requerem atenção</div>
            </div>
        </a>
        <a class="hm-kpi-link" href="/KPIs">
            <div class="hm-kpi teal" data-icon="📊">
                <div class="hm-kpi-label">% da Meta {perf_ref}</div>
                <div class="hm-kpi-value {pct_class}">{pct_display}</div>
                <div class="hm-kpi-sub">eficiência operacional</div>
            </div>
        </a>
    </div>
    """.replace(",}", "}"),
    unsafe_allow_html=True,
)

# ── Pipeline de Processos (Importação) ─────────────────────────────────────────
STATUS_CORES = {
    "Pré-embarque": "#7ea6c7",
    "Embarque": "#4a8ab5",
    "Chegada": "#c79536",
    "Registrado/Ag.Desembaraço": "#e6a832",
    "Carregamento": "#5e8668",
    "Encerramento": "#234055",
}

if not df_proc.empty:
    seg_html = ""
    legend_html = ""
    for s in STATUS_ORDEM:
        n = len(df_proc[df_proc["Status"] == s])
        pct = n / total_proc * 100 if total_proc > 0 else 0
        cor = STATUS_CORES.get(s, "#ccc")
        label = str(n) if pct > 5 else ""
        seg_html += f'<div class="hm-pipeline-seg" style="flex:{pct};background:{cor};">{label}</div>'
        legend_html += f'<div class="hm-pipeline-leg-item"><span class="hm-pipeline-dot" style="background:{cor};"></span>{s} ({n})</div>'

    extras_html = ""
    if valor_aduaneiro_total and valor_aduaneiro_total > 0:
        extras_html += f' &middot; Valor aduaneiro: <strong>{_br_moeda_curta(valor_aduaneiro_total)}</strong>'
    if total_containers:
        extras_html += f' &middot; <strong>{total_containers}</strong> containers'

    st.markdown(
        f"""
        <div class="hm-pipeline">
            <div class="hm-pipeline-header">
                <span>Pipeline de Processos · Importação · {total_proc} processos{extras_html}</span>
                <a href="/Processos_360">Ver detalhes →</a>
            </div>
            <div class="hm-pipeline-bar">{seg_html}</div>
            <div class="hm-pipeline-legend">{legend_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 1: Organograma + KPIs (2 colunas)
# ══════════════════════════════════════════════════════════════════════════════

# --- Card: Organograma ---
NIVEL_CORES = {
    "Gerência": "#234055",
    "Coordenação": "#4a8ab5",
    "Supervisão": "#c79536",
    "Especialistas": "#8b5e3c",
    "Analistas": "#5e8668",
    "Assist./Estag.": "#7ea6c7",
}

total_nivel = sum(nivel_counts.values()) or 1
hier_bar_html = ""
hier_legend_html = ""
for label, count in nivel_counts.items():
    if count == 0:
        continue
    pct = count / total_nivel * 100
    cor = NIVEL_CORES.get(label, "#999")
    lbl = str(count) if pct > 7 else ""
    hier_bar_html += f'<div class="hm-hier-seg" style="flex:{pct};background:{cor};">{lbl}</div>'
    hier_legend_html += f'<div class="hm-hier-leg-item"><span class="hm-hier-dot" style="background:{cor};"></span>{label} ({count})</div>'

# Unidades
unidades_html = ""
for cidade, count in sorted(unidades.items(), key=lambda x: -x[1]):
    unidades_html += f'<span style="background:rgba(35,64,85,0.07);color:#234055;border-radius:8px;padding:3px 8px;font-size:10px;font-weight:700;white-space:nowrap;">{cidade}: {count}</span> '

org_card = f"""
<div class="hm-sec">
    <div class="hm-sec-header">
        <div class="hm-sec-icon org">🗂️</div>
        <div>
            <div class="hm-sec-title">Organograma</div>
            <div class="hm-sec-desc">Estrutura organizacional e hierarquia</div>
        </div>
    </div>
    <div class="hm-sec-body">
        <div class="hm-sec-metrics tri">
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Colaboradores</div>
                <div class="hm-sec-metric-val">{len(ativos)}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Manpower</div>
                <div class="hm-sec-metric-val">{_br(mp_total, 1)}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Cargos</div>
                <div class="hm-sec-metric-val">{len(cargos)}</div>
            </div>
        </div>
        <div class="hm-section-label">Hierarquia</div>
        <div class="hm-hier-bar">{hier_bar_html}</div>
        <div class="hm-hier-legend">{hier_legend_html}</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;">
            <span style="font-size:10px;color:#7d8790;font-weight:700;margin-right:4px;">Unidades:</span>
            {unidades_html}
        </div>
    </div>
    <a class="hm-sec-link" href="/Organograma">Explorar Organograma →</a>
</div>"""

# --- Departamentos: dados para seção dedicada ---
dept_cards_data = []
for depto in departamentos:
    dept_ativos = [c for c in ativos if c.get("departamento_id") == depto["id"]]
    mp = mp_dept.get(depto["id"], 0)
    # Nomes dos colaboradores com cargo
    pessoas = []
    for c in sorted(dept_ativos, key=lambda x: cargo_map.get(x.get("cargo_id"), {}).get("nivel", 99)):
        cargo = cargo_map.get(c.get("cargo_id"), {})
        pessoas.append((c.get("nome", "—"), cargo.get("nome", "—")))
    dept_cards_data.append((depto["nome"], len(dept_ativos), mp, pessoas))

# --- Card: KPIs & Eficiência ---
if ultima_perf:
    mes_label = meses_pt[int(ultima_perf["mes"])]
    ano_label = str(int(ultima_perf["ano"]))
    perf_num = _br(ultima_perf.get("performance", 0), 1)
    meta_num = _br(ultima_perf.get("meta", 0), 1)
    vol_num = _br(ultima_perf.get("volume_score", 0), 0)
    mp_perf = _br(ultima_perf.get("manpower", 0), 1)
    pct_str = _br(pct_val, 1) + "%" if pct_val else "—"
    pct_icon = "✅" if pct_val and pct_val >= 100 else "⚠️"
    highlight_class = "hm-perf-highlight" if pct_val and pct_val >= 100 else "hm-perf-highlight below"

    # Mini histórico de performance (últimos 6 meses)
    perf_sorted = sorted(performance, key=lambda p: (p.get("ano", 0), p.get("mes", 0)))
    ultimos6 = perf_sorted[-6:]
    perf_hist_html = '<div style="display:flex;gap:4px;align-items:flex-end;height:50px;margin-bottom:10px;">'
    max_perf = max((p.get("performance", 0) or 0 for p in ultimos6), default=1) or 1
    for p in ultimos6:
        val = p.get("performance", 0) or 0
        h = max(val / max_perf * 44, 4)
        m = meses_pt[int(p.get("mes", 0))]
        pct_m = (p.get("pct_meta") or 0) * 100
        cor = "#5e8668" if pct_m >= 100 else "#c79536"
        perf_hist_html += f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;"><div style="width:100%;height:{h:.0f}px;background:{cor};border-radius:4px;" title="{m}: {_br(val,1)}"></div><span style="font-size:8px;color:#7d8790;font-weight:700;">{m}</span></div>'
    perf_hist_html += '</div>'

    kpi_card = f"""
    <div class="hm-sec">
        <div class="hm-sec-header">
            <div class="hm-sec-icon kpi">📊</div>
            <div>
                <div class="hm-sec-title">KPIs & Eficiência</div>
                <div class="hm-sec-desc">Performance operacional · Importação</div>
            </div>
        </div>
        <div class="hm-sec-body">
            <div class="{highlight_class}">
                <div class="hm-perf-label">Eficiência · {mes_label}/{ano_label}</div>
                <div class="hm-perf-val">{perf_num}</div>
                <div class="hm-perf-meta">{pct_icon} {pct_str} da meta ({meta_num})</div>
            </div>
            <div class="hm-sec-metrics">
                <div class="hm-sec-metric">
                    <div class="hm-sec-metric-label">Volume (Score)</div>
                    <div class="hm-sec-metric-val sm">{vol_num}</div>
                </div>
                <div class="hm-sec-metric">
                    <div class="hm-sec-metric-label">Manpower Mês</div>
                    <div class="hm-sec-metric-val sm">{mp_perf}</div>
                </div>
            </div>
            <div class="hm-section-label">Últimos {len(ultimos6)} meses</div>
            {perf_hist_html}
        </div>
        <a class="hm-sec-link" href="/KPIs">Explorar KPIs →</a>
    </div>"""
else:
    kpi_card = f"""
    <div class="hm-sec">
        <div class="hm-sec-header">
            <div class="hm-sec-icon kpi">📊</div>
            <div>
                <div class="hm-sec-title">KPIs & Eficiência</div>
                <div class="hm-sec-desc">Performance operacional</div>
            </div>
        </div>
        <div class="hm-sec-body">
            <div class="hm-sec-metrics">
                <div class="hm-sec-metric">
                    <div class="hm-sec-metric-label">Manpower Total</div>
                    <div class="hm-sec-metric-val">{_br(mp_total, 1)}</div>
                </div>
                <div class="hm-sec-metric">
                    <div class="hm-sec-metric-label">Colaboradores</div>
                    <div class="hm-sec-metric-val">{len(ativos)}</div>
                </div>
            </div>
            <p style="font-size:12px;color:#7d8790;text-align:center;margin:14px 0;">Dados de performance ainda não registrados.</p>
        </div>
        <a class="hm-sec-link" href="/KPIs">Explorar KPIs →</a>
    </div>"""

col_org, col_kpi = st.columns(2, gap="medium")
with col_org:
    st.markdown(org_card, unsafe_allow_html=True)
with col_kpi:
    st.markdown(kpi_card, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DEPARTAMENTOS — seção full-width com cards por departamento
# ══════════════════════════════════════════════════════════════════════════════
max_dept_count = max((d[1] for d in dept_cards_data), default=1) or 1

dept_cards_html = ""
for nome, n, mp, pessoas in sorted(dept_cards_data, key=lambda x: -x[1]):
    mp_str = _br(mp, 1) if mp > 0 else "—"
    pct_bar = n / max_dept_count * 100

    # Lista de nomes (agrupados por cargo)
    if pessoas:
        nomes_html = ", ".join(
            f'<strong>{p[0].split()[0]}</strong> <span style="opacity:0.7;">({p[1]})</span>'
            for p in pessoas[:8]  # max 8 para não explodir
        )
        if len(pessoas) > 8:
            nomes_html += f' <span style="opacity:0.6;">+{len(pessoas) - 8} mais</span>'
    else:
        nomes_html = '<span style="opacity:0.5;">—</span>'

    dept_cards_html += f"""
    <a href="/Organograma" style="text-decoration:none;color:inherit;display:block;">
    <div class="hm-dept-card">
        <div class="hm-dept-card-name">{nome}</div>
        <div class="hm-dept-card-nums">
            <div class="hm-dept-card-num">
                <div class="hm-dept-card-num-val">{n}</div>
                <div class="hm-dept-card-num-label">Ativos</div>
            </div>
            <div class="hm-dept-card-num">
                <div class="hm-dept-card-num-val" style="font-size:18px;">{mp_str}</div>
                <div class="hm-dept-card-num-label">Manpower</div>
            </div>
        </div>
        <div class="hm-dept-card-bar-bg">
            <div class="hm-dept-card-bar-fill" style="width:{pct_bar:.0f}%;"></div>
        </div>
        <div class="hm-dept-card-people">{nomes_html}</div>
    </div>
    </a>"""

st.markdown(
    f"""
    <div style="font-size:11px;font-weight:800;color:#234055;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
        <span>Departamentos · {len(departamentos)} áreas · {len(ativos)} colaboradores</span>
        <a href="/Organograma" style="font-size:11px;color:#c79536;font-weight:700;text-decoration:none;text-transform:none;">Ver organograma →</a>
    </div>
    <div class="hm-dept-grid">{dept_cards_html}</div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# LINHA 2: Processos 360 + Controle de Pessoas (2 colunas)
# ══════════════════════════════════════════════════════════════════════════════

# --- Card: Processos 360 ---
alert_items = []
if alertas_proc:
    alert_defs = [
        ("saldo_negativo", "Saldo Negativo", "critical"),
        ("canal_vermelho", "Canal Vermelho", "critical"),
        ("container_vencido", "Container Vencido", "critical"),
        ("li_indeferida", "LI/LPCO Indeferida", "critical"),
        ("follow_desatualizado", "Follow > 10d", "warning"),
        ("container_vencendo", "Container Vencendo", "warning"),
        ("perdimento_proximo", "Perdimento", "warning"),
        ("canal_amarelo", "Canal Amarelo", "info"),
        ("valor_alto", "Valor Alto", "info"),
    ]
    for key, label, severity in alert_defs:
        n = len(alertas_proc.get(key, pd.DataFrame()))
        if n > 0:
            alert_items.append((label, n, severity))

alerts_html = ""
if alert_items:
    alerts_html = '<div class="hm-section-label">Alertas</div><div class="hm-alert-row">'
    for label, n, severity in alert_items:
        alerts_html += f'<a class="hm-alert-link" href="/Processos_360"><span class="hm-alert-badge {severity}">{label} <span class="hm-alert-count">{n}</span></span></a>'
    alerts_html += "</div>"

# Top clientes
top_clientes_html = ""
if not df_proc.empty and "Cliente" in df_proc.columns:
    def _consolidar(nome):
        if not isinstance(nome, str):
            return nome
        nome = _re.sub(r'\s*\([^)]*\)\s*$', '', nome)
        nome = _re.sub(r'\s*-\s*\d[\d\-/\.]*\s*$', '', nome)
        nome = _re.sub(r'\s+\d[\d\-]+\s*$', '', nome)
        return nome.strip()

    cliente_col = df_proc["Cliente"].apply(_consolidar)
    top5 = cliente_col.value_counts().head(5)
    if not top5.empty:
        top_clientes_html = '<div class="hm-section-label">Top Clientes</div>'
        for cliente, count in top5.items():
            top_clientes_html += f'<div class="hm-top-item"><span class="hm-top-name">{cliente}</span><span class="hm-top-val">{count} proc.</span></div>'

# Modalidades resumo
modal_html = ""
if not df_proc.empty and "Modalidade" in df_proc.columns:
    top_mod = df_proc["Modalidade"].value_counts().head(3)
    if not top_mod.empty:
        modal_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">'
        for mod, cnt in top_mod.items():
            modal_html += f'<span style="background:rgba(35,64,85,0.07);color:#234055;border-radius:8px;padding:3px 8px;font-size:10px;font-weight:700;">{mod}: {cnt}</span>'
        modal_html += '</div>'

proc_card = f"""
<div class="hm-sec">
    <div class="hm-sec-header">
        <div class="hm-sec-icon proc">🚢</div>
        <div>
            <div class="hm-sec-title">Processos 360</div>
            <div class="hm-sec-desc">Importação · visão consolidada</div>
        </div>
    </div>
    <div class="hm-sec-body">
        <div class="hm-sec-metrics">
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Processos</div>
                <div class="hm-sec-metric-val">{total_proc}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Clientes</div>
                <div class="hm-sec-metric-val">{clientes_unicos}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Valor Aduaneiro</div>
                <div class="hm-sec-metric-val sm">{_br_moeda_curta(valor_aduaneiro_total)}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Containers</div>
                <div class="hm-sec-metric-val">{total_containers}</div>
            </div>
        </div>
        {alerts_html}
        {modal_html}
        {top_clientes_html}
    </div>
    <a class="hm-sec-link" href="/Processos_360">Explorar Processos →</a>
</div>"""

# --- Card: Controle de Pessoas ---
# Últimas 5 movimentações
mov_html = ""
for h in historico[:5]:
    tipo = h.get("tipo", "")
    dot_class = "entrada" if tipo == "Entrada" else "saida"
    nome = str(h.get("nome", "—")).replace("<", "&lt;").replace(">", "&gt;")
    cargo_nome = str(h.get("cargo", "")).replace("<", "&lt;").replace(">", "&gt;")
    try:
        dt = pd.to_datetime(h["data"])
        data_str = f"{meses_pt[dt.month]}/{str(dt.year)[2:]}"
    except Exception:
        data_str = "—"
    mov_html += (
        f'<div class="hm-mov-item">'
        f'<span class="hm-mov-dot {dot_class}"></span>'
        f'<span class="hm-mov-name">{nome}</span>'
        f'<span class="hm-mov-info">{cargo_nome}</span>'
        f'<span class="hm-mov-date">{data_str}</span>'
        f'</div>'
    )

mov_content = mov_html if mov_html else '<p style="font-size:11px;color:#7d8790;">Nenhuma movimentação.</p>'

n_ativos = len(ativos)
n_inativos = len(inativos)

pess_card = f"""
<div class="hm-sec">
    <div class="hm-sec-header">
        <div class="hm-sec-icon pess">👥</div>
        <div>
            <div class="hm-sec-title">Controle de Pessoas</div>
            <div class="hm-sec-desc">Gestão de contratações e desligamentos</div>
        </div>
    </div>
    <div class="hm-sec-body">
        <div class="hm-sec-metrics">
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Ativos</div>
                <div class="hm-sec-metric-val green">{n_ativos}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Inativos</div>
                <div class="hm-sec-metric-val">{n_inativos}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Entradas</div>
                <div class="hm-sec-metric-val sm">{entradas_total}</div>
            </div>
            <div class="hm-sec-metric">
                <div class="hm-sec-metric-label">Saídas</div>
                <div class="hm-sec-metric-val sm">{saidas_total}</div>
            </div>
        </div>
        <div class="hm-section-label">Últimas Movimentações</div>
        {mov_content}
    </div>
    <a class="hm-sec-link" href="/Controle_de_Pessoas">Explorar Pessoas →</a>
</div>"""

col_proc, col_pess = st.columns(2, gap="medium")
with col_proc:
    st.markdown(proc_card, unsafe_allow_html=True)
with col_pess:
    st.markdown(pess_card, unsafe_allow_html=True)

# ── Backup (admin only) ───────────────────────────────────────────────────────
if usuario_admin():
    st.divider()
    dados_bytes = ler_bytes_workbook()
    if dados_bytes:
        st.download_button(
            label="⬇ Baixar dados.xlsx (backup)",
            data=dados_bytes,
            file_name="dados_portal_gestor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
