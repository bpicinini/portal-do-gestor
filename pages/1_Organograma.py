from html import escape

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.departamentos import (
    listar_cargos,
    listar_departamentos,
    salvar_cargo,
)
from utils.organograma import construir_estrutura_reportes
from utils.pessoas import atualizar_responsavel_direto, listar_colaboradores
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


garantir_autenticado()
aplicar_estilos_globais()
renderizar_cabecalho_pagina(
    "Organograma",
    "Estrutura da operacao com leitura por niveis e uma visao paralela por reportes diretos.",
    badge="Estrutura ativa",
    pills=[
        "Visao por departamento",
        "Visao por reportes imediatos",
        "Cadastro operacional",
    ],
)

departamentos = listar_departamentos()
deptos_map = {d["id"]: d["nome"] for d in departamentos}
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
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
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
    border-radius: 14px;
    padding: 11px 12px;
}
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
.report-source.seed {
    background: #e5f1dd;
    color: #58785b;
}
.report-source.definido {
    background: #d8edf6;
    color: #1a6080;
}
.report-source.fallback {
    background: #f4e7c5;
    color: #9a6d19;
}
.report-empty {
    color: #7a848d;
    font-size: 12px;
    padding: 8px 2px 2px;
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


def _card(css_class, nome, cargo, unidade, peso=None):
    peso_str = f" | MP {peso:.2f}" if peso is not None else ""
    linha_info = f"{unidade}{peso_str}" if unidade else peso_str[3:] if peso_str.startswith(" | ") else ""
    return (
        f'<div class="{css_class}">'
        f'<div class="nome">{escape(str(nome))}</div>'
        f'<div class="cargo">{escape(str(cargo))}</div>'
        f'<div class="info">{escape(linha_info)}</div>'
        f"</div>"
    )


def card_para_nivel(pessoa):
    nivel = _nivel(pessoa)
    nome = pessoa["nome"]
    cargo = pessoa["cargo_nome"]
    unidade = pessoa.get("unidade") or pessoa.get("empresa", "")
    peso = pessoa.get("peso_manpower")

    if nivel <= 1:
        return _card("card-gerencia", nome, cargo, unidade)
    if nivel <= 2.0:
        return _card("card-coordenador", nome, cargo, unidade)
    if nivel <= 2.5:
        return _card("card-supervisor", nome, cargo, unidade)
    return _card("card-op", nome, cargo, unidade, peso=peso)


def _card_reporte_analista(pessoa):
    meta = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    return (
        '<div class="report-head">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{escape(meta)}</div>'
        "</div>"
    )


def _card_reporte_subordinado(item):
    pessoa = item["pessoa"]
    origem = item["origem"]
    if origem == "Definido pelo coordenador":
        badge_class = "definido"
    elif origem == "Planilha-base":
        badge_class = "seed"
    else:
        badge_class = "fallback"
    meta = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    return (
        '<div class="report-child">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{escape(meta)}</div>'
        f'<div class="report-source {badge_class}">{escape(origem)}</div>'
        "</div>"
    )


_opcoes_filtro = ["Todos"] + [d["nome"] for d in departamentos]
filtro_dept = st.pills(
    "Departamento",
    options=_opcoes_filtro,
    default="Todos",
    key="filtro_org",
) or "Todos"

tab_niveis, tab_reportes, tab_quadro, tab_gestao = st.tabs(
    ["Visao por niveis", "Visao por reportes", "Quadro completo", "Gestao"]
)

with tab_niveis:
    st.subheader("Visao por niveis")

    gerencia_geral = [c for c in todos_ativos if _nivel(c) <= 1]
    if gerencia_geral:
        st.markdown('<div class="nivel-label">Gerencia</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(gerencia_geral), 3))
        for idx, pessoa in enumerate(gerencia_geral):
            with cols[idx % len(cols)]:
                st.markdown(card_para_nivel(pessoa), unsafe_allow_html=True)
        st.markdown('<div class="conector">↓</div>', unsafe_allow_html=True)

    for depto in departamentos:
        if filtro_dept != "Todos" and depto["nome"] != filtro_dept:
            continue

        dept_colabs = listar_colaboradores(status="Ativo", departamento_id=int(depto["id"]))
        dept_colabs = [c for c in dept_colabs if _nivel(c) > 1]
        if not dept_colabs:
            continue

        with st.expander(
            f"**{depto['nome']}** | {len(dept_colabs)} pessoas",
            expanded=(filtro_dept != "Todos"),
        ):
            niveis = {}
            for pessoa in dept_colabs:
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

with tab_reportes:
    st.subheader("Visao por reportes imediatos")
    st.caption(
        "Esta leitura usa a aba Estrutura Gabriel da planilha PROJETO MEGAZORD como semente inicial. "
        "Quando a planilha nao explicita o reporte direto, a distribuicao e feita provisoriamente entre analistas do mesmo setor."
    )

    gerencia_geral = [c for c in todos_ativos if _nivel(c) <= 1]
    if gerencia_geral:
        st.markdown('<div class="nivel-label">Gerencia geral</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(gerencia_geral), 3))
        for idx, pessoa in enumerate(gerencia_geral):
            with cols[idx % len(cols)]:
                st.markdown(card_para_nivel(pessoa), unsafe_allow_html=True)

    for bloco in estrutura_reportes:
        if filtro_dept != "Todos" and bloco["departamento"] != filtro_dept:
            continue
        dept_total = len(bloco["lideres"]) + sum(len(grupo["reportes"]) + 1 for grupo in bloco["grupos"])
        with st.expander(
            f"**{bloco['departamento']}** | {dept_total} pessoas na visao de reportes",
            expanded=(filtro_dept != "Todos"),
        ):
            if bloco["lideres"]:
                st.markdown('<div class="nivel-label">Lideranca do setor</div>', unsafe_allow_html=True)
                lideres_html = '<div class="report-leaders">'
                for pessoa in bloco["lideres"]:
                    lideres_html += card_para_nivel(pessoa)
                lideres_html += "</div>"
                st.markdown(lideres_html, unsafe_allow_html=True)

            if bloco["grupos"]:
                st.markdown('<div class="nivel-label">Analistas e reportes</div>', unsafe_allow_html=True)
                html = '<div class="report-grid">'
                for grupo in bloco["grupos"]:
                    html += '<div class="report-column">'
                    html += _card_reporte_analista(grupo["analista"])
                    if grupo["reportes"]:
                        html += '<div class="report-stack">'
                        for item in grupo["reportes"]:
                            html += _card_reporte_subordinado(item)
                        html += "</div>"
                    else:
                        html += '<div class="report-empty">Nenhum reporte alocado no momento.</div>'
                    html += "</div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Nao ha analistas cadastrados neste setor para montar a visao de reportes.")

    st.divider()
    st.markdown("#### Tabela de analistas e assistentes")
    st.caption(
        "Visao simplificada para os coordenadores ajustarem os reportes diretos. "
        "Linhas marcadas como 'Distribuicao provisoria' ainda precisam ser confirmadas."
    )

    rows_tab = []
    for bloco in estrutura_reportes:
        if filtro_dept != "Todos" and bloco["departamento"] != filtro_dept:
            continue
        dept = bloco["departamento"]
        for grupo in bloco["grupos"]:
            analista = grupo["analista"]
            if grupo["reportes"]:
                for item in grupo["reportes"]:
                    sub = item["pessoa"]
                    rows_tab.append(
                        {
                            "Departamento": dept,
                            "Analista": analista["nome"],
                            "Cargo Analista": analista["cargo_nome"],
                            "Assistente / Estagiario": sub["nome"],
                            "Cargo": sub["cargo_nome"],
                            "Origem": item["origem"],
                        }
                    )
            else:
                rows_tab.append(
                    {
                        "Departamento": dept,
                        "Analista": analista["nome"],
                        "Cargo Analista": analista["cargo_nome"],
                        "Assistente / Estagiario": "—",
                        "Cargo": "—",
                        "Origem": "—",
                    }
                )

    if rows_tab:
        df_tab = pd.DataFrame(rows_tab)

        def _colorir_origem(val):
            if val == "Definido pelo coordenador":
                return "background-color: #d8edf6; color: #1a6080;"
            if val == "Planilha-base":
                return "background-color: #e5f1dd; color: #3d6b40;"
            if val == "Distribuição provisória":
                return "background-color: #fef3dc; color: #8a5e10;"
            return ""

        st.dataframe(
            df_tab.style.applymap(_colorir_origem, subset=["Origem"]),
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
        st.info("Nenhum dado de reportes para exibir.")

with tab_quadro:
    st.subheader("Quadro completo")
    if todos_ativos:
        df_raw = pd.DataFrame(todos_ativos)

        # Garante coluna responsavel_direto mesmo em dados antigos
        if "responsavel_direto" not in df_raw.columns:
            df_raw["responsavel_direto"] = None

        # Opções de responsável: apenas analistas (nivel 3–6)
        _analistas = [p for p in todos_ativos if 3 <= float(p.get("cargo_nivel") or 99) < 7]
        _opcoes_resp = [""] + sorted({a["nome"] for a in _analistas})

        df_quad = df_raw[
            [
                "id",
                "nome",
                "departamento_nome",
                "cargo_nome",
                "cargo_nivel",
                "peso_manpower",
                "unidade",
                "gestor_direto",
                "responsavel_direto",
            ]
        ].copy()
        df_quad.columns = [
            "ID", "Nome", "Departamento", "Cargo", "Nivel",
            "MP", "Unidade", "Gestor", "Responsável Direto",
        ]

        if filtro_dept != "Todos":
            df_quad = df_quad[df_quad["Departamento"] == filtro_dept]

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
                "Unidade": st.column_config.TextColumn(disabled=True),
                "Gestor": st.column_config.TextColumn(disabled=True),
                "Responsável Direto": st.column_config.SelectboxColumn(
                    options=_opcoes_resp,
                    help="Analista responsável por este colaborador na visão de reportes imediatos.",
                ),
            },
            key="editor_quadro",
        )

        if st.button("Salvar reportes", type="primary", key="btn_salvar_reportes"):
            _alteracoes = []
            for idx in df_quad.index:
                old_val = str(df_quad.at[idx, "Responsável Direto"] or "").strip()
                new_val = str(edited_quad.at[idx, "Responsável Direto"] or "").strip()
                if old_val != new_val:
                    _alteracoes.append((int(df_quad.at[idx, "ID"]), new_val or None))
            if _alteracoes:
                for _cid, _resp in _alteracoes:
                    atualizar_responsavel_direto(_cid, _resp)
                st.success(f"{len(_alteracoes)} reporte(s) salvo(s). Acesse a aba 'Visao por reportes' para conferir.")
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada.")

        st.caption(f"Total exibido: {len(df_quad)} colaboradores ativos")
    else:
        st.info("Nenhum colaborador cadastrado.")

with tab_gestao:
    st.subheader("Gestao")
    tab_dept, tab_cargo = st.tabs(["Departamentos", "Cargos"])

    with tab_dept:
        if departamentos:
            df_dept = pd.DataFrame(departamentos)
            df_dept.columns = ["ID", "Nome"]
            st.dataframe(df_dept, use_container_width=True, hide_index=True)

    with tab_cargo:
        col1, col2 = st.columns([2, 1])
        with col1:
            cargos_todos = listar_cargos()
            if cargos_todos:
                df_cargos = pd.DataFrame(cargos_todos)
                df_cargos["departamento"] = df_cargos["departamento_id"].map(deptos_map)
                df_cargos = df_cargos[["id", "nome", "nivel", "peso_manpower", "departamento"]]
                df_cargos.columns = ["ID", "Cargo", "Nivel", "Peso MP", "Departamento"]
                st.dataframe(df_cargos, use_container_width=True, hide_index=True)

        with col2:
            with st.form("form_cargo", clear_on_submit=True):
                st.markdown("**Novo cargo**")
                nome_cargo = st.text_input("Nome do cargo")
                nivel_cargo = st.number_input(
                    "Nivel hierarquico",
                    min_value=0.5,
                    max_value=10.0,
                    step=0.5,
                    value=5.0,
                )
                peso_cargo = st.number_input(
                    "Peso MP (0 = nao conta)",
                    min_value=0.0,
                    max_value=5.0,
                    step=0.05,
                    value=1.0,
                )
                dept_options = {d["nome"]: d["id"] for d in departamentos}
                dept_sel = st.selectbox("Departamento", options=list(dept_options.keys()))
                if st.form_submit_button("Salvar"):
                    if nome_cargo.strip():
                        peso = peso_cargo if peso_cargo > 0 else None
                        salvar_cargo(nome_cargo.strip(), nivel_cargo, peso, dept_options[dept_sel])
                        st.success(f"Cargo '{nome_cargo}' salvo.")
                        st.rerun()
                    else:
                        st.warning("Informe o nome do cargo.")
