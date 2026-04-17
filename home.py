"""Homepage — Landing institucional do Portal do Gestor.

Hub de navegação enxuto: banner de boas-vindas, destaque da liderança da
operação (Diretor e Gerente) e grid de departamentos. Cada card de
departamento leva ao Organograma filtrado pela respectiva área. KPIs,
volumes, alertas e manpower ficam nas páginas dedicadas.
"""

from datetime import date

import streamlit as st

from utils.auth import garantir_autenticado, obter_usuario_atual, usuario_admin
from utils.departamentos import listar_cargos, listar_departamentos
from utils.pessoas import listar_colaboradores
from utils.ui import aplicar_estilos_globais


# ── Bootstrap ──────────────────────────────────────────────────────────────────
aplicar_estilos_globais()
garantir_autenticado()
usuario_logado = obter_usuario_atual() or {}

ativos = listar_colaboradores(status="Ativo")
departamentos = listar_departamentos()
cargos = listar_cargos()
cargo_map = {c["id"]: c for c in cargos}

meses_pt = [
    "", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]

# ── Identificação da liderança ────────────────────────────────────────────────
# Faixas de nível reaproveitadas do desenho do Organograma: Coordenação e
# Supervisão cobrem os papéis de liderança imediata exibidos nos cards.
NIVEL_COORD = (1.5, 2)
NIVEL_SUP = (2.5, 2.5)


def _nivel_do(colab):
    if not colab:
        return None
    cargo = cargo_map.get(colab.get("cargo_id")) or {}
    return cargo.get("nivel")


def _cargo_nome(colab):
    if not colab:
        return ""
    cargo = cargo_map.get(colab.get("cargo_id")) or {}
    return cargo.get("nome") or ""


def _em_faixa(nivel, faixa):
    if nivel is None:
        return False
    return faixa[0] <= nivel <= faixa[1]


def _procurar_por_nome(termos):
    """Retorna o primeiro colaborador ativo cujo nome contém todos os termos."""
    termos_norm = [t.lower() for t in termos]
    for c in ativos:
        nome = str(c.get("nome") or "").lower()
        if all(t in nome for t in termos_norm):
            return c
    return None


# Diretor e Gerente: busca dinâmica + fallback institucional
diretor = _procurar_por_nome(["gabriel", "spohr"])
gerente = _procurar_por_nome(["bruno", "picinini"])

LIDERANCA = [
    {
        "nome": diretor["nome"] if diretor else "Gabriel Spohr",
        "cargo": "Diretor de Operações",
    },
    {
        "nome": gerente["nome"] if gerente else "Bruno Picinini",
        "cargo": "Gerente de Operações",
    },
]


# ── Departamentos em foco ─────────────────────────────────────────────────────
# A homepage dá destaque apenas aos quatro departamentos amparados pelo portal.
DEPTS_FOCO = ["Importação", "Agenciamento", "Exportação", "Seguro Internacional"]


def _encontrar_dept(nome_alvo):
    alvo = nome_alvo.lower()
    for d in departamentos:
        if str(d.get("nome") or "").lower() == alvo:
            return d
    return None


def _lideres_do_dept(dept_id):
    """Devolve (coordenador, supervisor) — cada um pode ser None."""
    coord = None
    sup = None
    for c in ativos:
        if c.get("departamento_id") != dept_id:
            continue
        nivel = _nivel_do(c)
        if coord is None and _em_faixa(nivel, NIVEL_COORD):
            coord = c
        elif sup is None and _em_faixa(nivel, NIVEL_SUP):
            sup = c
        if coord and sup:
            break
    return coord, sup


dept_cards = []
for nome in DEPTS_FOCO:
    d = _encontrar_dept(nome)
    if d is None:
        continue
    total_ativos = sum(1 for c in ativos if c.get("departamento_id") == d["id"])
    coord, sup = _lideres_do_dept(d["id"])
    dept_cards.append(
        {
            "id": d["id"],
            "nome": d["nome"],
            "total": total_ativos,
            "coord": coord,
            "sup": sup,
        }
    )


# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.block-container { padding-top: 1rem !important; }

/* ── Banner de boas-vindas ───────────────────────────────────────────────── */
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

/* ── Liderança da operação ─────────────────────────────────────────────── */
.hm-lead-strip {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    margin-bottom: 28px;
}
.hm-lead-card {
    background: transparent;
    border: none;
    border-left: 3px solid #c79536;
    border-radius: 0;
    padding: 6px 0 6px 18px;
    color: #234055;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: none;
}
.hm-lead-role {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: #c79536;
    margin-bottom: 6px;
}
.hm-lead-name {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: #234055;
    line-height: 1.15;
}

/* ── Título da seção ───────────────────────────────────────────────────── */
.hm-section-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
}
.hm-section-title {
    font-size: 12px;
    font-weight: 800;
    color: #234055;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}
.hm-section-hint {
    font-size: 11px;
    color: #7d8790;
    font-weight: 600;
}

/* ── Cards de departamento ─────────────────────────────────────────────── */
.hm-deptc {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.55);
    border-left: 5px solid #c79536;
    border-radius: 22px;
    padding: 26px 30px 24px;
    min-height: 210px;
    box-shadow: 0 6px 24px rgba(35, 64, 85, 0.06);
    transition: all 0.22s ease;
}
[data-testid="stColumn"]:has(.hm-deptc):hover .hm-deptc {
    transform: translateY(-3px);
    box-shadow: 0 18px 44px rgba(35, 64, 85, 0.14);
    border-left-color: #234055;
    background: rgba(255, 255, 255, 0.78);
}
.hm-deptc-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
    margin-bottom: 22px;
}
.hm-deptc-name {
    font-size: 28px;
    font-weight: 800;
    color: #234055;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.hm-deptc-count {
    background: rgba(35, 64, 85, 0.08);
    color: #234055;
    font-weight: 800;
    font-size: 15px;
    padding: 8px 16px;
    border-radius: 999px;
    white-space: nowrap;
}
.hm-deptc-leaders {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.hm-deptc-leader {
    display: flex;
    align-items: baseline;
    gap: 12px;
    font-size: 16px;
    line-height: 1.3;
}
.hm-deptc-leader-role {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 800;
    color: #c79536;
    min-width: 120px;
}
.hm-deptc-leader-name {
    color: #234055;
    font-weight: 700;
}
.hm-deptc-empty {
    font-size: 13px;
    color: #9aa2ab;
    font-style: italic;
}

/* Card inteiro clicável: overlay transparente do st.button sobre o card */
[data-testid="stColumn"]:has(.hm-deptc) {
    position: relative;
}
[data-testid="stColumn"]:has(.hm-deptc) [data-testid="stButton"] {
    position: absolute !important;
    inset: 0 !important;
    margin: 0 !important;
    z-index: 5 !important;
}
[data-testid="stColumn"]:has(.hm-deptc) [data-testid="stButton"] > button {
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    cursor: pointer !important;
}

/* ── Atalhos de módulos (cards pequenos, transparentes, linha única) ── */
.hm-mods-title {
    font-size: 11px;
    font-weight: 800;
    color: #234055;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 32px 0 12px;
}
[data-testid="stMain"] [data-testid="stPageLink"] a {
    background: transparent !important;
    border: 1px solid rgba(35, 64, 85, 0.12) !important;
    border-radius: 14px !important;
    padding: 12px 10px !important;
    min-height: 54px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
[data-testid="stMain"] [data-testid="stPageLink"] a:hover {
    background: rgba(199, 149, 54, 0.08) !important;
    border-color: rgba(199, 149, 54, 0.45) !important;
    transform: translateY(-1px);
}
[data-testid="stMain"] [data-testid="stPageLink"] a > div,
[data-testid="stMain"] [data-testid="stPageLink"] a p,
[data-testid="stMain"] [data-testid="stPageLink"] a span {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #234055 !important;
    margin: 0 !important;
    white-space: nowrap !important;
}
[data-testid="stMain"] [data-testid="stPageLink"] a:hover p,
[data-testid="stMain"] [data-testid="stPageLink"] a:hover span,
[data-testid="stMain"] [data-testid="stPageLink"] a:hover > div {
    color: #c79536 !important;
}

/* ── Responsivo ────────────────────────────────────────────────────────── */
@media (max-width: 900px) {
    .hm-lead-strip { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
    .hm-banner { flex-direction: column; align-items: flex-start; gap: 10px; padding: 20px 22px; }
    .hm-banner-title { font-size: 22px; }
    .hm-lead-card { padding: 4px 0 4px 14px; }
    .hm-lead-name { font-size: 18px; }
    .hm-deptc { padding: 20px 22px; min-height: auto; }
    .hm-deptc-name { font-size: 22px; }
    .hm-deptc-leader { font-size: 14px; }
    .hm-deptc-leader-role { min-width: 100px; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Banner de boas-vindas ─────────────────────────────────────────────────────
hoje = date.today()
data_fmt = hoje.strftime(f"%d {meses_pt[hoje.month]} %Y")

st.markdown(
    f"""
    <div class="hm-banner">
        <div>
            <div class="hm-banner-title">Bem-vindo, {usuario_logado.get("nome", "Usuário")}</div>
            <div class="hm-banner-sub">Portal do Gestor &middot; hub institucional de departamentos e lideranças da operação</div>
        </div>
        <div class="hm-banner-date">{data_fmt}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Liderança da operação ─────────────────────────────────────────────────────
lead_cards_html = ""
for l in LIDERANCA:
    lead_cards_html += f"""
    <div class="hm-lead-card">
        <div class="hm-lead-role">{l["cargo"]}</div>
        <div class="hm-lead-name">{l["nome"]}</div>
    </div>"""

st.markdown(
    f"""
    <div class="hm-section-head">
        <span class="hm-section-title">Liderança da Operação</span>
    </div>
    <div class="hm-lead-strip">{lead_cards_html}</div>
    """,
    unsafe_allow_html=True,
)


# ── Departamentos ─────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="hm-section-head">
        <span class="hm-section-title">Departamentos · {len(dept_cards)} áreas</span>
        <span class="hm-section-hint">clique em um card para ver o organograma da área</span>
    </div>
    """,
    unsafe_allow_html=True,
)


def _render_leader_line(cargo_nome_original, default_role, pessoa):
    """Uma linha de liderança dentro do card. Sufixo do cargo ajusta gênero."""
    if not pessoa:
        return ""
    nome = pessoa.get("nome", "—")
    # Usa o nome do cargo real quando disponível (ex.: "Coordenadora", "Supervisor")
    rotulo = cargo_nome_original or default_role
    return (
        f'<div class="hm-deptc-leader">'
        f'<span class="hm-deptc-leader-role">{rotulo}</span>'
        f'<span class="hm-deptc-leader-name">{nome}</span>'
        f"</div>"
    )


def _render_dept_card(card):
    coord = card["coord"]
    sup = card["sup"]
    coord_html = _render_leader_line(_cargo_nome(coord), "Coordenação", coord)
    sup_html = _render_leader_line(_cargo_nome(sup), "Supervisão", sup)
    if not coord_html and not sup_html:
        leaders_html = '<div class="hm-deptc-empty">Liderança a definir</div>'
    else:
        leaders_html = coord_html + sup_html

    return f"""
    <div class="hm-deptc">
        <div class="hm-deptc-top">
            <div class="hm-deptc-name">{card["nome"]}</div>
            <div class="hm-deptc-count">{card["total"]} pessoas</div>
        </div>
        <div class="hm-deptc-leaders">{leaders_html}</div>
    </div>
    """


def _ir_para_dept(nome):
    st.session_state["filtro_org"] = nome
    st.switch_page("pages/1_Organograma.py")


# Grid 2×2 — cada card é inteiramente clicável via overlay invisível
for i in range(0, len(dept_cards), 2):
    col_a, col_b = st.columns(2, gap="medium")
    linha = dept_cards[i : i + 2]
    for col, card in zip((col_a, col_b), linha):
        with col:
            st.markdown(_render_dept_card(card), unsafe_allow_html=True)
            if st.button(
                " ",
                key=f"go_dept_{card['id']}",
                use_container_width=True,
            ):
                _ir_para_dept(card["nome"])


# ── Atalhos para módulos ──────────────────────────────────────────────────────
modulos = [
    ("pages/1_Organograma.py", "Organograma", "🗂️"),
    ("pages/3_Manpower_e_Eficiencia.py", "KPIs", "📊"),
    ("pages/5_Processos_360.py", "Processos 360", "🚢"),
    ("pages/6_Restituicoes.py", "Restituições", "💰"),
]
if usuario_admin():
    modulos.append(("pages/4_Usuarios.py", "Usuários", "🔐"))

st.markdown(
    '<div class="hm-mods-title">Módulos</div>',
    unsafe_allow_html=True,
)
mod_cols = st.columns(len(modulos), gap="small")
for col, (pg, label, icon) in zip(mod_cols, modulos):
    with col:
        st.page_link(pg, label=label, icon=icon, use_container_width=True)
