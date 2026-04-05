import streamlit as st
from streamlit_cookies_controller import CookieController

from utils.auth import (
    _COOKIE_CTRL_KEY,
    obter_usuario_atual,
    renderizar_login,
    renderizar_usuario_sidebar,
    restaurar_sessao_do_cookie,
    seed_usuarios_iniciais,
    usuario_admin,
)


st.set_page_config(
    page_title="Portal do Gestor - 3S Corporate",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Instancia o controller de cookies antes de qualquer lógica de auth.
st.session_state[_COOKIE_CTRL_KEY] = CookieController(key="portal_cookies")

seed_usuarios_iniciais()
restaurar_sessao_do_cookie()

if not obter_usuario_atual():
    renderizar_login()
    st.stop()

pages = [
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Organograma.py", title="Organograma", icon="🗂️"),
    st.Page("pages/3_Manpower_e_Eficiencia.py", title="KPIs", icon="📊"),
    st.Page("pages/2_Controle_de_Pessoas.py", title="Controle de Pessoas", icon="👥"),
]

if usuario_admin():
    pages.append(st.Page("pages/4_Usuarios.py", title="Usuários", icon="🔐"))

renderizar_usuario_sidebar()

pg = st.navigation(pages)
pg.run()
