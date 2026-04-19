from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.departamentos import listar_cargos, listar_departamentos
from utils.organograma import construir_estrutura_reportes
from utils.pessoas import atualizar_responsavel_direto, contratar, desligar, listar_colaboradores, listar_historico
from utils.ui import aplicar_estilos_globais, is_dark_mode, renderizar_cabecalho_pagina, renderizar_dataframe


garantir_autenticado()
aplicar_estilos_globais()
renderizar_cabecalho_pagina(
    "Organograma",
    "Estrutura da operacao com leitura por niveis e uma visao paralela por reportes diretos.",
    badge="Estrutura ativa",
)

departamentos = listar_departamentos()
todos_ativos = listar_colaboradores(status="Ativo")
estrutura_reportes = construir_estrutura_reportes(todos_ativos)

st.markdown(
    """
<style>
.card-gerencia {
    background:
        radial-gradient(circle at top right, rgba(242, 212, 145, 0.22), transparent 30%),
        linear-gradient(135deg, #0f2232 0%, #1b3549 55%, #111111 100%);
    color: white;
    border-radius: 22px;
    padding: 18px 20px;
    margin: 4px 2px;
    min-height: 92px;
    border: 1px solid rgba(216, 165, 67, 0.38);
    border-left: 6px solid #d8a543;
    box-shadow: 0 18px 40px rgba(15, 34, 50, 0.28);
    position: relative;
    overflow: hidden;
}
.card-coordenador {
    background: linear-gradient(135deg, #1b3a4d 0%, #111111 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 5px solid #5ba8cc;
    box-shadow: 0 10px 28px rgba(27, 58, 77, 0.18);
}
.card-supervisor {
    background: linear-gradient(135deg, #2c5268 0%, #3c6478 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 4px solid #80c2df;
    box-shadow: 0 8px 22px rgba(44, 82, 104, 0.16);
}
.card-gerencia .nome, .card-coordenador .nome, .card-supervisor .nome {
    font-weight: 700;
    font-size: 14px;
    line-height: 1.3;
}
.card-gerencia .nome {
    font-size: 16px;
    letter-spacing: -0.02em;
}
.card-gerencia .cargo, .card-coordenador .cargo, .card-supervisor .cargo {
    font-size: 12px;
    opacity: 0.82;
    margin-top: 2px;
}
.card-gerencia .cargo {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 800;
    color: #f4d491;
    opacity: 1;
}
.card-gerencia .info, .card-coordenador .info, .card-supervisor .info {
    font-size: 11px;
    opacity: 0.68;
    margin-top: 2px;
}
/* Analistas e especialistas (nivel 3–6): tint sutil, borda azul */
.card-analista {
    background: #edf3f7;
    border: 1px solid #c4d6e0;
    border-left: 4px solid #6aaac8;
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 4px 14px rgba(35, 64, 85, 0.07);
}
.card-analista.nh { border-left: 4px solid #3b82f6; }
.card-analista.ita { border-left: 4px solid #16a34a; }
.card-analista .nome {
    font-weight: 700;
    font-size: 13px;
    color: #111111;
    line-height: 1.3;
}
.card-analista .cargo { font-size: 11px; color: #6E6E73; margin-top: 2px; }
.card-analista .info  { font-size: 11px; color: #6E6E73; margin-top: 1px; }
/* Assistentes / Estagiários (nivel 7+): neutro, apenas borda fina */
.card-op {
    background: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-left: 4px solid #E5E5EA;
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 4px 14px rgba(35, 64, 85, 0.06);
}
.card-op.nh  { border-left: 4px solid #3b82f6; }
.card-op.ita { border-left: 4px solid #16a34a; }
.card-op .nome  { font-weight: 700; font-size: 13px; color: #111111; line-height: 1.3; }
.card-op .cargo { font-size: 11px; color: #6E6E73; margin-top: 2px; }
.card-op .info  { font-size: 11px; color: #6E6E73; margin-top: 1px; }
.badge-nh {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 999px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 800;
    margin-top: 3px;
}
.badge-ita {
    display: inline-block;
    background: #dcfce7;
    color: #166534;
    border-radius: 999px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 800;
    margin-top: 3px;
}
.nivel-label {
    font-size: 12px;
    font-weight: 700;
    color: #111111;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 14px 0 6px 0;
    padding-left: 8px;
    border-left: 3px solid #111111;
}
.conector {
    text-align: center;
    color: #6E6E73;
    font-size: 20px;
    margin: 2px 0;
}
.report-leaders {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 14px;
}
.report-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
}
.report-column {
    background: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 20px;
    padding: 14px;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.report-head {
    background: #edf3f7;
    border: 1px solid #c4d6e0;
    border-left: 4px solid #6aaac8;
    border-radius: 16px;
    padding: 14px 16px;
}
.report-head.nh  { border-left: 4px solid #3b82f6; }
.report-head.ita { border-left: 4px solid #16a34a; }
.report-head .nome {
    font-size: 14px;
    font-weight: 800;
    line-height: 1.2;
    color: #111111;
}
.report-head .cargo {
    font-size: 11px;
    color: #6E6E73;
    margin-top: 3px;
}
.report-head .meta {
    font-size: 11px;
    color: #6E6E73;
    margin-top: 5px;
}
.report-stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
}
.report-child {
    background: #FAFAFA;
    border: 1px solid #E5E5EA;
    border-left: 4px solid #E5E5EA;
    border-radius: 14px;
    padding: 11px 12px;
}
.report-child.nh { border-left: 4px solid #3b82f6; }
.report-child.ita { border-left: 4px solid #16a34a; }
.report-child .nome {
    color: #111111;
    font-size: 13px;
    font-weight: 700;
    line-height: 1.25;
}
.report-child .cargo {
    color: #6b7680;
    font-size: 11px;
    margin-top: 2px;
}
.report-child .meta {
    color: #89939b;
    font-size: 11px;
    margin-top: 5px;
}
.report-source {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 0.16rem 0.5rem;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.04em;
    margin-top: 8px;
}
.report-source.seed    { background: #e5f1dd; color: #58785b; }
.report-source.definido { background: #d8edf6; color: #1a6080; }
.report-source.fallback { background: #FAFAFA; color: #6E6E73; }
.report-empty {
    color: #7a848d;
    font-size: 12px;
    padding: 8px 2px 2px;
}
.lider-secao {
    border: 1px solid #E5E5EA;
    border-top: 4px solid #111111;
    border-radius: 18px;
    padding: 16px 16px 12px;
    margin-bottom: 18px;
    background: #FFFFFF;
}
.lider-secao-topo {
    margin-bottom: 14px;
}
.filtro-label {
    font-size: 11px;
    font-weight: 700;
    color: #9aa4ae;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 2px;
}
/* Botões de filtro em colunas: pills compactos e sutis */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
    border-radius: 999px !important;
    font-size: 12px !important;
    padding: 3px 14px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    min-height: 0 !important;
    height: auto !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #E5E5EA !important;
    color: #6E6E73 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: rgba(17, 17, 17, 0.04) !important;
    border-color: #111111 !important;
    color: #111111 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] {
    background: #111111 !important;
    border: 1px solid #111111 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] * {
    color: #FFFFFF !important;
}

/* Evita painel branco grande na aba de reportes (mantém comportamento igual ao restante da página) */
div[data-testid="stExpander"] {
    background: transparent !important;
}
div[data-testid="stExpanderDetails"] {
    background: transparent !important;
}
</style>
""",
    unsafe_allow_html=True,
)

if is_dark_mode():
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] {
            background: #1f3b52 !important;
            border-color: #2b4a63 !important;
            color: #d4dae2 !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] * {
            color: #d4dae2 !important;
        }
        .report-column,
        .lider-secao,
        .report-child,
        .report-source.fallback {
            background: #161b22 !important;
            border-color: #30363d !important;
        }
        .report-head {
            background: linear-gradient(135deg, #1b3245 0%, #213a4f 100%) !important;
            border-color: #2b4a63 !important;
        }
        div[data-testid="stExpander"],
        div[data-testid="stExpanderDetails"] {
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

NIVEL_LABEL = {
    0.5: "Gerencia",
    1: "Gerencia",
    2: "Coordenacao",
    2.5: "Supervisao",
    3: "Especialistas",
    4: "Analistas Senior",
    5: "Analistas Pleno",
    6: "Analistas Junior",
    7: "Assistentes",
    8: "Estagiarios",
    9: "Jovens Aprendizes",
}


def _nivel(pessoa):
    try:
        return float(pessoa.get("cargo_nivel", 99) or 99)
    except (TypeError, ValueError):
        return 99.0


def _unidade_class(unidade):
    if unidade == "Novo Hamburgo":
        return "nh"
    if unidade == "Itajaí":
        return "ita"
    return ""


def _badge_unidade(unidade):
    cls = _unidade_class(unidade)
    if cls:
        return f'<span class="badge-{cls}">{escape(unidade)}</span>'
    return escape(str(unidade))


def _card(css_class, nome, cargo, unidade, peso=None):
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    peso_str = f" · MP {peso:.2f}" if peso is not None else ""
    badge = _badge_unidade(unidade) if unidade else ""
    return (
        f'<div class="{css_class}{extra}">'
        f'<div class="nome">{escape(str(nome))}</div>'
        f'<div class="cargo">{escape(str(cargo))}{escape(peso_str)}</div>'
        f'<div class="info">{badge}</div>'
        f"</div>"
    )


def card_para_nivel(pessoa):
    nivel = _nivel(pessoa)
    nome = pessoa["nome"]
    cargo = pessoa["cargo_nome"]
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "")
    peso = pessoa.get("peso_manpower")

    if nivel <= 1:
        return _card("card-gerencia", nome, cargo, unidade)
    if nivel <= 2.0:
        return _card("card-coordenador", nome, cargo, unidade)
    if nivel <= 2.5:
        return _card("card-supervisor", nome, cargo, unidade)
    if nivel < 7:
        return _card("card-analista", nome, cargo, unidade, peso=peso)
    return _card("card-op", nome, cargo, unidade, peso=peso)


def _card_reporte_analista(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    return (
        f'<div class="report-head{extra}">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        "</div>"
    )


def _card_reporte_subordinado(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    return (
        f'<div class="report-child{extra}">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        "</div>"
    )


# ── Filtros ──────────────────────────────────────────────────────────────────

if "filtro_org" not in st.session_state:
    st.session_state.filtro_org = "Todos"
if "filtro_unidade" not in st.session_state:
    st.session_state.filtro_unidade = "Todas"

st.markdown('<div class="filtro-label">Departamento</div>', unsafe_allow_html=True)
_opcoes_dept = ["Todos"] + [d["nome"] for d in departamentos]
_dcols = st.columns(len(_opcoes_dept))
for _i, _opt in enumerate(_opcoes_dept):
    with _dcols[_i]:
        if st.button(
            _opt,
            key=f"_dtag_{_i}",
            type="primary" if st.session_state.filtro_org == _opt else "secondary",
            use_container_width=True,
        ):
            st.session_state.filtro_org = _opt
            st.rerun()

st.markdown('<div class="filtro-label" style="margin-top:10px">Unidade</div>', unsafe_allow_html=True)
_opcoes_uni = ["Todas", "Novo Hamburgo", "Itajaí"]
_ucols = st.columns(len(_opcoes_uni))
for _i, _opt in enumerate(_opcoes_uni):
    with _ucols[_i]:
        if st.button(
            _opt,
            key=f"_utag_{_i}",
            type="primary" if st.session_state.filtro_unidade == _opt else "secondary",
            use_container_width=True,
        ):
            st.session_state.filtro_unidade = _opt
            st.rerun()

filtro_dept = st.session_state.filtro_org
filtro_unidade = st.session_state.filtro_unidade


def _filtrar(pessoas):
    resultado = pessoas
    if filtro_dept != "Todos":
        resultado = [p for p in resultado if p.get("departamento_nome") == filtro_dept]
    if filtro_unidade != "Todas":
        resultado = [p for p in resultado if str(p.get("unidade") or "") == filtro_unidade]
    return resultado


# Gerência geral
gerencia_geral = [c for c in todos_ativos if _nivel(c) <= 1]

MESES_PT_ORG = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

tab_niveis, tab_reportes, tab_quadro, tab_gestao = st.tabs(
    ["Visao por niveis", "Visao por reportes", "Quadro completo", "Gestao de equipe"]
)

# ── Tab: Visão por níveis ────────────────────────────────────────────────────
with tab_niveis:
    st.subheader("Visao por niveis")

    for depto in departamentos:
        if filtro_dept != "Todos" and depto["nome"] != filtro_dept:
            continue

        dept_colabs = listar_colaboradores(status="Ativo", departamento_id=int(depto["id"]))
        ids_dept = {c.get("id") for c in dept_colabs}
        gerencia_extra = [g for g in gerencia_geral if g.get("id") not in ids_dept]
        dept_todos = gerencia_extra + dept_colabs

        # Aplica filtro de unidade (exceto na gerência geral)
        if filtro_unidade != "Todas":
            dept_filtrado = gerencia_extra + [
                p for p in dept_colabs if str(p.get("unidade") or "") == filtro_unidade
            ]
        else:
            dept_filtrado = dept_todos

        if not dept_filtrado:
            continue

        with st.expander(
            f"**{depto['nome']}** | {len(dept_filtrado)} pessoas",
            expanded=(filtro_dept != "Todos"),
        ):
            niveis = {}
            for pessoa in dept_filtrado:
                niveis.setdefault(_nivel(pessoa), []).append(pessoa)

            nivel_anterior = None
            for nivel in sorted(niveis):
                pessoas = sorted(niveis[nivel], key=lambda item: item["nome"])
                if nivel_anterior is not None:
                    st.markdown('<div class="conector">↓</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="nivel-label">{NIVEL_LABEL.get(nivel, f"Nivel {nivel}")}</div>',
                    unsafe_allow_html=True,
                )
                n_cols = min(len(pessoas), 2) if nivel <= 2.5 else min(len(pessoas), 4)
                cols = st.columns(max(n_cols, 1))
                for idx, pessoa in enumerate(pessoas):
                    with cols[idx % len(cols)]:
                        st.markdown(card_para_nivel(pessoa), unsafe_allow_html=True)
                nivel_anterior = nivel

# ── Tab: Visão por reportes ──────────────────────────────────────────────────
with tab_reportes:
    st.subheader("Visao por reportes imediatos")
    st.caption("Reportes definidos no Quadro completo.")

    def _html_grupo_analista(grupo):
        """Renderiza coluna de um analista com seus subordinados."""
        html = '<div class="report-column">'
        html += _card_reporte_analista(grupo["analista"])
        if grupo["reportes"]:
            html += '<div class="report-stack">'
            for p in grupo["reportes"]:
                html += _card_reporte_subordinado(p)
            html += "</div>"
        else:
            html += '<div class="report-empty">Nenhum reporte alocado.</div>'
        html += "</div>"
        return html

    for bloco in estrutura_reportes:
        if filtro_dept != "Todos" and bloco["departamento"] != filtro_dept:
            continue

        # IDs presentes no bloco para detectar gerência geral cross-dept
        ids_bloco = {p.get("id") for p in bloco["lideres"]}
        gerencia_extra_rep = [g for g in gerencia_geral if g.get("id") not in ids_bloco]

        # Conta total de pessoas para o header do expander
        def _conta_secao(secao):
            total = 1  # o lider
            for ga in secao["grupos_analistas"]:
                total += 1 + len(ga["reportes"])
            total += len(secao["reportes_diretos"])
            return total

        secoes = bloco.get("secoes_lider", [])
        sem_aloc = bloco.get("sem_alocacao", [])
        grupos_sem_lider = bloco.get("grupos_sem_lider", [])

        # Aplica filtro de unidade
        if filtro_unidade != "Todas":
            def _filtra_secao(secao):
                lider_ok = str(secao["lider"].get("unidade") or "") == filtro_unidade
                grupos_f = [
                    {
                        "analista": g["analista"],
                        "reportes": [
                            p for p in g["reportes"]
                            if str(p.get("unidade") or "") == filtro_unidade
                        ],
                    }
                    for g in secao["grupos_analistas"]
                    if str(g["analista"].get("unidade") or "") == filtro_unidade
                    or any(str(p.get("unidade") or "") == filtro_unidade for p in g["reportes"])
                ]
                rd_f = [p for p in secao["reportes_diretos"] if str(p.get("unidade") or "") == filtro_unidade]
                if lider_ok or grupos_f or rd_f:
                    return {**secao, "grupos_analistas": grupos_f, "reportes_diretos": rd_f}
                return None

            secoes = [s for s in [_filtra_secao(s) for s in secoes] if s]
            grupos_sem_lider = [
                {
                    "analista": g["analista"],
                    "reportes": [
                        p for p in g["reportes"]
                        if str(p.get("unidade") or "") == filtro_unidade
                    ],
                }
                for g in grupos_sem_lider
                if str(g["analista"].get("unidade") or "") == filtro_unidade
                or any(str(p.get("unidade") or "") == filtro_unidade for p in g["reportes"])
            ]
            sem_aloc = [p for p in sem_aloc if str(p.get("unidade") or "") == filtro_unidade]

        dept_total = (
            len(gerencia_extra_rep)
            + sum(_conta_secao(s) for s in secoes)
            + sum(1 + len(g["reportes"]) for g in grupos_sem_lider)
            + len(sem_aloc)
        )

        with st.expander(
            f"**{bloco['departamento']}** | {dept_total} pessoas",
            expanded=(filtro_dept != "Todos"),
        ):
            # Gerência geral cross-dept
            if gerencia_extra_rep:
                st.markdown('<div class="nivel-label">Gerência</div>', unsafe_allow_html=True)
                h = '<div class="report-leaders">'
                for p in gerencia_extra_rep:
                    h += card_para_nivel(p)
                h += "</div>"
                st.markdown(h, unsafe_allow_html=True)

            # Seções por lider — cada seção é uma caixa delimitada
            for secao in secoes:
                lider = secao["lider"]
                grupos_a = secao["grupos_analistas"]
                rep_dir = secao["reportes_diretos"]

                html = '<div class="lider-secao">'
                html += '<div class="lider-secao-topo">'
                html += card_para_nivel(lider)
                html += "</div>"

                if grupos_a:
                    html += '<div class="report-grid">'
                    for grupo in grupos_a:
                        html += _html_grupo_analista(grupo)
                    html += "</div>"

                if rep_dir:
                    html += '<div class="report-stack" style="margin-top:10px">'
                    for p in rep_dir:
                        html += _card_reporte_subordinado(p)
                    html += "</div>"

                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

            # Analistas sem lider definido
            if grupos_sem_lider:
                st.markdown('<div class="nivel-label">Analistas (sem liderança definida)</div>', unsafe_allow_html=True)
                html = '<div class="report-grid">'
                for grupo in grupos_sem_lider:
                    html += _html_grupo_analista(grupo)
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

            # Sem alocação definida
            if sem_aloc:
                st.markdown('<div class="nivel-label">Sem alocação definida</div>', unsafe_allow_html=True)
                html = '<div class="report-leaders">'
                for p in sem_aloc:
                    html += card_para_nivel(p)
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)


# ── Tab: Quadro completo ─────────────────────────────────────────────────────
with tab_quadro:
    st.subheader("Quadro completo")
    st.caption(
        "Edite a coluna 'Responsável Direto' diretamente na tabela e clique em Salvar. "
        "O organograma de reportes reflete imediatamente."
    )
    if todos_ativos:
        df_raw = pd.DataFrame(todos_ativos)

        if "responsavel_direto" not in df_raw.columns:
            df_raw["responsavel_direto"] = None

        _analistas = [p for p in todos_ativos if 3 <= float(p.get("cargo_nivel") or 99) < 7]
        _lideres_resp = [p for p in todos_ativos if 1 < float(p.get("cargo_nivel") or 99) <= 2.5]
        _opcoes_resp = [""] + sorted({p["nome"] for p in _lideres_resp + _analistas})

        df_quad = df_raw[[
            "id", "nome", "departamento_nome", "cargo_nome", "cargo_nivel",
            "peso_manpower", "unidade", "gestor_direto", "responsavel_direto",
        ]].copy()
        df_quad.columns = [
            "ID", "Nome", "Departamento", "Cargo", "Nivel",
            "MP", "Und.", "Gestor", "Responsável Direto",
        ]

        # Indicador visual de unidade (coluna extra não editável)
        df_quad.insert(6, "U", df_quad["Und."].map(
            {"Novo Hamburgo": "🔵 NH", "Itajaí": "🟢 ITJ"}
        ).fillna("—"))

        if filtro_dept != "Todos":
            df_quad = df_quad[df_quad["Departamento"] == filtro_dept]
        if filtro_unidade != "Todas":
            df_quad = df_quad[df_quad["Und."] == filtro_unidade]
        df_quad = df_quad.sort_values(["Departamento", "Nivel", "Nome"]).reset_index(drop=True)
        df_quad["Responsável Direto"] = df_quad["Responsável Direto"].fillna("").astype(str).str.strip()

        edited_quad = st.data_editor(
            df_quad,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(disabled=True, width="small"),
                "Nome": st.column_config.TextColumn(disabled=True),
                "Departamento": st.column_config.TextColumn(disabled=True),
                "Cargo": st.column_config.TextColumn(disabled=True),
                "Nivel": st.column_config.NumberColumn(format="%.1f", disabled=True, width="small"),
                "MP": st.column_config.NumberColumn(format="%.2f", disabled=True, width="small"),
                "U": st.column_config.TextColumn(disabled=True, width="small"),
                "Und.": st.column_config.TextColumn(disabled=True),
                "Gestor": st.column_config.TextColumn(disabled=True),
                "Responsável Direto": st.column_config.SelectboxColumn(
                    options=_opcoes_resp,
                    help="Analista ou coordenador responsável direto no organograma de reportes.",
                ),
            },
            key="editor_quadro",
        )

        if st.button("Salvar reportes", type="primary", key="btn_salvar_resp"):
            _alteracoes = []
            for idx in df_quad.index:
                old_val = str(df_quad.at[idx, "Responsável Direto"] or "").strip()
                new_val = str(edited_quad.at[idx, "Responsável Direto"] or "").strip()
                if old_val != new_val:
                    _alteracoes.append((int(df_quad.at[idx, "ID"]), new_val or None))
            if _alteracoes:
                for _cid, _resp in _alteracoes:
                    atualizar_responsavel_direto(_cid, _resp)
                st.success(f"{len(_alteracoes)} reporte(s) salvo(s). Confira na aba 'Visao por reportes'.")
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada.")

        st.caption(f"Total exibido: {len(df_quad)} colaboradores")
    else:
        st.info("Nenhum colaborador cadastrado.")

# ── Tab: Gestão de Equipe ─────────────────────────────────────────────────────
with tab_gestao:
    st.subheader("Gestao de equipe")
    st.caption("Registre entradas, desligamentos e consulte o histórico consolidado da equipe.")

    subtab_contrat, subtab_desl, subtab_hist = st.tabs(
        ["Contratacoes", "Desligamentos", "Historico"]
    )

    # ── Sub-aba: Contratações ──────────────────────────────────────────
    with subtab_contrat:
        st.subheader("Nova Contratacao")
        st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

        with st.form("form_contratacao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_novo = st.text_input("Nome completo")
                dept_sel = st.selectbox(
                    "Departamento",
                    options=[d["nome"] for d in departamentos],
                    key="gest_dept_contrat",
                )
                dept_id_sel = next((d["id"] for d in departamentos if d["nome"] == dept_sel), None)
                cargos_dept = listar_cargos(dept_id_sel)
                cargo_options = {c["nome"]: c["id"] for c in cargos_dept}
                cargo_nomes = list(cargo_options.keys())
                cargo_sel = st.selectbox("Cargo", options=cargo_nomes, disabled=not cargo_nomes)
                if not cargo_nomes:
                    st.info("Cadastre ao menos um cargo nesse departamento antes de registrar.")
            with col2:
                unidade = st.selectbox("Unidade", ["Novo Hamburgo", "Itajaí"])
                gestor = st.text_input("Gestor direto")
                data_entrada = st.date_input("Data de entrada", value=date.today())
                obs = st.text_area("Observacao (opcional)", height=68)

            if st.form_submit_button("Registrar contratacao", type="primary", disabled=not cargo_options):
                if nome_novo.strip() and cargo_sel:
                    novo_id = contratar(
                        nome=nome_novo.strip(),
                        cargo_id=cargo_options[cargo_sel],
                        departamento_id=dept_id_sel,
                        empresa=unidade,
                        cidade=unidade,
                        gestor_direto=gestor,
                        data_entrada=data_entrada,
                        observacao=obs,
                    )
                    st.success(f"**{nome_novo}** registrado(a) com sucesso! (ID: {novo_id})")
                    st.balloons()
                else:
                    st.warning("Preencha nome e cargo.")

    # ── Sub-aba: Desligamentos ─────────────────────────────────────────
    with subtab_desl:
        st.subheader("Registrar Desligamento")
        st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

        ativos_desl = listar_colaboradores(status="Ativo")
        if ativos_desl:
            nomes_ativos = {
                f"{c['nome']} ({c['cargo_nome']} — {c['departamento_nome']})": c["id"]
                for c in ativos_desl
            }
            with st.form("form_desligamento"):
                pessoa_sel = st.selectbox("Colaborador", options=list(nomes_ativos.keys()))
                data_saida = st.date_input("Data de saida", value=date.today())
                obs_saida = st.text_area("Motivo / Observacao (opcional)", height=68)
                col1_desl, col2_desl = st.columns([1, 3])
                with col1_desl:
                    confirmar = st.checkbox("Confirmo o desligamento")
                submitted_desl = st.form_submit_button("Registrar desligamento", type="primary")

                if submitted_desl:
                    if confirmar:
                        desligar(
                            colab_id=nomes_ativos[pessoa_sel],
                            data_saida=data_saida,
                            observacao=obs_saida,
                        )
                        nome_simples = pessoa_sel.split(" (")[0]
                        st.success(f"**{nome_simples}** desligado(a) com sucesso.")
                        st.rerun()
                    else:
                        st.warning("Marque a confirmacao para prosseguir.")
        else:
            st.info("Nenhum colaborador ativo encontrado.")

    # ── Sub-aba: Histórico ─────────────────────────────────────────────
    with subtab_hist:
        st.subheader("Log de Movimentacoes")
        historico = listar_historico()
        if historico:
            df_hist = pd.DataFrame(historico)
            datas = pd.to_datetime(df_hist["data"], errors="coerce")
            df_hist["data"] = datas.apply(
                lambda val: f"{MESES_PT_ORG[val.month]}/{val.year}" if pd.notna(val) else ""
            )
            df_hist = df_hist[["data", "tipo", "nome", "cargo", "observacao"]]
            df_hist.columns = ["Periodo", "Evento", "Nome", "Cargo", "Observacao"]

            def _estilo_evento(val):
                if val == "Entrada":
                    return "color: green; font-weight: bold"
                if val == "Saída":
                    return "color: red; font-weight: bold"
                return ""

            styled_hist = df_hist.style.map(_estilo_evento, subset=["Evento"])
            renderizar_dataframe(styled_hist, use_container_width=True, hide_index=True)
            st.caption(f"{len(df_hist)} registros")
        else:
            st.info("Nenhum registro no historico.")
