from datetime import datetime

import streamlit as st


def saudacao_periodo():
    hora = datetime.now().hour
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


def aplicar_estilos_globais():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #f6f2ea;
            --surface: #fffdf8;
            --surface-soft: #f3ede2;
            --line: #e3d8c5;
            --text: #223645;
            --muted: #6f7a84;
            --navy: #234055;
            --navy-soft: #36586f;
            --gold: #c79536;
            --gold-soft: #f2e2ba;
            --green: #5e8668;
            --green-soft: #e3f0de;
            --shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(199, 149, 54, 0.07), transparent 24%),
                linear-gradient(180deg, #f8f4ed 0%, var(--bg) 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 2rem !important;
        }

        [data-testid="stHeader"] {
            background: rgba(248, 244, 237, 0.8);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fcfaf5 0%, #f6f0e6 100%);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebarContent"] {
            padding-top: 0.8rem;
        }

        [data-testid="stSidebarNav"] {
            background: transparent;
            padding-top: 0.3rem;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 14px;
            margin: 0.18rem 0 0.28rem 0;
            padding: 0.62rem 0.85rem;
            color: var(--text);
            transition: all 0.18s ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: #efe6d6;
            color: var(--navy);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(135deg, #f4e8ca 0%, #f8f1df 100%);
            color: var(--navy);
            font-weight: 700;
            border: 1px solid #ead9ac;
            box-shadow: inset 4px 0 0 var(--gold);
        }

        [data-testid="stSidebarNav"] span {
            font-size: 0.95rem;
        }

        h1, h2, h3 {
            color: var(--navy);
            letter-spacing: -0.02em;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--navy);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            background: var(--surface-soft);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.45rem 0.95rem;
            color: var(--muted);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #f3e2b9 0%, #f8f0dd 100%);
            color: var(--navy) !important;
            border-color: #e8d39b !important;
        }

        .stButton button,
        .stDownloadButton button,
        .stFormSubmitButton button {
            border-radius: 14px;
            border: 1px solid #d4b164;
            background: linear-gradient(135deg, #d59a2b 0%, #bf7f16 100%);
            color: white;
            font-weight: 700;
            box-shadow: 0 10px 24px rgba(191, 127, 22, 0.18);
        }

        .stButton button:hover,
        .stDownloadButton button:hover,
        .stFormSubmitButton button:hover {
            border-color: #b77811;
            background: linear-gradient(135deg, #c98e23 0%, #a96b0f 100%);
            color: white;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stDateInput > div > div,
        .stSelectbox > div > div,
        .stTextArea textarea {
            background: var(--surface) !important;
            border-radius: 14px !important;
            border: 1px solid var(--line) !important;
        }

        .stRadio > div,
        div[data-testid="stExpander"] {
            background: rgba(255, 253, 248, 0.6);
            border-radius: 18px;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
        }

        .stAlert {
            border-radius: 16px;
            border: 1px solid var(--line);
        }

        .dashboard-shell {
            background: linear-gradient(135deg, rgba(255,253,248,0.96) 0%, rgba(243,237,226,0.96) 100%);
            border: 1px solid var(--line);
            border-radius: 26px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1.25rem;
            box-shadow: var(--shadow);
        }

        .dashboard-shell-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .dashboard-kicker {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .dashboard-title {
            color: var(--navy);
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.02;
            margin: 0;
        }

        .dashboard-desc {
            color: var(--muted);
            font-size: 0.98rem;
            margin-top: 0.45rem;
        }

        .dashboard-badge {
            background: linear-gradient(135deg, var(--green-soft) 0%, #eef7e8 100%);
            color: var(--green);
            border: 1px solid #cddfc8;
            border-radius: 999px;
            padding: 0.55rem 0.9rem;
            font-size: 0.84rem;
            font-weight: 800;
            white-space: nowrap;
        }

        .dashboard-meta {
            margin-top: 0.95rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
        }

        .dashboard-pill {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.42rem 0.75rem;
            color: var(--navy-soft);
            font-size: 0.84rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_cabecalho_pagina(titulo, descricao, badge=None, pills=None, kicker="Portal do Gestor"):
    badge_html = f'<div class="dashboard-badge">{badge}</div>' if badge else ""
    pills = pills or []
    pills_html = "".join(f'<div class="dashboard-pill">{pill}</div>' for pill in pills)
    st.markdown(
        f"""
        <div class="dashboard-shell">
            <div class="dashboard-shell-top">
                <div>
                    <div class="dashboard-kicker">{kicker}</div>
                    <h1 class="dashboard-title">{titulo}</h1>
                    <div class="dashboard-desc">{descricao}</div>
                </div>
                {badge_html}
            </div>
            <div class="dashboard-meta">{pills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
