from datetime import datetime

import altair as alt
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


def altair_theme_args():
    """Retorna kwargs para .configure() de gráficos Altair no tema atual."""
    if is_dark_mode():
        return dict(
            background="transparent",
            title={"color": "#c9d6e0"},
            axis={
                "labelColor": "#8b949e",
                "titleColor": "#c9d6e0",
                "gridColor": "#30363d",
                "domainColor": "#30363d",
                "tickColor": "#30363d",
            },
            legend={
                "labelColor": "#8b949e",
                "titleColor": "#c9d6e0",
            },
            view={"stroke": "#30363d"},
            header={"labelColor": "#8b949e", "titleColor": "#c9d6e0"},
        )
    return dict(background="transparent")


def aplicar_estilos_globais():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #F5F5F7;
            --surface: #FFFFFF;
            --surface-soft: #FAFAFA;
            --line: #E5E5EA;
            --line-soft: #F2F2F7;
            --text: #111111;
            --muted: #6E6E73;
            --navy: #111111;
            --navy-soft: #333333;
            --accent: #111111;
            --accent-soft: rgba(17, 17, 17, 0.04);
            --role-coord: #4F46E5;
            --role-sup: #7C3AED;
            --role-dir: #111111;
            --green: #2E7D4F;
            --green-soft: #E8F4EC;
            --gold: #111111;
            --gold-soft: rgba(17, 17, 17, 0.04);
            --shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            --shadow-hover: 0 6px 20px rgba(0, 0, 0, 0.06);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.1rem !important;
            padding-bottom: 2rem !important;
        }

        [data-testid="stHeader"] {
            background: rgba(245, 245, 247, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }

        [data-testid="stSidebar"] {
            background: var(--surface-soft);
            border-right: 1px solid var(--line);
            width: 220px !important;
            min-width: 220px !important;
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
            border-radius: 10px;
            margin: 0.14rem 0 0.14rem 0;
            padding: 0.56rem 0.8rem;
            color: var(--muted) !important;
            transition: all 0.18s ease-in-out;
            text-decoration: none !important;
            font-weight: 500;
        }

        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNavItems"] a span,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span,
        [data-testid="stSidebar"] li a span {
            color: var(--muted) !important;
        }

        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNavItems"] a:hover,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover,
        [data-testid="stSidebar"] li a:hover {
            background: rgba(17, 17, 17, 0.05);
            color: var(--text) !important;
        }

        [data-testid="stSidebarNav"] a:hover span,
        [data-testid="stSidebarNavItems"] a:hover span,
        [data-testid="stSidebar"] li a:hover span {
            color: var(--text) !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] {
            background: rgba(17, 17, 17, 0.06);
            color: var(--text) !important;
            font-weight: 600;
            border: none;
            box-shadow: none;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNavItems"] a[aria-current="page"] span,
        [data-testid="stSidebar"] li a[aria-current="page"] span {
            color: var(--text) !important;
        }

        [data-testid="stSidebarNav"] span,
        [data-testid="stSidebarNavItems"] span {
            font-size: 0.92rem;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.02em;
            font-weight: 700;
        }

        h4, h5, h6 {
            color: var(--text);
            letter-spacing: -0.01em;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
            transition: all 0.2s ease-in-out;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 500;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: transparent;
            border-bottom: 1px solid var(--line);
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0.6rem 0.9rem;
            color: var(--muted);
            font-weight: 500;
            transition: all 0.2s ease-in-out;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text);
            background: rgba(17, 17, 17, 0.02);
        }

        .stTabs [aria-selected="true"] {
            background: transparent;
            color: var(--text) !important;
            border-bottom: 2px solid var(--text) !important;
            font-weight: 600;
        }

        .stButton button,
        .stDownloadButton button,
        .stFormSubmitButton button {
            border-radius: 10px;
            border: 1px solid var(--line);
            background: var(--surface);
            color: var(--text);
            font-weight: 500;
            box-shadow: none;
            transition: all 0.2s ease-in-out;
        }

        .stButton button:hover,
        .stDownloadButton button:hover,
        .stFormSubmitButton button:hover {
            border-color: #111111;
            background: rgba(17, 17, 17, 0.04);
            color: var(--text);
            transform: translateY(-1px);
        }

        .stButton button[kind="primary"],
        .stFormSubmitButton button[kind="primary"] {
            background: #111111;
            color: #FFFFFF;
            border-color: #111111;
        }

        .stButton button[kind="primary"]:hover,
        .stFormSubmitButton button[kind="primary"]:hover {
            background: #2a2a2a;
            border-color: #2a2a2a;
            color: #FFFFFF;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stDateInput > div > div,
        .stSelectbox > div > div,
        .stTextArea textarea {
            background: var(--surface) !important;
            border-radius: 10px !important;
            border: 1px solid var(--line) !important;
        }

        .stRadio > div {
            background: transparent;
            border-radius: 14px;
        }

        div[data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            box-shadow: var(--shadow);
        }

        .stAlert {
            border-radius: 12px;
            border: 1px solid var(--line);
            background: var(--surface);
        }

        .dashboard-shell {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 18px;
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
            font-size: 0.7rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .dashboard-title {
            color: var(--text);
            font-size: 1.9rem;
            font-weight: 700;
            line-height: 1.05;
            margin: 0;
            letter-spacing: -0.025em;
        }

        .dashboard-desc {
            color: var(--muted);
            font-size: 0.95rem;
            margin-top: 0.4rem;
            font-weight: 400;
        }

        .dashboard-badge {
            background: var(--line-soft);
            color: var(--muted);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.45rem 0.85rem;
            font-size: 0.78rem;
            font-weight: 600;
            white-space: nowrap;
            letter-spacing: 0.01em;
        }

        .dashboard-meta {
            margin-top: 0.85rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .dashboard-pill {
            background: var(--line-soft);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.38rem 0.7rem;
            color: var(--muted);
            font-size: 0.8rem;
            font-weight: 500;
        }

        /* ── Responsividade mobile ── */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] {
                width: auto !important;
                min-width: 0 !important;
            }

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

    # Registrar tema Altair dark/light
    if is_dark_mode():
        def _altair_dark():
            return {
                "config": {
                    "background": "transparent",
                    "title": {"color": "#c9d6e0"},
                    "axis": {
                        "labelColor": "#8b949e",
                        "titleColor": "#c9d6e0",
                        "gridColor": "#30363d",
                        "domainColor": "#30363d",
                        "tickColor": "#30363d",
                    },
                    "legend": {"labelColor": "#8b949e", "titleColor": "#c9d6e0"},
                    "view": {"stroke": "#30363d"},
                    "header": {"labelColor": "#8b949e", "titleColor": "#c9d6e0"},
                    "text": {"color": "#c9d6e0"},
                    "arc": {"stroke": "#30363d"},
                }
            }
        alt.themes.register("portal_dark", _altair_dark)
        alt.themes.enable("portal_dark")
        _aplicar_dark_mode()
    else:
        def _altair_light():
            return {"config": {"background": "transparent"}}
        alt.themes.register("portal_light", _altair_light)
        alt.themes.enable("portal_light")


def renderizar_dataframe(df, use_container_width=True, hide_index=True, height=None, **extra_kwargs):
    """Renderiza DataFrame como HTML estilizado (dark-mode-aware) ou st.dataframe."""
    import pandas as pd

    if not is_dark_mode():
        kwargs = dict(use_container_width=use_container_width, hide_index=hide_index, **extra_kwargs)
        if height is not None:
            kwargs["height"] = height
        if isinstance(df, pd.io.formats.style.Styler):
            st.dataframe(df, **kwargs)
        else:
            st.dataframe(df, **kwargs)
        return

    # Dark mode: render HTML table
    if isinstance(df, pd.io.formats.style.Styler):
        data = df.data
    else:
        data = df

    max_height_css = f"max-height:{height}px;overflow-y:auto;" if height else ""

    rows_html = ""
    for _, row in data.iterrows():
        cells = "".join(
            f'<td style="padding:10px 12px;border-bottom:1px solid #30363d;color:#d4dae2;font-size:13px;">'
            f'{v if v is not None else "—"}</td>'
            for v in row
        )
        rows_html += f"<tr>{cells}</tr>"

    header_cells = "".join(
        f'<th style="text-align:left;padding:10px 12px;font-size:11px;'
        f'color:#8b949e;text-transform:uppercase;font-weight:700;letter-spacing:0.08em;'
        f'border-bottom:1px solid #30363d;background:#1c2333;position:sticky;top:0;">{col}</th>'
        for col in data.columns
    )

    html = f"""
    <div style="border:1px solid #30363d;border-radius:10px;overflow:hidden;{max_height_css}">
        <table style="width:100%;border-collapse:collapse;background:#161b22;">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


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
            --accent: #e6e6e6;
            --accent-soft: rgba(255, 255, 255, 0.06);
            --role-coord: #8b83ef;
            --role-sup: #b29aef;
            --role-dir: #e6e6e6;
            --gold: #e6e6e6;
            --gold-soft: rgba(255, 255, 255, 0.06);
            --green: #7aad86;
            --green-soft: #1a2a1e;
            --shadow: 0 2px 14px rgba(0, 0, 0, 0.35);
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
                radial-gradient(circle at top left, rgba(255, 255, 255, 0.02), transparent 24%),
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
            box-shadow: none !important;
            outline: none !important;
        }
        [data-testid="stSidebarNav"] a span,
        [data-testid="stSidebarNavItems"] a span,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span,
        [data-testid="stSidebar"] li a span {
            background: transparent !important;
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
            box-shadow: none !important;
            outline: none !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] *,
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"] *,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] *,
        [data-testid="stSidebar"] li a[aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] * {
            background: rgba(255, 255, 255, 0.08) !important;
            color: #fff !important;
            border-color: transparent !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"],
        [data-testid="stSidebarNavItems"] a[aria-current="page"],
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"],
        [data-testid="stSidebar"] li a[aria-current="page"] {
            border: 1px solid transparent !important;
            box-shadow: none !important;
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span,
        [data-testid="stSidebarNavItems"] a[aria-current="page"] span,
        [data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] span,
        [data-testid="stSidebar"] li a[aria-current="page"] span {
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
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
            background: transparent !important;
            color: var(--text) !important;
            border-color: transparent !important;
            border-bottom: 2px solid var(--text) !important;
        }

        .stButton button,
        .stDownloadButton button,
        .stFormSubmitButton button {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            color: var(--text) !important;
        }
        .stButton button *,
        .stDownloadButton button *,
        .stFormSubmitButton button * {
            color: var(--text) !important;
        }
        .stButton button[kind="primary"],
        .stFormSubmitButton button[kind="primary"] {
            background: #fff !important;
            color: #0d1117 !important;
            border-color: #fff !important;
        }
        .stButton button[kind="primary"] *,
        .stFormSubmitButton button[kind="primary"] * {
            color: #0d1117 !important;
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

        /* st.dataframe — glide-data-grid theme via CSS custom props */
        [data-testid="stDataFrame"],
        .stDataFrame {
            color: var(--text) !important;
            background: var(--surface) !important;
            border-radius: 8px;
        }
        [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"],
        [data-testid="stDataFrame"] .dvn-scroller {
            background: var(--surface) !important;
        }
        [data-testid="stDataFrame"] [contenteditable="true"],
        [data-testid="stDataFrame"] input,
        [data-testid="stDataFrame"] textarea,
        [data-testid="stDataFrame"] select {
            background: var(--surface-soft) !important;
            color: var(--text) !important;
            border-color: var(--line) !important;
        }
        /* Override glide-data-grid canvas theme */
        .stApp {
            --gdg-bg-cell: #161b22 !important;
            --gdg-bg-cell-medium: #1c2333 !important;
            --gdg-bg-cell-selected: #242d3d !important;
            --gdg-bg-cell-selected-faded: #202938 !important;
            --gdg-bg-header: #1c2333 !important;
            --gdg-bg-header-has-focus: #242d3d !important;
            --gdg-bg-header-hovered: #242d3d !important;
            --gdg-border-color: #30363d !important;
            --gdg-horizontal-border-color: #30363d !important;
            --gdg-text-dark: #d4dae2 !important;
            --gdg-text-medium: #8b949e !important;
            --gdg-text-light: #6e7a86 !important;
            --gdg-text-header: #8b949e !important;
            --gdg-text-header-selected: #c9d6e0 !important;
            --gdg-text-group-header: #8b949e !important;
            --gdg-bg-search-result: rgba(255, 255, 255, 0.06) !important;
            --gdg-accent-color: #8b83ef !important;
            --gdg-accent-light: rgba(139, 131, 239, 0.15) !important;
            --gdg-accent-fg: #fff !important;
            --gdg-link-color: #58a6ff !important;
            --gdg-cell-horizontal-padding: 10px !important;
            --gdg-cell-vertical-padding: 8px !important;
        }

        /* st.caption, markdown */
        .stMarkdown p, .stCaption, [data-testid="stCaption"] {
            color: var(--text) !important;
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

        /* Homepage cards/links — avoid light blocks and focus halo in dark mode */
        .hm-lead-card,
        .hm-deptc,
        [data-testid="stMain"] [data-testid="stPageLink"] a {
            background: transparent !important;
            border-color: var(--line) !important;
            box-shadow: none !important;
        }
        .hm-deptc-count {
            background: rgba(255, 255, 255, 0.08) !important;
            color: var(--text) !important;
            border: 1px solid var(--line) !important;
        }
        .hm-lead-card:hover,
        [data-testid="stColumn"]:has(.hm-deptc):hover .hm-deptc,
        [data-testid="stMain"] [data-testid="stPageLink"] a:hover {
            background: transparent !important;
            border-color: rgba(255, 255, 255, 0.18) !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stPageLink"] a:focus,
        [data-testid="stMain"] [data-testid="stPageLink"] a:focus-visible,
        [data-testid="stMain"] [data-testid="stPageLink"] a:active {
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stPageLink"] a [data-testid="stIconMaterial"],
        [data-testid="stMain"] [data-testid="stPageLink"] a [data-testid="stIconMaterial"] *,
        [data-testid="stMain"] [data-testid="stPageLink"] a [data-testid="stIconEmoji"],
        [data-testid="stMain"] [data-testid="stPageLink"] a [data-testid="stIconEmoji"] * {
            background: transparent !important;
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stPageLink"],
        [data-testid="stMain"] [data-testid="stPageLink"] *,
        [data-testid="stMain"] [data-testid="stPageLink"] p {
            background-color: transparent !important;
        }
        [data-testid="stForm"] {
            background: var(--surface) !important;
            border: 1px solid var(--line) !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
        }

        .hm-kpi {
            background: #161b22 !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-color: var(--line) !important;
        }
        .hm-kpi:hover {
            background: #1c2333 !important;
            border-color: rgba(255, 255, 255, 0.18) !important;
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
            border-color: rgba(255, 255, 255, 0.18) !important;
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
            background: rgba(255, 255, 255, 0.06) !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
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
            border-top-color: rgba(255, 255, 255, 0.18) !important;
        }
        .hm-dept-card:hover {
            background: #1c2333 !important;
            border-color: rgba(255, 255, 255, 0.18) !important;
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
        .card-analista {
            background: #1c2333 !important;
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
        .report-source.fallback { background: rgba(255, 255, 255, 0.06) !important; color: var(--gold) !important; }
        .report-empty { color: var(--muted) !important; }

        /* ══ CONTROLE DE PESSOAS ══ */
        .btn-secondary { background: var(--surface) !important; color: var(--navy-soft) !important; border-color: var(--line) !important; }
        .btn-secondary:hover { background: var(--surface-soft) !important; color: var(--navy) !important; }

        /* ══ USUARIOS ══ */
        .user-toolbar {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.95) 0%, rgba(28, 35, 51, 0.95) 100%) !important;
            border-color: var(--line) !important;
        }
        .user-toolbar strong { color: var(--navy) !important; }
        .user-panel { background: var(--surface) !important; border-color: var(--line) !important; }
        .user-panel-title { color: var(--navy) !important; }
        .user-panel-sub   { color: var(--muted) !important; }
        .user-table { background: var(--surface) !important; }
        .user-table thead th { color: var(--muted) !important; border-bottom-color: var(--line) !important; background: var(--surface-soft) !important; }
        .user-table td { color: var(--text) !important; border-bottom-color: var(--line) !important; background: transparent !important; }
        .user-table tbody tr { border-bottom-color: var(--line) !important; }
        .user-table tbody tr:hover { background: rgba(255, 255, 255, 0.03) !important; }
        .user-name  { color: var(--navy) !important; }
        .user-email { color: var(--muted) !important; }
        .user-status { color: var(--green) !important; }
        .user-status.inativo { color: var(--gold) !important; }
        .user-role { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.1) !important; color: var(--gold) !important; }
        .user-role.admin { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.1) !important; color: var(--gold) !important; }
        .user-role.usuario, .user-role.user { background: rgba(122, 173, 134, 0.12) !important; border-color: rgba(122, 173, 134, 0.2) !important; color: var(--green) !important; }
        .user-tag { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.1) !important; color: var(--gold) !important; }
        .profile-card { background: var(--surface) !important; border-color: var(--line) !important; }

        /* ══ HTML tables (global dark override) ══ */
        .stApp table {
            background: var(--surface) !important;
        }
        .stApp table thead tr {
            background: var(--surface-soft) !important;
        }
        .stApp table th {
            color: var(--muted) !important;
            background: var(--surface-soft) !important;
            border-bottom-color: var(--line) !important;
        }
        .stApp table td {
            color: var(--text) !important;
            border-bottom-color: var(--line) !important;
        }
        .stApp table tr {
            border-bottom-color: var(--line) !important;
        }
        [style*="border-bottom:1px solid #f0e8d8"],
        [style*="border-bottom: 1px solid #f0e8d8"],
        [style*="border-bottom:1px solid #efe7da"],
        [style*="border-bottom: 1px solid #efe7da"] {
            border-bottom-color: var(--line) !important;
        }

        /* ══ PROCESSOS 360 — inline style overrides ══ */
        [style*="background:#f6f0e4"], [style*="background: #f6f0e4"] { background: var(--surface-soft) !important; }
        [style*="background:#fffdf8"], [style*="background: #fffdf8"] { background: var(--surface) !important; }
        [style*="background:#f6f1e7"], [style*="background: #f6f1e7"] { background: var(--surface-soft) !important; }
        [style*="background:#f0e8d8"], [style*="background: #f0e8d8"] { background: var(--surface-soft) !important; }
        [style*="background:#e3d8c5"], [style*="border-color:#e3d8c5"] { border-color: var(--line) !important; }
        /* Pipeline KPI strip (Processos 360 Visão Geral) */
        [style*="background: linear-gradient(135deg, rgba(255,253,248"],
        [style*="background:linear-gradient(135deg,rgba(255,253,248"],
        [style*="background: linear-gradient(135deg, rgba(255, 253, 248"] {
            background: linear-gradient(135deg, #161b22, #1c2333) !important;
            border-color: var(--line) !important;
        }
        [style*="background: rgba(255,255,255,0.6)"],
        [style*="background:rgba(255,255,255,0.6)"] {
            background: var(--surface-soft) !important;
            border-color: var(--line) !important;
        }
        [style*="rgba(245,245,247,0.96)"],
        [style*="rgba(250,250,252,0.96)"],
        [style*="background:rgba(245,245,247,0.5)"],
        [style*="background: rgba(245,245,247,0.5)"] {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            box-shadow: none !important;
        }
        [style*="background:#FAFAFA"], [style*="background: #FAFAFA"] {
            background: var(--surface-soft) !important;
        }

        /* ══ Gráficos Altair/Vega — fundo transparente ══ */
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"],
        .vega-embed,
        .vega-embed summary,
        .vega-embed .chart-wrapper {
            background: transparent !important;
        }
        .vega-embed .vega-bindings,
        .vega-embed .vega-bindings * {
            color: var(--text) !important;
        }
        .vega-embed svg { background: transparent !important; }
        .vega-embed canvas { background: transparent !important; }
        /* Only the outermost background rect, NOT data marks */
        .vega-embed svg > g > rect.background,
        .vega-embed svg > rect {
            fill: transparent !important;
        }

        /* Inline bg overrides for tags/pills with light bg */
        [style*="background:rgba(35,64,85,0.07)"],
        [style*="background: rgba(35,64,85,0.07)"],
        [style*="background:rgba(35, 64, 85, 0.07)"] {
            background: rgba(255, 255, 255, 0.08) !important;
            color: var(--navy) !important;
        }

        /* Restituições / Jurídico — tags legíveis e ações sem fundo branco */
        .rst-tag,
        .pj-tag {
            background: rgba(255, 255, 255, 0.08) !important;
            color: var(--text) !important;
            border-color: var(--line) !important;
        }
        .rst-tag-status,
        .pj-tag-status {
            background: #1c2333 !important;
            color: var(--navy) !important;
            border-color: var(--line) !important;
        }
        div[class*="st-key-rst-row-"] button,
        div[class*="st-key-pj-row-"] button,
        div[class*="st-key-rst-row-"] [data-testid="stPopover"] button,
        div[class*="st-key-pj-row-"] [data-testid="stPopover"] button {
            background: var(--surface-soft) !important;
            color: var(--text) !important;
            border-color: var(--line) !important;
        }
        div[class*="st-key-rst-row-"] button:hover,
        div[class*="st-key-pj-row-"] button:hover {
            background: #242d3d !important;
            border-color: rgba(255, 255, 255, 0.18) !important;
        }
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
            background: transparent !important;
            box-shadow: none !important;
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
