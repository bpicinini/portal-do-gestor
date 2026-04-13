from html import escape

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.departamentos import listar_departamentos
from utils.organograma import construir_estrutura_reportes
from utils.pessoas import atualizar_responsavel_direto, listar_colaboradores
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


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
        radial-gradient(circle at top right, rgba(242, 212, 145, 0.28), transparent 28%),
        linear-gradient(135deg, #183142 0%, #234055 52%, #2a4a5f 100%);
    color: white;
    border-radius: 22px;
    padding: 18px 20px;
    margin: 4px 2px;
    min-height: 92px;
    border: 1px solid rgba(216, 165, 67, 0.42);
    border-left: 6px solid #d8a543;
    box-shadow: 0 20px 44px rgba(24, 49, 66, 0.26);
    position: relative;
    overflow: hidden;
}
.card-coordenador {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 100%),
        linear-gradient(135deg, #53707f 0%, #476271 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 4px solid #9eb5c1;
    box-shadow: 0 14px 32px rgba(35, 64, 85, 0.12);
}
.card-supervisor {
    background: linear-gradient(135deg, #c89a44 0%, #b47f27 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    box-shadow: 0 14px 35px rgba(180, 127, 39, 0.22);
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
    opacity: 0.85;
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
    opacity: 0.72;
    margin-top: 2px;
}
.card-op {
    background: #fffdf8;
    border: 1px solid #e3d8c5;
    border-left: 4px solid #e3d8c5;
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.card-op.nh {
    border-left: 4px solid #3b82f6;
}
.card-op.ita {
    border-left: 4px solid #16a34a;
}
.card-op .nome {
    font-weight: 700;
    font-size: 13px;
    color: #234055;
    line-height: 1.3;
}
.card-op .cargo {
    font-size: 11px;
    color: #65707a;
    margin-top: 2px;
}
.card-op .info {
    font-size: 11px;
    color: #87919a;
    margin-top: 1px;
}
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
    font-weight: 800;
    color: #234055;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 14px 0 6px 0;
    padding-left: 8px;
    border-left: 3px solid #c79536;
}
.conector {
    text-align: center;
    color: #c79536;
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
    background: #fffdf8;
    border: 1px solid #e3d8c5;
    border-radius: 20px;
    padding: 14px;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.report-head {
    background: linear-gradient(135deg, #31586c 0%, #234055 100%);
    color: white;
    border-radius: 16px;
    padding: 14px 16px;
}
.report-head .nome {
    font-size: 15px;
    font-weight: 800;
    line-height: 1.2;
}
.report-head .cargo {
    font-size: 12px;
    opacity: 0.9;
    margin-top: 4px;
}
.report-head .meta {
    font-size: 11px;
    opacity: 0.75;
    margin-top: 6px;
}
.report-stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
}
.report-child {
    background: #f6f1e7;
    border: 1px solid #eadfcd;
    border-left: 4px solid #e3d8c5;
    border-radius: 14px;
    padding: 11px 12px;
}
.report-child.nh { border-left: 4px solid #3b82f6; }
.report-child.ita { border-left: 4px solid #16a34a; }
.report-child .nome {
    color: #234055;
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
.report-source.fallback { background: #f4e7c5; color: #9a6d19; }
.report-empty {
    color: #7a848d;
    font-size: 12px;
    padding: 8px 2px 2px;
}
.filtro-label {
    font-size: 11px;
    font-weight: 800;
    color: #6f7a84;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
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
    return _card("card-op", nome, cargo, unidade, peso=peso)


def _card_reporte_analista(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    return (
        '<div class="report-head">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        "</div>"
    )


def _card_reporte_subordinado(item):
    pessoa = item["pessoa"]
    origem = item["origem"]
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    if origem == "Definido pelo coordenador":
        badge_class = "definido"
    elif origem == "Planilha-base":
        badge_class = "seed"
    else:
        badge_class = "fallback"
    return (
        f'<div class="report-child{extra}">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        f'<div class="report-source {badge_class}">{escape(origem)}</div>'
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

tab_niveis, tab_reportes, tab_quadro = st.tabs(
    ["Visao por niveis", "Visao por reportes", "Quadro completo"]
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
    st.caption(
        "Reportes definidos no Quadro completo prevalecem. "
        "Demais sao distribuidos provisoriamente por setor."
    )

    for bloco in estrutura_reportes:
        if filtro_dept != "Todos" and bloco["departamento"] != filtro_dept:
            continue

        ids_bloco = {p.get("id") for p in bloco["lideres"]}
        for grupo in bloco["grupos"]:
            ids_bloco.add(grupo["analista"].get("id"))
            for item in grupo["reportes"]:
                ids_bloco.add(item["pessoa"].get("id"))
        gerencia_extra_rep = [g for g in gerencia_geral if g.get("id") not in ids_bloco]

        # Aplica filtro de unidade nos grupos
        grupos_filtrados = bloco["grupos"]
        if filtro_unidade != "Todas":
            grupos_filtrados = [
                {
                    "analista": g["analista"],
                    "reportes": [
                        r for r in g["reportes"]
                        if str(r["pessoa"].get("unidade") or "") == filtro_unidade
                    ],
                }
                for g in bloco["grupos"]
                if str(g["analista"].get("unidade") or "") == filtro_unidade
                or any(str(r["pessoa"].get("unidade") or "") == filtro_unidade for r in g["reportes"])
            ]

        dept_total = (
            len(gerencia_extra_rep)
            + len(bloco["lideres"])
            + sum(len(g["reportes"]) + 1 for g in grupos_filtrados)
        )

        with st.expander(
            f"**{bloco['departamento']}** | {dept_total} pessoas",
            expanded=(filtro_dept != "Todos"),
        ):
            all_lideres = gerencia_extra_rep + bloco["lideres"]
            if all_lideres:
                st.markdown('<div class="nivel-label">Lideranca do setor</div>', unsafe_allow_html=True)
                lideres_html = '<div class="report-leaders">'
                for pessoa in all_lideres:
                    lideres_html += card_para_nivel(pessoa)
                lideres_html += "</div>"
                st.markdown(lideres_html, unsafe_allow_html=True)

            if grupos_filtrados:
                st.markdown('<div class="nivel-label">Analistas e reportes</div>', unsafe_allow_html=True)
                html = '<div class="report-grid">'
                for grupo in grupos_filtrados:
                    html += '<div class="report-column">'
                    html += _card_reporte_analista(grupo["analista"])
                    if grupo["reportes"]:
                        html += '<div class="report-stack">'
                        for item in grupo["reportes"]:
                            html += _card_reporte_subordinado(item)
                        html += "</div>"
                    else:
                        html += '<div class="report-empty">Nenhum reporte alocado.</div>'
                    html += "</div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Nao ha analistas para exibir com os filtros atuais.")

    st.divider()
    st.markdown("#### Tabela de analistas e assistentes")
    st.caption("Use o botao 'Salvar reportes' no Quadro completo para definir os reportes.")

    rows_tab = []
    for bloco in estrutura_reportes:
        if filtro_dept != "Todos" and bloco["departamento"] != filtro_dept:
            continue
        dept = bloco["departamento"]
        for grupo in bloco["grupos"]:
            analista = grupo["analista"]
            unidade_a = str(analista.get("unidade") or "")
            if grupo["reportes"]:
                for item in grupo["reportes"]:
                    sub = item["pessoa"]
                    unidade_s = str(sub.get("unidade") or "")
                    if filtro_unidade != "Todas" and unidade_s != filtro_unidade:
                        continue
                    rows_tab.append({
                        "Departamento": dept,
                        "Analista": analista["nome"],
                        "Unidade Analista": unidade_a,
                        "Assistente / Estagiario": sub["nome"],
                        "Cargo": sub["cargo_nome"],
                        "Unidade": unidade_s,
                        "Origem": item["origem"],
                    })
            else:
                if filtro_unidade != "Todas" and unidade_a != filtro_unidade:
                    continue
                rows_tab.append({
                    "Departamento": dept,
                    "Analista": analista["nome"],
                    "Unidade Analista": unidade_a,
                    "Assistente / Estagiario": "—",
                    "Cargo": "—",
                    "Unidade": "—",
                    "Origem": "—",
                })

    if rows_tab:
        df_tab = pd.DataFrame(rows_tab)

        def _style_cell(val):
            if val == "Novo Hamburgo":
                return "background-color: #dbeafe; color: #1e40af; font-weight: 700;"
            if val == "Itajaí":
                return "background-color: #dcfce7; color: #166534; font-weight: 700;"
            if val == "Definido pelo coordenador":
                return "background-color: #d8edf6; color: #1a6080; font-weight: 700;"
            if val == "Planilha-base":
                return "background-color: #e5f1dd; color: #3d6b40; font-weight: 700;"
            if val == "Distribuição provisória":
                return "background-color: #fef3dc; color: #8a5e10; font-weight: 700;"
            return ""

        st.dataframe(
            df_tab.style.map(_style_cell, subset=["Unidade Analista", "Unidade", "Origem"]),
            use_container_width=True,
            hide_index=True,
        )
        csv_bytes = df_tab.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="Baixar tabela (.csv)",
            data=csv_bytes,
            file_name="reportes_organograma.csv",
            mime="text/csv",
        )
    else:
        st.info("Nenhum dado para exibir com os filtros atuais.")

# ── Tab: Quadro completo ─────────────────────────────────────────────────────
with tab_quadro:
    st.subheader("Quadro completo")
    if todos_ativos:
        df_raw = pd.DataFrame(todos_ativos)

        if "responsavel_direto" not in df_raw.columns:
            df_raw["responsavel_direto"] = None

        _analistas = [p for p in todos_ativos if 3 <= float(p.get("cargo_nivel") or 99) < 7]
        _opcoes_resp = [""] + sorted({a["nome"] for a in _analistas})

        df_quad = df_raw[[
            "id", "nome", "departamento_nome", "cargo_nome", "cargo_nivel",
            "peso_manpower", "unidade", "gestor_direto", "responsavel_direto",
        ]].copy()
        df_quad.columns = [
            "ID", "Nome", "Departamento", "Cargo", "Nivel",
            "MP", "Unidade", "Gestor", "Responsável Direto",
        ]

        if filtro_dept != "Todos":
            df_quad = df_quad[df_quad["Departamento"] == filtro_dept]
        if filtro_unidade != "Todas":
            df_quad = df_quad[df_quad["Unidade"] == filtro_unidade]
        df_quad = df_quad.sort_values(["Departamento", "Nivel", "Nome"]).reset_index(drop=True)
        df_quad["Responsável Direto"] = df_quad["Responsável Direto"].fillna("").astype(str).str.strip()

        def _style_unidade(val):
            if val == "Novo Hamburgo":
                return "background-color: #dbeafe; color: #1e40af; font-weight: 700;"
            if val == "Itajaí":
                return "background-color: #dcfce7; color: #166534; font-weight: 700;"
            return ""

        st.dataframe(
            df_quad.style.map(_style_unidade, subset=["Unidade"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(width="small"),
                "Nivel": st.column_config.NumberColumn(format="%.1f", width="small"),
                "MP": st.column_config.NumberColumn(format="%.2f", width="small"),
            },
        )

        st.markdown("**Atribuir Responsável Direto**")
        st.caption("Selecione o colaborador e o analista responsável, depois clique em Salvar.")

        _nomes_quad = ["—"] + list(df_quad["Nome"])
        _col_sel, _col_resp, _col_btn = st.columns([2, 2, 1])
        with _col_sel:
            _colab_sel = st.selectbox("Colaborador", _nomes_quad, key="sel_colab_resp")
        with _col_resp:
            _resp_sel = st.selectbox("Responsável Direto", _opcoes_resp, key="sel_resp")
        with _col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Salvar", type="primary", key="btn_salvar_resp"):
                if _colab_sel != "—":
                    _row = df_quad[df_quad["Nome"] == _colab_sel]
                    if not _row.empty:
                        atualizar_responsavel_direto(int(_row.iloc[0]["ID"]), _resp_sel or None)
                        st.success(f"Reporte de {_colab_sel} salvo.")
                        st.rerun()
                else:
                    st.warning("Selecione um colaborador.")

        st.caption(f"Total exibido: {len(df_quad)} colaboradores")
    else:
        st.info("Nenhum colaborador cadastrado.")
