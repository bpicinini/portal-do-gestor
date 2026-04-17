"""Homepage — Landing institucional do Portal do Gestor.

Hub de navegação enxuto: banner de boas-vindas, destaque da liderança da
operação (Diretor e Gerente) e grid de departamentos. Cada card de
departamento leva ao Organograma filtrado pela respectiva área. KPIs,
volumes, alertas e manpower ficam nas páginas dedicadas.
"""

from datetime import date

import streamlit as st

from utils.auth import garantir_autenticado, obter_usuario_atual
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


def _iniciais(nome):
    partes = [p for p in str(nome or "").split() if p]
    if not partes:
        return "·"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


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
    margin-bottom: 26px;
}
.hm-lead-card {
    background: linear-gradient(135deg, rgba(35, 64, 85, 0.92) 0%, rgba(27, 53, 73, 0.95) 100%);
    border: 1px solid rgba(199, 149, 54, 0.32);
    border-left: 5px solid #c79536;
    border-radius: 22px;
    padding: 20px 22px;
    color: #f6ecd8;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 14px 36px rgba(15, 34, 50, 0.22);
}
.hm-lead-avatar {
    width: 62px; height: 62px;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, #e9c174, #c79536 55%, #8a6424);
    color: #1b3549;
    font-size: 22px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 6px 16px rgba(199, 149, 54, 0.3);
    letter-spacing: -0.02em;
}
.hm-lead-role {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 700;
    color: #e9c174;
    margin-bottom: 4px;
}
.hm-lead-name {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #ffffff;
    line-height: 1.2;
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
    border-left: 4px solid #c79536;
    border-radius: 20px;
    padding: 22px 24px 18px;
    min-height: 168px;
    box-shadow: 0 6px 24px rgba(35, 64, 85, 0.06);
    transition: all 0.2s ease;
}
.hm-deptc:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 40px rgba(35, 64, 85, 0.12);
    border-left-color: #234055;
    background: rgba(255, 255, 255, 0.72);
}
.hm-deptc-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 14px;
}
.hm-deptc-name {
    font-size: 20px;
    font-weight: 800;
    color: #234055;
    letter-spacing: -0.01em;
    line-height: 1.2;
}
.hm-deptc-count {
    background: rgba(35, 64, 85, 0.08);
    color: #234055;
    font-weight: 800;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 999px;
    white-space: nowrap;
}
.hm-deptc-leaders {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.hm-deptc-leader {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-size: 13px;
    line-height: 1.35;
}
.hm-deptc-leader-role {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    color: #c79536;
    min-width: 96px;
}
.hm-deptc-leader-name {
    color: #234055;
    font-weight: 700;
}
.hm-deptc-empty {
    font-size: 12px;
    color: #9aa2ab;
    font-style: italic;
}

/* ── Botão "Explorar" como link minimalista ──────────────────────────── */
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] .stButton > button:focus:not(:active) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: #c79536 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 8px 4px 18px !important;
    text-align: right !important;
    transition: color 0.18s ease, transform 0.18s ease !important;
}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stMain"] .stButton > button:active {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #234055 !important;
    transform: translateX(2px);
}

/* ── Rodapé ────────────────────────────────────────────────────────────── */
.hm-footnote {
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid rgba(35, 64, 85, 0.08);
    font-size: 11px;
    color: #7d8790;
    text-align: center;
    font-weight: 500;
}

/* ── Responsivo ────────────────────────────────────────────────────────── */
@media (max-width: 900px) {
    .hm-lead-strip { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
    .hm-banner { flex-direction: column; align-items: flex-start; gap: 10px; padding: 20px 22px; }
    .hm-banner-title { font-size: 22px; }
    .hm-lead-card { padding: 16px 18px; }
    .hm-lead-avatar { width: 52px; height: 52px; font-size: 18px; }
    .hm-lead-name { font-size: 17px; }
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
        <div class="hm-lead-avatar">{_iniciais(l["nome"])}</div>
        <div>
            <div class="hm-lead-role">{l["cargo"]}</div>
            <div class="hm-lead-name">{l["nome"]}</div>
        </div>
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


# Grid 2×2
for i in range(0, len(dept_cards), 2):
    col_a, col_b = st.columns(2, gap="medium")
    linha = dept_cards[i : i + 2]
    for col, card in zip((col_a, col_b), linha):
        with col:
            st.markdown(_render_dept_card(card), unsafe_allow_html=True)
            if st.button(
                f"Explorar {card['nome']} →",
                key=f"go_dept_{card['id']}",
                use_container_width=True,
            ):
                _ir_para_dept(card["nome"])


# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hm-footnote">
        Para KPIs, volumes e indicadores operacionais, acesse as páginas específicas pelo menu lateral.
    </div>
    """,
    unsafe_allow_html=True,
)
