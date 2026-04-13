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

# Injeta dark mode CSS ANTES de qualquer conteúdo renderizar
# para evitar flash de tema claro na troca de página
if is_dark_mode():
    _aplicar_dark_mode()

seed_usuarios_iniciais()
restaurar_sessao()

if not obter_usuario_atual():
    renderizar_login()
    st.stop()

# Salva token no localStorage após login (evita race condition com st.rerun)
processar_pendencias()

pages = [
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Organograma.py", title="Organograma", icon="🗂️"),
    st.Page("pages/3_Manpower_e_Eficiencia.py", title="KPIs", icon="📊"),
    st.Page("pages/2_Controle_de_Pessoas.py", title="Controle de Pessoas", icon="👥"),
    st.Page("pages/5_Processos_360.py", title="Processos 360", icon="🚢"),
]

if usuario_admin():
    pages.append(st.Page("pages/4_Usuarios.py", title="Usuários", icon="🔐"))

renderizar_usuario_sidebar()

st.sidebar.toggle(
    "🌙 Dark Mode",
    key="dark_mode",
)

pg = st.navigation(pages)
pg.run()
