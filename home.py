import streamlit as st
import pandas as pd
from datetime import date
from utils.excel_io import ler_bytes_workbook
from utils.departamentos import listar_departamentos
from utils.pessoas import listar_colaboradores, listar_historico
from utils.manpower import calcular_manpower_por_departamento, listar_performance
from utils.ui import aplicar_estilos_globais, saudacao_periodo

# ── Dados ──────────────────────────────────────────────────────────────────────
aplicar_estilos_globais()

ativos       = listar_colaboradores(status="Ativo")
departamentos = listar_departamentos()
mp_dept      = calcular_manpower_por_departamento()
historico    = listar_historico()
performance  = listar_performance()

mp_total = sum(mp_dept.values())

ultima_perf = None
if performance:
    ultima_perf = sorted(performance, key=lambda p: (p.get("ano", 0), p.get("mes", 0)), reverse=True)[0]

meses_pt = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# ── CSS global ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Remove padding padrão do topo */
.block-container { padding-top: 1rem !important; }

/* ── Banner ── */
.banner {
    background: linear-gradient(135deg, rgba(255,253,248,0.96) 0%, rgba(242,234,217,0.96) 100%);
    border: 1px solid #e3d8c5;
    border-radius: 24px;
    padding: 28px 36px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #223645;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.banner-title { font-size: 30px; font-weight: 800; letter-spacing: -0.5px; margin: 0; color: #234055; }
.banner-sub   { font-size: 14px; color: #6f7a84; margin-top: 6px; }
.banner-badge {
    background: linear-gradient(135deg, #e7f2df 0%, #f1f7ea 100%);
    border: 1px solid #cddfc8;
    border-radius: 999px;
    padding: 10px 18px;
    text-align: center;
    color: #5e8668;
}
.banner-badge-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; opacity: 0.8; }
.banner-badge-value { font-size: 22px; font-weight: 800; margin-top: 2px; }

/* ── KPI cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.kpi-card {
    background: #fffdf8;
    border-radius: 20px;
    padding: 20px 20px 16px;
    border: 1px solid #e3d8c5;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: attr(data-icon);
    position: absolute;
    right: 14px;
    top: 14px;
    font-size: 26px;
    opacity: 0.13;
}
.kpi-label  { font-size: 12px; color: #6f7a84; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
.kpi-value  { font-size: 32px; font-weight: 800; color: #234055; line-height: 1.1; margin: 6px 0 4px; }
.kpi-sub    { font-size: 12px; color: #86909a; }

.kpi-card.accent-gold  { background: linear-gradient(180deg, #fffdf8 0%, #fbf4e6 100%); }
.kpi-card.accent-teal  { background: linear-gradient(180deg, #fffdf8 0%, #eef5f0 100%); }
.kpi-card.accent-green { background: linear-gradient(180deg, #fffdf8 0%, #edf6ec 100%); }
.kpi-value.green { color: #5e8668; }
.kpi-value.amber { color: #b78328; }

/* ── Departamento cards ── */
.dept-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.dept-card {
    background: #fffdf8;
    border: 1px solid #e3d8c5;
    border-top: 3px solid #c79536;
    border-radius: 18px;
    padding: 14px 18px;
    color: #223645;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.dept-name   { font-size: 12px; font-weight: 800; color: #234055; text-transform: uppercase; letter-spacing: 0.08em; }
.dept-pessoas { font-size: 26px; font-weight: 800; color: #223645; margin: 6px 0 1px; line-height: 1; }
.dept-label  { font-size: 11px; color: #7d8790; }
.dept-mp     { margin-top: 8px; padding-top: 8px; border-top: 1px solid #e6dece;
               display: flex; justify-content: space-between; align-items: center; }
.dept-mp-val { font-size: 15px; font-weight: 700; color: #234055; }
.dept-mp-label { font-size: 11px; color: #7d8790; }

/* ── Seção títulos ── */
.section-title {
    font-size: 13px; font-weight: 800; color: #234055;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 4px 0 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #eadfcd;
}

/* ── Movimentações ── */
.mov-list { list-style: none; padding: 0; margin: 0; }
.mov-item {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid #f1ebe1;
    font-size: 13px;
}
.mov-item:last-child { border-bottom: none; }
.mov-badge {
    flex-shrink: 0; width: 8px; height: 8px; border-radius: 50%;
}
.mov-badge.entrada { background: #2a7d4f; }
.mov-badge.saida   { background: #c0392b; }
.mov-nome   { font-weight: 700; color: #223645; flex: 1; }
.mov-cargo  { color: #7d8790; font-size: 12px; }
.mov-data   { color: #9ca5ad; font-size: 11px; flex-shrink: 0; }

/* ── Performance card ── */
.perf-card {
    background: linear-gradient(135deg, #2f5663 0%, #234055 100%);
    border-radius: 22px;
    padding: 20px 24px;
    color: white;
    margin-bottom: 14px;
    box-shadow: 0 16px 30px rgba(35, 64, 85, 0.18);
}
.perf-card.below {
    background: linear-gradient(135deg, #9b7a34 0%, #7e6128 100%);
}
.perf-title { font-size: 11px; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.08em; }
.perf-value { font-size: 42px; font-weight: 800; margin: 6px 0 2px; line-height: 1; }
.perf-meta  { font-size: 13px; opacity: 0.85; }
.perf-pct   { font-size: 15px; font-weight: 700; margin-top: 8px; }

/* ── Quick links ── */
.quick-link {
    display: block; background: #fffdf8; border: 1px solid #e3d8c5;
    border-radius: 18px; padding: 14px 16px;
    text-decoration: none; color: #234055;
    margin-bottom: 10px; transition: all 0.15s;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.quick-link:hover { background: #f7f0e1; border-color: #d7ba7a; }
.quick-link-icon  { font-size: 20px; margin-bottom: 4px; }
.quick-link-title { font-weight: 700; font-size: 14px; }
.quick-link-desc  { font-size: 12px; color: #7d8790; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Banner ─────────────────────────────────────────────────────────────────────
hoje = date.today()
data_fmt = hoje.strftime(f"%d {meses_pt[hoje.month]} %Y")

def _br(val, dec=2):
    if val is None:
        return "—"
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

if ultima_perf:
    mes_label = meses_pt[int(ultima_perf["mes"])]
    ano_short = str(int(ultima_perf["ano"]))[2:]
    perf_num = _br(ultima_perf.get('performance', 0), 1)
    badge_html = f'<div class="banner-badge"><div class="banner-badge-label">Performance {mes_label}/{ano_short}</div><div class="banner-badge-value">{perf_num}</div></div>'
else:
    badge_html = ""

st.markdown(f'<div class="banner"><div><div class="banner-title">{saudacao_periodo()}, Bruno Picinini</div><div class="banner-sub">Portal do Gestor &nbsp;&middot;&nbsp; operação, pessoas e performance centralizadas em um único painel &nbsp;&middot;&nbsp; {data_fmt}</div></div>{badge_html}</div>', unsafe_allow_html=True)

# ── KPI cards ──────────────────────────────────────────────────────────────────
pct_meta_str = "—"
pct_class = ""
if ultima_perf and ultima_perf.get("pct_meta"):
    pct = ultima_perf["pct_meta"] * 100
    pct_meta_str = _br(pct, 1) + "%"
    pct_class = "green" if pct >= 100 else "amber"

perf_val = _br(ultima_perf.get('performance', 0), 1) if ultima_perf else "—"
mp_total_str = _br(mp_total, 2)

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card" data-icon="👥">
        <div class="kpi-label">Colaboradores Ativos</div>
        <div class="kpi-value">{len(ativos)}</div>
        <div class="kpi-sub">quadro atual</div>
    </div>
    <div class="kpi-card accent-gold" data-icon="📊">
        <div class="kpi-label">Manpower Total</div>
        <div class="kpi-value">{mp_total_str}</div>
        <div class="kpi-sub">soma dos pesos ativos</div>
    </div>
    <div class="kpi-card accent-teal" data-icon="📈">
        <div class="kpi-label">Performance Atual</div>
        <div class="kpi-value {pct_class}">{perf_val}</div>
        <div class="kpi-sub">{pct_meta_str} da meta</div>
    </div>
    <div class="kpi-card accent-green" data-icon="🏢">
        <div class="kpi-label">Departamentos</div>
        <div class="kpi-value">{len(departamentos)}</div>
        <div class="kpi-sub">áreas operacionais</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Departamento cards ─────────────────────────────────────────────────────────
dept_cards_html = '<div class="dept-grid">'
for depto in departamentos:
    dept_ativos = [c for c in ativos if c.get("departamento_id") == depto["id"]]
    mp = mp_dept.get(depto["id"], 0)
    mp_str = _br(mp, 2) if mp > 0 else "—"
    dept_cards_html += f"""
    <div class="dept-card">
        <div class="dept-name">{depto['nome']}</div>
        <div class="dept-pessoas">{len(dept_ativos)}</div>
        <div class="dept-label">pessoas ativas</div>
        <div class="dept-mp">
            <div>
                <div class="dept-mp-val">{mp_str}</div>
                <div class="dept-mp-label">manpower</div>
            </div>
        </div>
    </div>"""
dept_cards_html += '</div>'
st.markdown(dept_cards_html, unsafe_allow_html=True)

# ── Linha inferior: movimentações + performance + atalhos ──────────────────────
col_mov, col_right = st.columns([3, 2], gap="large")

with col_mov:
    st.markdown('<div class="section-title">Últimas Movimentações</div>', unsafe_allow_html=True)

    if historico:
        colabs_map = {c["id"]: c for c in ativos + listar_colaboradores(status="Inativo")}
        items_html = '<ul class="mov-list">'
        for h in historico[:8]:
            tipo = h.get("tipo", "")
            badge_class = "entrada" if tipo == "Entrada" else "saida"
            nome = h.get("nome", "—")
            cargo = h.get("cargo", "")
            cid = h.get("colaborador_id")
            dept = colabs_map.get(cid, {}).get("departamento_nome", "—") if cid else "—"
            try:
                dt = pd.to_datetime(h["data"])
                data_str = f"{meses_pt[dt.month]}/{str(dt.year)[2:]}"
            except Exception:
                data_str = "—"
            items_html += f"""
            <li class="mov-item">
                <span class="mov-badge {badge_class}"></span>
                <span class="mov-nome">{nome}<br><span class="mov-cargo">{cargo} · {dept}</span></span>
                <span class="mov-data">{data_str}</span>
            </li>"""
        items_html += '</ul>'
        st.markdown(items_html, unsafe_allow_html=True)
    else:
        st.info("Nenhuma movimentação registrada.")

with col_right:
    # Performance card
    if ultima_perf:
        pct_val = (ultima_perf.get("pct_meta") or 0) * 100
        card_class = "perf-card" if pct_val >= 100 else "perf-card below"
        meta_val = ultima_perf.get("meta", 0)
        vol = ultima_perf.get("volume_score", 0)
        mes_label = meses_pt[int(ultima_perf["mes"])]
        ano_label = str(int(ultima_perf["ano"]))
        st.markdown(f"""
        <div class="{card_class}">
            <div class="perf-title">Performance · {mes_label}/{ano_label}</div>
            <div class="perf-value">{_br(ultima_perf.get('performance', 0), 1)}</div>
            <div class="perf-meta">Meta: {_br(meta_val, 1)} &nbsp;·&nbsp; Volume: {_br(vol, 0)}</div>
            <div class="perf-pct">{'✅' if pct_val >= 100 else '⚠️'} {_br(pct_val, 1)}% da meta</div>
        </div>
        """, unsafe_allow_html=True)

    # Atalhos
    st.markdown('<div class="section-title">Acesso Rápido</div>', unsafe_allow_html=True)
    st.markdown("""
    <a class="quick-link" href="/Organograma">
        <div class="quick-link-icon">🗂️</div>
        <div class="quick-link-title">Organograma</div>
        <div class="quick-link-desc">Visualize a estrutura e edite cargos</div>
    </a>
    <a class="quick-link" href="/Controle_de_Pessoas">
        <div class="quick-link-icon">👥</div>
        <div class="quick-link-title">Controle de Pessoas</div>
        <div class="quick-link-desc">Contratações, desligamentos e histórico</div>
    </a>
    <a class="quick-link" href="/KPIs">
        <div class="quick-link-icon">📊</div>
        <div class="quick-link-title">KPIs</div>
        <div class="quick-link-desc">Eficiência, manpower e volume score</div>
    </a>
    """, unsafe_allow_html=True)

# ── Backup ─────────────────────────────────────────────────────────────────────
st.divider()
dados_bytes = ler_bytes_workbook()
if dados_bytes:
    st.download_button(
        label="⬇ Baixar dados.xlsx (backup)",
        data=dados_bytes,
        file_name="dados_portal_gestor.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
