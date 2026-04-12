from datetime import datetime

import streamlit as st


def saudacao_periodo():
    hora = datetime.now().hour
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


def is_dark_mode():
    return st.session_state.get("dark_mode", False)


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

        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"] {
            background: transparent;
            padding-top: 0.3rem;
        }

        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNavItems"] a,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"],
        [data-testid="stSidebar"] li a {
            border-radius: 14px;
            margin: 0.18rem 0 0.28rem 0;
            padding: 0.62rem 0.85rem;
            color: var(--text) !important;
            transition: all 0.18s ease;
            text-decoration: none !important;
        }

        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNavItems"] a span,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span,
        [data-testid="stSidebar"] li a span {
            color: var(--text) !important;
        }

        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNavItems"] a:hover,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover,
        [data-testid="stSidebar"] li a:hover {
            background: #efe6d6;
            color: var(--navy) !important;
        }

        [data-testid="stSidebarNav"] a:hover span,
        [data-testid="stSidebarNavItems"] a:hover span,
        [data-testid="stSidebar"] li a:hover span {
            color: var(--navy) !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] {
            background: linear-gradient(135deg, #f4e8ca 0%, #f8f1df 100%);
            color: var(--navy) !important;
            font-weight: 700;
            border: 1px solid #ead9ac;
            box-shadow: inset 4px 0 0 var(--gold);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNavItems"] a[aria-current="page"] span,
        [data-testid="stSidebar"] li a[aria-current="page"] span {
            color: var(--navy) !important;
        }

        [data-testid="stSidebarNav"] span,
        [data-testid="stSidebarNavItems"] span {
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

        /* ── Responsividade mobile ── */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.6rem !important;
                padding-right: 0.6rem !important;
                padding-top: 0.75rem !important;
            }

            .dashboard-shell {
                padding: 0.85rem 1rem;
                border-radius: 18px;
                margin-bottom: 1rem;
            }

            .dashboard-shell-top {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }

            .dashboard-badge {
                width: 100%;
                text-align: center;
                box-sizing: border-box;
            }

            .dashboard-title {
                font-size: 1.45rem;
            }

            .dashboard-desc {
                font-size: 0.9rem;
            }

            .dashboard-meta {
                gap: 0.5rem;
            }

            .dashboard-pill {
                font-size: 0.78rem;
                padding: 0.35rem 0.6rem;
            }

            div[data-testid="stMetric"] {
                padding: 0.75rem 0.85rem;
                border-radius: 16px;
            }

            /* tabs com scroll horizontal */
            .stTabs [data-baseweb="tab-list"] {
                overflow-x: auto;
                flex-wrap: nowrap;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                padding-bottom: 2px;
            }

            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                display: none;
            }

            .stTabs [data-baseweb="tab"] {
                white-space: nowrap;
                flex-shrink: 0;
                padding: 0.4rem 0.75rem;
                font-size: 0.82rem;
            }

            /* sidebar nav — alvos maiores no touch */
            [data-testid="stSidebarNav"] a {
                padding: 0.75rem 0.85rem;
                margin: 0.22rem 0 0.32rem 0;
            }

            [data-testid="stSidebarNav"] span {
                font-size: 1rem;
            }

            /* botões mais fáceis de tocar */
            .stButton button,
            .stFormSubmitButton button {
                min-height: 44px;
            }

            /* formulários sem overflow */
            .stTextInput > div > div,
            .stSelectbox > div > div,
            .stDateInput > div > div {
                font-size: 1rem !important;
            }
        }

        @media (max-width: 480px) {
            .dashboard-title {
                font-size: 1.25rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if is_dark_mode():
        _aplicar_dark_mode()


def _aplicar_dark_mode():
    st.markdown(
        """
        <style>
        /* ══════════════════════════════════════════════════════════════════
           DARK MODE — override completo
           ══════════════════════════════════════════════════════════════════ */

        :root {
            --bg: #0d1117;
            --surface: #161b22;
            --surface-soft: #1c2333;
            --line: #30363d;
            --text: #d4dae2;
            --muted: #8b949e;
            --navy: #c9d6e0;
            --navy-soft: #8faabb;
            --gold: #e0a83d;
            --gold-soft: #2a2210;
            --green: #7aad86;
            --green-soft: #1a2a1e;
            --shadow: 0 14px 35px rgba(0, 0, 0, 0.35);
        }

        /* ── Kill all backdrop-filter (light theme bleeds through) ── */
        [class*="hm-"],
        .dashboard-shell,
        .dashboard-badge,
        .dashboard-pill {
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }

        /* ── NUCLEAR: force light text everywhere ── */
        .stApp,
        .stApp *,
        .stApp p,
        .stApp span,
        .stApp div,
        .stApp label,
        .stApp li,
        .stApp td,
        .stApp th {
            color: var(--text) !important;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(224, 168, 61, 0.04), transparent 24%),
                linear-gradient(180deg, #0d1117 0%, #0d1117 100%) !important;
        }

        /* ── Sidebar — fundo e TODOS os textos internos ── */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #11161d 0%, #0d1117 100%) !important;
            border-right: 1px solid var(--line) !important;
        }

        [data-testid="stSidebarContent"] {
            background: transparent !important;
        }

        /* Sidebar nav links — dark mode */
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] a *,
        [data-testid="stSidebarNavItems"] a,
        [data-testid="stSidebarNavItems"] a *,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] *,
        [data-testid="stSidebar"] li a,
        [data-testid="stSidebar"] li a * {
            color: #e0e6ed !important;
            text-decoration: none !important;
        }

        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] a:hover *,
        [data-testid="stSidebarNavItems"] a:hover,
        [data-testid="stSidebarNavItems"] a:hover *,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover *,
        [data-testid="stSidebar"] li a:hover,
        [data-testid="stSidebar"] li a:hover * {
            background: rgba(255, 255, 255, 0.06) !important;
            color: #fff !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] *,
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"] *,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] *,
        [data-testid="stSidebar"] li a[aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] * {
            background: linear-gradient(135deg, rgba(224, 168, 61, 0.12) 0%, rgba(224, 168, 61, 0.06) 100%) !important;
            color: var(--gold) !important;
            border-color: rgba(224, 168, 61, 0.25) !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] {
            border: 1px solid rgba(224, 168, 61, 0.25) !important;
            box-shadow: inset 4px 0 0 var(--gold) !important;
        }

        /* Sidebar collapse button */
        [data-testid="stSidebar"] button,
        [data-testid="stSidebar"] button *,
        [data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] * {
            color: var(--muted) !important;
        }

        /* Sidebar Sair button */
        [data-testid="stSidebar"] .stButton button {
            background: rgba(255, 255, 255, 0.06) !important;
            border-color: var(--line) !important;
            color: var(--text) !important;
        }
        [data-testid="stSidebar"] .stButton button *,
        [data-testid="stSidebar"] .stButton button p {
            color: var(--text) !important;
        }

        /* Auth sidebar card (inline styles) */
        [data-testid="stSidebar"] [style*="background: linear-gradient(135deg, rgba(255,253,248"] {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.95) 0%, rgba(28, 35, 51, 0.95) 100%) !important;
            border-color: var(--line) !important;
        }
        [data-testid="stSidebar"] [style*="color:#6f7a84"],
        [data-testid="stSidebar"] [style*="color: #6f7a84"] {
            color: var(--muted) !important;
        }
        [data-testid="stSidebar"] [style*="color:#234055"],
        [data-testid="stSidebar"] [style*="color: #234055"] {
            color: var(--navy) !important;
        }
        [data-testid="stSidebar"] [style*="background:#eef5f0"],
        [data-testid="stSidebar"] [style*="background: #eef5f0"] {
            background: rgba(122, 173, 134, 0.12) !important;
            border-color: rgba(122, 173, 134, 0.2) !important;
        }
        [data-testid="stSidebar"] [style*="color:#36586f"],
        [data-testid="stSidebar"] [style*="color: #36586f"] {
            color: var(--navy-soft) !important;
        }

        /* Toggle label */
        [data-testid="stSidebar"] .stToggle label,
        [data-testid="stSidebar"] .stToggle label *,
        [data-testid="stSidebar"] .stToggle p,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] * {
            color: var(--text) !important;
        }

        /* ── Header ── */
        [data-testid="stHeader"] {
            background: rgba(13, 17, 23, 0.85) !important;
            backdrop-filter: blur(12px);
        }
        [data-testid="stHeader"] *,
        [data-testid="stHeader"] button {
            color: var(--text) !important;
        }

        /* ── Headings ── */
        h1, h2, h3, h4, h5, h6 {
            color: var(--navy) !important;
        }

        /* ── Streamlit native widgets ── */
        div[data-testid="stMetric"] {
            background: var(--surface) !important;
            border-color: var(--line) !important;
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] * { color: var(--muted) !important; }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * { color: var(--navy) !important; }

        .stTabs [data-baseweb="tab"] {
            background: var(--surface-soft) !important;
            border-color: var(--line) !important;
            color: var(--muted) !important;
        }
        .stTabs [data-baseweb="tab"] * { color: inherit !important; }
        .stTabs [aria-selected="true"],
        .stTabs [aria-selected="true"] * {
            background: linear-gradient(135deg, rgba(224, 168, 61, 0.15) 0%, rgba(224, 168, 61, 0.08) 100%) !important;
            color: var(--gold) !important;
            border-color: rgba(224, 168, 61, 0.3) !important;
        }

        .stButton button,
        .stDownloadButton button,
        .stFormSubmitButton button {
            background: linear-gradient(135deg, #c98e23 0%, #a96b0f 100%) !important;
            color: #fff !important;
        }
        .stButton button *,
        .stDownloadButton button *,
        .stFormSubmitButton button * {
            color: #fff !important;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stDateInput > div > div,
        .stSelectbox > div > div,
        .stTextArea textarea {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            color: var(--text) !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            color: var(--text) !important;
        }
        .stSelectbox [data-baseweb="select"] *,
        .stDateInput [data-baseweb] * {
            color: var(--text) !important;
        }

        /* Dropdowns / popover */
        [data-baseweb="popover"],
        [data-baseweb="popover"] *,
        [data-baseweb="menu"],
        [data-baseweb="menu"] * {
            background: var(--surface) !important;
            color: var(--text) !important;
        }
        [data-baseweb="menu"] li:hover {
            background: var(--surface-soft) !important;
        }

        .stRadio > div,
        div[data-testid="stExpander"] {
            background: rgba(22, 27, 34, 0.6) !important;
        }
        div[data-testid="stExpander"] {
            border-color: var(--line) !important;
        }
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
            color: var(--text) !important;
        }

        .stAlert { border-color: var(--line) !important; }

        /* st.dataframe */
        [data-testid="stDataFrame"],
        .stDataFrame { color: var(--text) !important; }

        /* st.caption, markdown */
        .stMarkdown p, .stCaption, [data-testid="stCaption"] {
            color: var(--text) !important;
        }

        /* st.page_link */
        [data-testid="stPageLink"],
        [data-testid="stPageLink"] a,
        [data-testid="stPageLink-NavLink"],
        [data-testid="stPageLink-NavLink"] * {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            color: var(--gold) !important;
        }

        /* st.subheader */
        [data-testid="stSubheader"],
        [data-testid="stSubheader"] * {
            color: var(--navy) !important;
        }

        /* st.info, st.success, st.warning, st.error */
        [data-testid="stNotification"],
        .stAlert div {
            color: var(--text) !important;
        }

        /* st.divider */
        [data-testid="stHorizontalRule"] hr,
        hr {
            border-color: var(--line) !important;
        }

        /* ── Dashboard shell (cabeçalhos de página) ── */
        .dashboard-shell {
            background: linear-gradient(135deg, #161b22 0%, #1c2333 100%) !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .dashboard-kicker { color: var(--muted) !important; }
        .dashboard-title  { color: var(--navy) !important; }
        .dashboard-desc   { color: var(--muted) !important; }
        .dashboard-badge {
            background: linear-gradient(135deg, var(--green-soft) 0%, rgba(26, 42, 30, 0.8) 100%) !important;
            color: var(--green) !important;
            border-color: rgba(122, 173, 134, 0.25) !important;
        }
        .dashboard-pill {
            background: rgba(255, 255, 255, 0.06) !important;
            border-color: var(--line) !important;
            color: var(--navy-soft) !important;
        }

        /* ══ HOME — Hero / KPIs / Pipeline / Cards ══ */
        .hm-banner {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .hm-banner-title { color: var(--navy) !important; }
        .hm-banner-sub   { color: var(--muted) !important; }
        .hm-banner-date  {
            background: #1c2333 !important;
            border-color: var(--line) !important;
            color: var(--navy) !important;
        }
        .hm-kpi {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .hm-kpi:hover {
            background: #1c2333 !important;
            border-color: rgba(224, 168, 61, 0.4) !important;
        }
        .hm-kpi-label { color: var(--muted) !important; }
        .hm-kpi-value { color: var(--navy) !important; }
        .hm-kpi-sub   { color: #6e7a86 !important; }
        .hm-kpi-value.green { color: var(--green) !important; }
        .hm-kpi-value.amber { color: var(--gold) !important; }

        .hm-pipeline {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .hm-pipeline:hover { background: #1c2333 !important; }
        .hm-pipeline-header { color: var(--navy) !important; }
        .hm-pipeline-header span { color: var(--gold) !important; }
        .hm-pipeline-leg-item { color: var(--muted) !important; }

        .hm-sec {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .hm-sec:hover {
            background: #1c2333 !important;
            border-color: rgba(224, 168, 61, 0.4) !important;
        }
        .hm-sec-title { color: var(--navy) !important; }
        .hm-sec-desc  { color: var(--muted) !important; }
        .hm-sec-metric {
            background: #1c2333 !important;
            border-color: var(--line) !important;
        }
        .hm-sec-metric-label { color: var(--muted) !important; }
        .hm-sec-metric-val   { color: var(--navy) !important; }
        .hm-sec-metric-val.green { color: var(--green) !important; }
        .hm-sec-metric-val.amber { color: var(--gold) !important; }
        .hm-section-label { color: var(--muted) !important; }

        .hm-alert-badge.critical {
            background: rgba(181, 66, 58, 0.18) !important;
            border-color: rgba(181, 66, 58, 0.3) !important;
            color: #e87c75 !important;
        }
        .hm-alert-badge.warning {
            background: rgba(224, 168, 61, 0.15) !important;
            border-color: rgba(224, 168, 61, 0.25) !important;
            color: var(--gold) !important;
        }
        .hm-alert-badge.info {
            background: rgba(139, 148, 158, 0.12) !important;
            color: var(--muted) !important;
            border-color: rgba(139, 148, 158, 0.2) !important;
        }

        .hm-hier-legend .hm-hier-leg-item { color: var(--muted) !important; }
        .hm-hier-seg { color: #fff !important; }

        .hm-dept-card {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
            border-top-color: rgba(224, 168, 61, 0.5) !important;
        }
        .hm-dept-card:hover {
            background: #1c2333 !important;
            border-color: rgba(224, 168, 61, 0.4) !important;
        }
        .hm-dept-card-name     { color: var(--navy) !important; }
        .hm-dept-card-num-val  { color: var(--navy) !important; }
        .hm-dept-card-num-label { color: var(--muted) !important; }
        .hm-dept-card-bar-bg   { background: rgba(255, 255, 255, 0.06) !important; }
        .hm-dept-card-bar-fill { background: rgba(74, 138, 181, 0.6) !important; }
        .hm-dept-card-people   { color: var(--muted) !important; }
        .hm-dept-card-people strong { color: var(--navy) !important; }

        .hm-perf-highlight { background: rgba(22, 38, 52, 0.95) !important; }
        .hm-perf-highlight * { color: #fff !important; }
        .hm-perf-highlight.below { background: rgba(42, 34, 16, 0.9) !important; }
        .hm-perf-highlight.below * { color: #fff !important; }

        .hm-mov-item { border-bottom-color: var(--line) !important; }
        .hm-mov-name { color: var(--navy) !important; }
        .hm-mov-info { color: var(--muted) !important; }
        .hm-mov-date { color: #6e7a86 !important; }

        .hm-top-item { border-bottom-color: var(--line) !important; }
        .hm-top-name { color: var(--navy) !important; }
        .hm-top-val  { color: var(--muted) !important; }

        /* ══ ORGANOGRAMA ══ */
        .card-gerencia {
            background: linear-gradient(135deg, #0d1a24 0%, #142232 52%, #182a3a 100%) !important;
            border-color: rgba(216, 165, 67, 0.35) !important;
        }
        .card-gerencia * { color: #fff !important; }
        .card-gerencia .cargo { color: #f4d491 !important; }

        .card-coordenador {
            background: linear-gradient(135deg, #1c2e3a 0%, #1a2a36 100%) !important;
            border-color: rgba(158, 181, 193, 0.2) !important;
        }
        .card-coordenador * { color: #fff !important; }

        .card-supervisor {
            background: linear-gradient(135deg, #3a2e14 0%, #2e2410 100%) !important;
        }
        .card-supervisor * { color: #fff !important; }

        .card-op {
            background: var(--surface) !important;
            border-color: var(--line) !important;
        }
        .card-op .nome  { color: var(--navy) !important; }
        .card-op .cargo { color: var(--muted) !important; }
        .card-op .info  { color: #6e7a86 !important; }

        .nivel-label { color: var(--navy) !important; border-left-color: var(--gold) !important; }
        .conector { color: var(--gold) !important; }

        .report-column { background: var(--surface) !important; border-color: var(--line) !important; }
        .report-head { background: linear-gradient(135deg, #142232 0%, #0d1a24 100%) !important; }
        .report-head * { color: #fff !important; }
        .report-child { background: var(--surface-soft) !important; border-color: var(--line) !important; }
        .report-child .nome  { color: var(--navy) !important; }
        .report-child .cargo { color: var(--muted) !important; }
        .report-child .meta  { color: #6e7a86 !important; }
        .report-source.seed { background: rgba(122, 173, 134, 0.15) !important; color: var(--green) !important; }
        .report-source.fallback { background: rgba(224, 168, 61, 0.15) !important; color: var(--gold) !important; }
        .report-empty { color: var(--muted) !important; }

        /* ══ CONTROLE DE PESSOAS ══ */
        .btn-secondary { background: var(--surface) !important; color: var(--navy-soft) !important; border-color: var(--line) !important; }
        .btn-secondary:hover { background: var(--surface-soft) !important; color: var(--navy) !important; }

        /* ══ USUARIOS ══ */
        .user-toolbar { border-color: var(--line) !important; }
        .user-panel { background: var(--surface) !important; border-color: var(--line) !important; }
        .user-panel-title { color: var(--navy) !important; }
        .user-panel-sub   { color: var(--muted) !important; }
        .user-table thead th { color: var(--muted) !important; border-bottom-color: var(--line) !important; background: var(--surface-soft) !important; }
        .user-table tbody tr { border-bottom-color: var(--line) !important; }
        .user-table tbody tr:hover { background: rgba(255, 255, 255, 0.03) !important; }
        .user-name  { color: var(--navy) !important; }
        .user-email { color: var(--muted) !important; }
        .user-role.admin { background: rgba(224, 168, 61, 0.12) !important; border-color: rgba(224, 168, 61, 0.2) !important; color: var(--gold) !important; }
        .user-role.usuario { background: rgba(122, 173, 134, 0.12) !important; border-color: rgba(122, 173, 134, 0.2) !important; color: var(--green) !important; }
        .user-tag { background: rgba(224, 168, 61, 0.1) !important; border-color: rgba(224, 168, 61, 0.2) !important; color: var(--gold) !important; }
        .profile-card { background: var(--surface) !important; border-color: var(--line) !important; }

        /* ══ PROCESSOS 360 — inline style overrides ══ */
        [style*="background:#f6f0e4"], [style*="background: #f6f0e4"] { background: var(--surface-soft) !important; }
        [style*="background:#fffdf8"], [style*="background: #fffdf8"] { background: var(--surface) !important; }
        [style*="background:#f6f1e7"], [style*="background: #f6f1e7"] { background: var(--surface-soft) !important; }
        [style*="background:#f0e8d8"], [style*="background: #f0e8d8"] { background: var(--surface-soft) !important; }
        [style*="background:#e3d8c5"], [style*="border-color:#e3d8c5"] { border-color: var(--line) !important; }

        /* Inline bg overrides for tags/pills with light bg */
        [style*="background:rgba(35,64,85,0.07)"],
        [style*="background: rgba(35,64,85,0.07)"],
        [style*="background:rgba(35, 64, 85, 0.07)"] {
            background: rgba(255, 255, 255, 0.08) !important;
            color: var(--navy) !important;
        }

        /* Inline color overrides for common light-mode colors */
        [style*="color:#234055"], [style*="color: #234055"] { color: var(--navy) !important; }
        [style*="color:#6f7a84"], [style*="color: #6f7a84"] { color: var(--muted) !important; }
        [style*="color:#223645"], [style*="color: #223645"] { color: var(--text) !important; }
        [style*="color:#7d8790"], [style*="color: #7d8790"] { color: var(--muted) !important; }
        [style*="color:#65707a"], [style*="color: #65707a"] { color: var(--muted) !important; }
        [style*="color:#87919a"], [style*="color: #87919a"] { color: #6e7a86 !important; }

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
