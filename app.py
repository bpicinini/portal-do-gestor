import streamlit as st

st.set_page_config(
    page_title="Portal do Gestor - 3S Corporate",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Organograma.py", title="Organograma", icon="🗂️"),
    st.Page("pages/3_Manpower_e_Eficiencia.py", title="KPIs", icon="📊"),
    st.Page("pages/2_Controle_de_Pessoas.py", title="Controle de Pessoas", icon="👥"),
])

pg.run()
