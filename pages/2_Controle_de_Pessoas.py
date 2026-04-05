import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils.departamentos import listar_departamentos, listar_cargos
from utils.pessoas import listar_colaboradores, contratar, desligar, atualizar_colaborador, listar_historico
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina

aplicar_estilos_globais()
renderizar_cabecalho_pagina(
    "Controle de Pessoas",
    "Entradas, saídas e histórico operacional com foco em atualização rápida do quadro.",
    badge="Fluxo de equipe",
)

departamentos = listar_departamentos()
deptos_map = {d["id"]: d["nome"] for d in departamentos}
MESES_PT = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button[kind="secondary"] {
        background: #fffdf8;
        color: #36586f;
        border: 1px solid #e3d8c5;
        box-shadow: none;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background: #f4ecde;
        color: #234055;
        border-color: #d6c3a6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "controle_pessoas_secao" not in st.session_state:
    st.session_state.controle_pessoas_secao = "Colaboradores"


def abrir_secao(nome):
    st.session_state.controle_pessoas_secao = nome


col_nav_1, col_nav_2, col_nav_3, col_nav_4 = st.columns(4)
with col_nav_1:
    st.button(
        "Colaboradores",
        type="primary" if st.session_state.controle_pessoas_secao == "Colaboradores" else "secondary",
        use_container_width=True,
        on_click=abrir_secao,
        args=("Colaboradores",),
    )
with col_nav_2:
    st.button(
        "Contratações",
        type="primary" if st.session_state.controle_pessoas_secao == "Registrar Entrada" else "secondary",
        use_container_width=True,
        on_click=abrir_secao,
        args=("Registrar Entrada",),
    )
with col_nav_3:
    st.button(
        "Desligamentos",
        type="primary" if st.session_state.controle_pessoas_secao == "Registrar Saída" else "secondary",
        use_container_width=True,
        on_click=abrir_secao,
        args=("Registrar Saída",),
    )
with col_nav_4:
    st.button(
        "Histórico consolidado",
        type="primary" if st.session_state.controle_pessoas_secao == "Histórico" else "secondary",
        use_container_width=True,
        on_click=abrir_secao,
        args=("Histórico",),
    )

secao_atual = st.session_state.controle_pessoas_secao

# === SIDEBAR FILTROS ===
filtro_status = "Todos"
filtro_dept = "Todos"
filtro_nome = ""
with st.sidebar:
    if secao_atual == "Colaboradores":
        st.subheader("Filtros")
        filtro_status = st.radio("Status", ["Todos", "Ativo", "Inativo"])
        dept_options = ["Todos"] + [d["nome"] for d in departamentos]
        filtro_dept = st.selectbox("Departamento", dept_options)
        filtro_nome = st.text_input("Buscar por nome")
    else:
        st.subheader("Navegação")
        st.caption(f"Seção atual: **{secao_atual}**")


# --- TAB COLABORADORES ---
if secao_atual == "Colaboradores":
    status_filter = None if filtro_status == "Todos" else filtro_status
    dept_filter = None
    if filtro_dept != "Todos":
        dept_filter = next((d["id"] for d in departamentos if d["nome"] == filtro_dept), None)

    colaboradores = listar_colaboradores(status=status_filter, departamento_id=dept_filter)

    if filtro_nome:
        colaboradores = [c for c in colaboradores if filtro_nome.lower() in c["nome"].lower()]

    if colaboradores:
        df = pd.DataFrame(colaboradores)
        df = df[["id", "nome", "departamento_nome", "cargo_nome", "peso_manpower",
                "empresa", "gestor_direto", "data_entrada", "data_saida", "status"]]
        df.columns = ["ID", "Nome", "Departamento", "Cargo", "MP", "Unidade",
                      "Gestor", "Entrada", "Saída", "Status"]

        # Formatar datas sem horário
        for col_data in ["Entrada", "Saída"]:
            df[col_data] = pd.to_datetime(df[col_data], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")

        # Formatar MP em BR
        df["MP"] = df["MP"].apply(
            lambda v: f"{v:.2f}".replace(".", ",") if v is not None and str(v) not in ("", "None") and not (isinstance(v, float) and __import__("math").isnan(v)) else ""
        )

        def estilo_status(val):
            if val == "Ativo":
                return "color: green; font-weight: bold"
            elif val == "Inativo":
                return "color: gray; font-weight: bold"
            return ""

        styled = df.style.map(estilo_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} colaboradores encontrados")
    else:
        st.info("Nenhum colaborador encontrado com os filtros aplicados.")

# --- TAB REGISTRAR ENTRADA ---
if secao_atual == "Registrar Entrada":
    st.subheader("Nova Contratação")
    st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

    with st.form("form_contratacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome_novo = st.text_input("Nome completo")
            dept_sel = st.selectbox("Departamento", options=[d["nome"] for d in departamentos], key="dept_contrat")
            dept_id_sel = next((d["id"] for d in departamentos if d["nome"] == dept_sel), None)

            cargos_dept = listar_cargos(dept_id_sel)
            cargo_options = {c["nome"]: c["id"] for c in cargos_dept}
            cargo_nomes = list(cargo_options.keys())
            cargo_sel = st.selectbox("Cargo", options=cargo_nomes, disabled=not cargo_nomes)
            if not cargo_nomes:
                st.info("Cadastre ao menos um cargo nesse departamento antes de registrar uma contratação.")

        with col2:
            unidade = st.selectbox("Unidade", ["Novo Hamburgo", "Itajaí"])
            gestor = st.text_input("Gestor direto")
            data_entrada = st.date_input("Data de entrada", value=date.today())
            obs = st.text_area("Observação (opcional)", height=68)

        if st.form_submit_button("Registrar contratação", type="primary", disabled=not cargo_options):
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

# --- TAB REGISTRAR SAÍDA ---
if secao_atual == "Registrar Saída":
    st.subheader("Registrar Desligamento")
    st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

    ativos = listar_colaboradores(status="Ativo")
    if ativos:
        nomes_ativos = {f"{c['nome']} ({c['cargo_nome']} — {c['departamento_nome']})": c["id"] for c in ativos}

        with st.form("form_desligamento"):
            pessoa_sel = st.selectbox("Colaborador", options=list(nomes_ativos.keys()))
            data_saida = st.date_input("Data de saída", value=date.today())
            obs_saida = st.text_area("Motivo / Observação (opcional)", height=68)

            col1, col2 = st.columns([1, 3])
            with col1:
                confirmar = st.checkbox("Confirmo o desligamento")
            submitted = st.form_submit_button("Registrar desligamento", type="primary")

            if submitted:
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
                    st.warning("Marque a confirmação para prosseguir.")
    else:
        st.info("Nenhum colaborador ativo encontrado.")

# --- TAB HISTÓRICO ---
if secao_atual == "Histórico":
    st.subheader("Log de Movimentações")

    historico = listar_historico()
    if historico:
        df_hist = pd.DataFrame(historico)
        datas = pd.to_datetime(df_hist["data"], errors="coerce")
        df_hist["data"] = datas.apply(
            lambda val: f"{MESES_PT[val.month]}/{val.year}" if pd.notna(val) else ""
        )
        df_hist = df_hist[["data", "tipo", "nome", "cargo", "observacao"]]
        df_hist.columns = ["Período", "Evento", "Nome", "Cargo", "Observação"]

        def estilo_evento(val):
            if val == "Entrada":
                return "color: green; font-weight: bold"
            elif val == "Saída":
                return "color: red; font-weight: bold"
            return ""

        styled = df_hist.style.map(estilo_evento, subset=["Evento"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_hist)} registros")
    else:
        st.info("Nenhum registro no histórico.")
