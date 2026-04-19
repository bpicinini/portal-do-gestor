import streamlit as st

from utils.auth import (
    obter_usuario_atual,
    processar_pendencias,
    renderizar_login,
    renderizar_usuario_sidebar,
    restaurar_sessao,
    seed_usuarios_iniciais,
    usuario_admin,
)
from utils.ui import is_dark_mode, _aplicar_dark_mode


st.set_page_config(
    page_title="Portal do Gestor - 3S Corporate",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

seed_usuarios_iniciais()
restaurar_sessao()

if not obter_usuario_atual():
    renderizar_login()
    st.stop()

# Salva token no localStorage após login (evita race condition com st.rerun)
processar_pendencias()

# Inicializa toggle antes de renderizar páginas para evitar 1º frame em tema errado
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

st.sidebar.toggle(
    ":material/dark_mode: Dark Mode",
    key="dark_mode",
)

# Injeta dark mode já com estado atualizado do toggle nesta execução
if is_dark_mode():
    _aplicar_dark_mode()

pages = [
    st.Page("home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/1_Organograma.py", title="Organograma", icon=":material/account_tree:"),
    st.Page("pages/3_Manpower_e_Eficiencia.py", title="KPIs", icon=":material/bar_chart:"),
    st.Page("pages/5_Processos_360.py", title="Visão Geral 360", icon=":material/local_shipping:"),
    st.Page("pages/6_Restituicoes.py", title="Restituições", icon=":material/currency_exchange:"),
    st.Page("pages/7_Processos_Judiciais.py", title="Intimações & Jurídico", icon=":material/gavel:"),
]

if usuario_admin():
    pages.append(st.Page("pages/4_Usuarios.py", title="Usuários", icon=":material/people:"))

renderizar_usuario_sidebar()

pg = st.navigation(pages)
pg.run()
