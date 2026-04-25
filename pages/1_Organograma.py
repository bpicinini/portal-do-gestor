from datetime import date
from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils.auth import garantir_autenticado
from utils.departamentos import listar_cargos, listar_departamentos
from utils.organograma import construir_estrutura_reportes
from utils.pessoas import atualizar_responsavel_direto, contratar, desligar, listar_colaboradores, listar_historico
from utils.ui import aplicar_estilos_globais, is_dark_mode, renderizar_cabecalho_pagina, renderizar_dataframe


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
        radial-gradient(circle at top right, rgba(242, 212, 145, 0.22), transparent 30%),
        linear-gradient(135deg, #0f2232 0%, #1b3549 55%, #111111 100%);
    color: white;
    border-radius: 22px;
    padding: 18px 20px;
    margin: 4px 2px;
    min-height: 92px;
    border: 1px solid rgba(216, 165, 67, 0.38);
    border-left: 6px solid #d8a543;
    box-shadow: 0 18px 40px rgba(15, 34, 50, 0.28);
    position: relative;
    overflow: hidden;
}
.card-coordenador {
    background: linear-gradient(135deg, #1b3a4d 0%, #111111 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 5px solid #5ba8cc;
    box-shadow: 0 10px 28px rgba(27, 58, 77, 0.18);
}
.card-supervisor {
    background: linear-gradient(135deg, #2c5268 0%, #3c6478 100%);
    color: white;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 2px;
    min-height: 72px;
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 4px solid #80c2df;
    box-shadow: 0 8px 22px rgba(44, 82, 104, 0.16);
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
    opacity: 0.82;
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
    opacity: 0.68;
    margin-top: 2px;
}
/* Analistas e especialistas (nivel 3–6): tint sutil, borda azul */
.card-analista {
    background: #edf3f7;
    border: 1px solid #c4d6e0;
    border-left: 4px solid #6aaac8;
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 4px 14px rgba(35, 64, 85, 0.07);
}
.card-analista.nh { border-left: 4px solid #3b82f6; }
.card-analista.ita { border-left: 4px solid #16a34a; }
.card-analista .nome {
    font-weight: 700;
    font-size: 13px;
    color: #111111;
    line-height: 1.3;
}
.card-analista .cargo { font-size: 11px; color: #6E6E73; margin-top: 2px; }
.card-analista .info  { font-size: 11px; color: #6E6E73; margin-top: 1px; }
/* Assistentes / Estagiários (nivel 7+): neutro, apenas borda fina */
.card-op {
    background: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-left: 4px solid #E5E5EA;
    border-radius: 16px;
    padding: 9px 12px;
    margin: 3px 2px;
    min-height: 62px;
    box-shadow: 0 4px 14px rgba(35, 64, 85, 0.06);
}
.card-op.nh  { border-left: 4px solid #3b82f6; }
.card-op.ita { border-left: 4px solid #16a34a; }
.card-op .nome  { font-weight: 700; font-size: 13px; color: #111111; line-height: 1.3; }
.card-op .cargo { font-size: 11px; color: #6E6E73; margin-top: 2px; }
.card-op .info  { font-size: 11px; color: #6E6E73; margin-top: 1px; }
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
    font-weight: 700;
    color: #111111;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 14px 0 6px 0;
    padding-left: 8px;
    border-left: 3px solid #111111;
}
.conector {
    text-align: center;
    color: #6E6E73;
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
    background: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 20px;
    padding: 14px;
    box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
}
.report-head {
    background: #edf3f7;
    border: 1px solid #c4d6e0;
    border-left: 4px solid #6aaac8;
    border-radius: 16px;
    padding: 14px 16px;
}
.report-head.nh  { border-left: 4px solid #3b82f6; }
.report-head.ita { border-left: 4px solid #16a34a; }
.report-head .nome {
    font-size: 14px;
    font-weight: 800;
    line-height: 1.2;
    color: #111111;
}
.report-head .cargo {
    font-size: 11px;
    color: #6E6E73;
    margin-top: 3px;
}
.report-head .meta {
    font-size: 11px;
    color: #6E6E73;
    margin-top: 5px;
}
.report-stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
}
.report-child {
    background: #FAFAFA;
    border: 1px solid #E5E5EA;
    border-left: 4px solid #E5E5EA;
    border-radius: 14px;
    padding: 11px 12px;
}
.report-child.nh { border-left: 4px solid #3b82f6; }
.report-child.ita { border-left: 4px solid #16a34a; }
.report-child .nome {
    color: #111111;
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
.report-source.fallback { background: #FAFAFA; color: #6E6E73; }
.report-empty {
    color: #7a848d;
    font-size: 12px;
    padding: 8px 2px 2px;
}
.lider-secao {
    border: 1px solid #E5E5EA;
    border-top: 4px solid #111111;
    border-radius: 18px;
    padding: 16px 16px 12px;
    margin-bottom: 18px;
    background: #FFFFFF;
}
.lider-secao-topo {
    margin-bottom: 14px;
}
.filtro-label {
    font-size: 11px;
    font-weight: 700;
    color: #9aa4ae;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 2px;
}
/* Botões de filtro em colunas: pills compactos e sutis */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
    border-radius: 999px !important;
    font-size: 12px !important;
    padding: 3px 14px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    min-height: 0 !important;
    height: auto !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #E5E5EA !important;
    color: #6E6E73 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: rgba(17, 17, 17, 0.04) !important;
    border-color: #111111 !important;
    color: #111111 !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] {
    background: #111111 !important;
    border: 1px solid #111111 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] * {
    color: #FFFFFF !important;
}

/* Evita painel branco grande na aba de reportes (mantém comportamento igual ao restante da página) */
div[data-testid="stExpander"] {
    background: transparent !important;
}
div[data-testid="stExpanderDetails"] {
    background: transparent !important;
}
</style>
""",
    unsafe_allow_html=True,
)

if is_dark_mode():
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] {
            background: #1f3b52 !important;
            border-color: #2b4a63 !important;
            color: #d4dae2 !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[kind="primary"] * {
            color: #d4dae2 !important;
        }
        .report-column,
        .lider-secao,
        .report-child,
        .report-source.fallback {
            background: #161b22 !important;
            border-color: #30363d !important;
        }
        .report-head {
            background: linear-gradient(135deg, #1b3245 0%, #213a4f 100%) !important;
            border-color: #2b4a63 !important;
        }
        div[data-testid="stExpander"],
        div[data-testid="stExpanderDetails"] {
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

NIVEL_LABEL = {
    0.5: "Gerência",
    1: "Gerência",
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
    if nivel < 7:
        return _card("card-analista", nome, cargo, unidade, peso=peso)
    return _card("card-op", nome, cargo, unidade, peso=peso)


def _card_reporte_analista(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    return (
        f'<div class="report-head{extra}">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        "</div>"
    )


def _card_reporte_subordinado(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    u_cls = _unidade_class(unidade)
    extra = f" {u_cls}" if u_cls else ""
    return (
        f'<div class="report-child{extra}">'
        f'<div class="nome">{escape(str(pessoa["nome"]))}</div>'
        f'<div class="cargo">{escape(str(pessoa["cargo_nome"]))}</div>'
        f'<div class="meta">{_badge_unidade(unidade)}</div>'
        "</div>"
    )


# ── Departamento como abas ────────────────────────────────────────────────────

gerencia_geral = [c for c in todos_ativos if _nivel(c) <= 1]

MESES_PT_ORG = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _render_quadro(fd, fu, _ks):
    """Renderiza o quadro completo (data editor com responsaveis diretos)."""
    st.subheader("Quadro completo")
    st.caption(
        "Edite a coluna 'Responsável Direto' diretamente na tabela e clique em Salvar. "
        "O organograma de reportes reflete imediatamente."
    )
    if todos_ativos:
        df_raw = pd.DataFrame(todos_ativos)

        if "responsavel_direto" not in df_raw.columns:
            df_raw["responsavel_direto"] = None

        _analistas = [p for p in todos_ativos if 3 <= float(p.get("cargo_nivel") or 99) < 7]
        _lideres_resp = [p for p in todos_ativos if 1 < float(p.get("cargo_nivel") or 99) <= 2.5]
        _opcoes_resp = [""] + sorted({p["nome"] for p in _lideres_resp + _analistas})

        df_quad = df_raw[[
            "id", "nome", "departamento_nome", "cargo_nome", "cargo_nivel",
            "peso_manpower", "unidade", "gestor_direto", "responsavel_direto",
        ]].copy()
        df_quad.columns = [
            "ID", "Nome", "Departamento", "Cargo", "Nivel",
            "MP", "Und.", "Gestor", "Responsável Direto",
        ]

        df_quad.insert(6, "U", df_quad["Und."].map(
            {"Novo Hamburgo": "🔵 NH", "Itajaí": "🟢 ITJ"}
        ).fillna("--"))

        if fd != "Todos":
            df_quad = df_quad[df_quad["Departamento"] == fd]
        if fu != "Todas":
            df_quad = df_quad[df_quad["Und."] == fu]
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
                "U": st.column_config.TextColumn(disabled=True, width="small"),
                "Und.": st.column_config.TextColumn(disabled=True),
                "Gestor": st.column_config.TextColumn(disabled=True),
                "Responsável Direto": st.column_config.SelectboxColumn(
                    options=_opcoes_resp,
                    help="Analista ou coordenador responsavel direto no organograma de reportes.",
                ),
            },
            key=f"editor_quadro_{_ks}",
        )

        if st.button("Salvar reportes", type="primary", key=f"btn_salvar_resp_{_ks}"):
            _alteracoes = []
            for idx in df_quad.index:
                old_val = str(df_quad.at[idx, "Responsável Direto"] or "").strip()
                new_val = str(edited_quad.at[idx, "Responsável Direto"] or "").strip()
                if old_val != new_val:
                    _alteracoes.append((int(df_quad.at[idx, "ID"]), new_val or None))
            if _alteracoes:
                for _cid, _resp in _alteracoes:
                    atualizar_responsavel_direto(_cid, _resp)
                st.success(f"{len(_alteracoes)} reporte(s) salvo(s). Confira na aba 'Visao por reportes'.")
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada.")

        st.caption(f"Total exibido: {len(df_quad)} colaboradores")
    else:
        st.info("Nenhum colaborador cadastrado.")


def _render_views(fd):
    """Renderiza as abas de conteudo filtradas pelo departamento `fd`."""
    _uni_key = f"filtro_uni_{fd.lower().replace(' ', '').replace('/', '')}"
    if _uni_key not in st.session_state:
        st.session_state[_uni_key] = "Todas"

    st.markdown('<div class="filtro-label">Unidade</div>', unsafe_allow_html=True)
    _opcoes_uni = ["Todas", "Novo Hamburgo", "Itajaí"]
    _ucols = st.columns(len(_opcoes_uni))
    for _i, _opt in enumerate(_opcoes_uni):
        with _ucols[_i]:
            if st.button(
                _opt,
                key=f"_utag_{fd.lower().replace(' ', '')}_{_i}",
                type="primary" if st.session_state[_uni_key] == _opt else "secondary",
                use_container_width=True,
            ):
                st.session_state[_uni_key] = _opt
                st.rerun()
    fu = st.session_state[_uni_key]
    _ks = fd.lower().replace(" ", "").replace("/", "")

    # ─────────────────────────────────────────────────────────────────────
    # ABA "TODOS" — organograma único + quadro completo
    # ─────────────────────────────────────────────────────────────────────
    if fd == "Todos":
        tab_org, tab_quadro = st.tabs(["Organograma", "Quadro completo"])

        with tab_org:
            _dark = is_dark_mode()
            _bg_body    = "#0e1117" if _dark else "#ffffff"
            _card_bg    = "rgba(255,255,255,0.07)" if _dark else "#f2f6fa"
            _card_bdr   = "#2e4a60" if _dark else "#c0d2e2"
            _text_main  = "#ddeaf2" if _dark else "#1a2a38"
            _text_sub   = "#789ab0" if _dark else "#4a6a80"
            _line_col   = "#2e4a60" if _dark else "#a8bece"
            _dept_oc = {
                "Importação":          "#1a5a9e",
                "Agenciamento":        "#1a7a3a",
                "Exportação":          "#4a8a1a",
                "Seguro Internacional":"#8a6a0a",
            }

            visible_ids = {
                p["id"] for p in todos_ativos
                if fu == "Todas" or str(p.get("unidade") or "") == fu
            }
            _fp: dict = {}
            for p in todos_ativos:
                if p["id"] not in visible_ids:
                    continue
                g = str(p.get("gestor_direto") or "").strip()
                if g:
                    _fp.setdefault(g, []).append(p)
            for k in _fp:
                _fp[k].sort(key=lambda x: (_nivel(x), x.get("nome", "")))

            _c_abbr = {
                "Gerente de Operações":       "Gerente de Operações",
                "Coordenador de Importação":  "Coord. Import.",
                "Coordenadora de Importação": "Coord. Import.",
                "Coordenador de Exportação":  "Coord. Export.",
                "Coordenadora de Exportação": "Coord. Export.",
                "Coordenador":   "Coord.",
                "Coordenadora":  "Coord.",
                "Supervisor":    "Supervisor",
                "Especialista":  "Especialista",
                "Analista Sênior": "An. Sênior",
                "Analista Pleno":  "An. Pleno",
                "Analista Júnior": "An. Júnior",
                "Assistente":    "Assist.",
                "Estagiário":    "Estag.",
                "Jovem Aprendiz":"J. Aprendiz",
            }

            _seen2: set = set()
            _seen2_names: set = set()

            def _oc_card(p, depth):
                nome  = p.get("nome", "")
                cargo = _c_abbr.get(p.get("cargo_nome", ""), p.get("cargo_nome", ""))
                dept  = p.get("departamento_nome", "")
                dc    = _dept_oc.get(dept, "#556070")
                if depth <= 1:
                    nm_s, rl_s, mw = "13px", "10.5px", "108px"
                elif depth == 2:
                    nm_s, rl_s, mw = "12px", "10px",   "96px"
                else:
                    nm_s, rl_s, mw = "11px", "9.5px",  "82px"
                border_top = f"3px solid {dc}" if depth == 2 else f"1px solid {_card_bdr}"
                dept_short = {
                    "Importação": "Import.", "Agenciamento": "Agenc.",
                    "Exportação": "Export.", "Seguro Internacional": "Seguro",
                }.get(dept, dept)
                dept_badge = (
                    f'<div style="font-size:8px;color:#fff;background:{dc};'
                    f'border-radius:2px;padding:1px 5px;margin-top:3px;'
                    f'display:inline-block;">{dept_short}</div>'
                ) if depth == 2 else ""
                return (
                    f'<div class="oc-card" style="min-width:{mw};border-top:{border_top};">'
                    f'<div style="font-size:{nm_s};font-weight:600;color:{_text_main};'
                    f'line-height:1.3;">{nome}</div>'
                    f'<div style="font-size:{rl_s};color:{_text_sub};margin-top:2px;'
                    f'line-height:1.2;">{cargo}</div>'
                    f'{dept_badge}'
                    f'</div>'
                )

            def _fp_get(nome):
                """Lookup children by full name, fallback to first+last name."""
                ch = _fp.get(nome, [])
                if not ch:
                    parts = nome.split()
                    if len(parts) > 2:
                        ch = _fp.get(parts[0] + " " + parts[-1], [])
                return ch

            def _oc_li(p, depth):
                if p["id"] in _seen2 or p.get("nome", "") in _seen2_names:
                    return ""
                _seen2.add(p["id"])
                _seen2_names.add(p.get("nome", ""))
                children = [c for c in _fp_get(p["nome"]) if c["id"] not in _seen2 and c.get("nome", "") not in _seen2_names]
                card = _oc_card(p, depth)
                if not children:
                    return f"<li>{card}</li>"
                ch = "".join(_oc_li(c, depth + 1) for c in children)
                return f"<li>{card}<ul>{ch}</ul></li>"

            bruno = next(
                (p for p in todos_ativos if "Bruno" in p.get("nome", "") and "Picinini" in p.get("nome", "")),
                next((p for p in todos_ativos if str(p.get("gestor_direto", "")).strip() == "Gabriel Spohr"), None),
            )

            gabriel_card = (
                f'<div class="oc-card oc-top">'
                f'<div style="font-size:14px;font-weight:700;color:{_text_main};">Gabriel Spohr</div>'
                f'<div style="font-size:11px;color:{_text_sub};margin-top:2px;">Diretor de Operações</div>'
                f'</div>'
            )

            if bruno and bruno["id"] in visible_ids:
                _seen2.add(bruno["id"])
                bruno_card = _oc_card(bruno, 1)
                diretos = [c for c in _fp.get(bruno["nome"], []) if c["id"] in visible_ids]
                ch_html = "".join(_oc_li(d, 2) for d in diretos)
                inner = (
                    f"<li>{gabriel_card}"
                    f"<ul><li>{bruno_card}<ul>{ch_html}</ul></li></ul>"
                    f"</li>"
                )
            else:
                inner = f"<li>{gabriel_card}</li>"

            _lc = _line_col
            html_doc = (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
                f"*{{box-sizing:border-box;margin:0;padding:0;}}"
                f"body{{background:{_bg_body};font-family:system-ui,-apple-system,sans-serif;"
                f"padding:16px 24px 28px;overflow:auto;}}"
                f".oc-root{{display:flex;justify-content:center;list-style:none;padding:0;margin:0;}}"
                f"ul{{display:flex;justify-content:center;list-style:none;"
                f"padding:22px 0 0;position:relative;margin:0;}}"
                f"li>ul::before{{content:'';position:absolute;top:0;left:50%;"
                f"border-left:1px solid {_lc};height:22px;}}"
                f"li{{list-style-type:none;text-align:center;position:relative;"
                f"padding:22px 5px 0;display:flex;flex-direction:column;align-items:center;}}"
                f".oc-root>li{{padding-top:0;}}"
                f"li::before,li::after{{content:'';position:absolute;top:0;right:50%;"
                f"border-top:1px solid {_lc};width:50%;height:22px;}}"
                f"li::after{{right:auto;left:50%;border-left:1px solid {_lc};}}"
                f".oc-root>li::before,.oc-root>li::after{{display:none;}}"
                f"li:only-child::before,li:only-child::after{{display:none;}}"
                f"li:only-child{{padding-top:0;}}"
                f"li:first-child::before,li:last-child::after{{border:0 none;}}"
                f"li:last-child::before{{border-right:1px solid {_lc};border-radius:0 4px 0 0;}}"
                f"li:first-child::after{{border-radius:4px 0 0 0;}}"
                f".oc-card{{background:{_card_bg};border:1px solid {_card_bdr};"
                f"border-radius:6px;padding:5px 8px;text-align:center;max-width:130px;flex-shrink:0;}}"
                f".oc-top{{padding:8px 14px;min-width:160px;border-width:1px;}}"
                f"</style></head><body>"
                f"<ul class='oc-root'>{inner}</ul>"
                f"</body></html>"
            )

            _max_d = [0]
            def _depth(name, d=0):
                _max_d[0] = max(_max_d[0], d)
                for c in _fp_get(name):
                    _depth(c["nome"], d + 1)
            if bruno:
                _depth(bruno["nome"], 1)
            _est_h = max(500, (_max_d[0] + 2) * 100 + 60)
            components.html(html_doc, height=_est_h, scrolling=True)

        with tab_quadro:
            _render_quadro(fd, fu, _ks)

    # ─────────────────────────────────────────────────────────────────────
    # ABAS POR DEPARTAMENTO — 4 visões mantidas
    # ─────────────────────────────────────────────────────────────────────
    else:
        tab_niveis, tab_reportes, tab_quadro, tab_gestao = st.tabs(
            ["Visao por niveis", "Visao por reportes", "Quadro completo", "Gestao de equipe"]
        )

        with tab_niveis:
            st.subheader("Visao por niveis")

            for depto in departamentos:
                if depto["nome"] != fd:
                    continue

                dept_colabs = listar_colaboradores(status="Ativo", departamento_id=int(depto["id"]))
                ids_dept = {c.get("id") for c in dept_colabs}
                gerencia_extra = [g for g in gerencia_geral if g.get("id") not in ids_dept]
                dept_todos = gerencia_extra + dept_colabs

                if fu != "Todas":
                    dept_filtrado = gerencia_extra + [
                        p for p in dept_colabs if str(p.get("unidade") or "") == fu
                    ]
                else:
                    dept_filtrado = dept_todos

                if not dept_filtrado:
                    continue

                with st.expander(
                    f"**{depto['nome']}** | {len(dept_filtrado)} pessoas",
                    expanded=True,
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

        with tab_reportes:
            st.subheader("Visao por reportes imediatos")
            st.caption("Reportes definidos no Quadro completo.")

            def _html_grupo_analista(grupo):
                html = '<div class="report-column">'
                html += _card_reporte_analista(grupo["analista"])
                if grupo["reportes"]:
                    html += '<div class="report-stack">'
                    for p in grupo["reportes"]:
                        html += _card_reporte_subordinado(p)
                    html += "</div>"
                else:
                    html += '<div class="report-empty">Nenhum reporte alocado.</div>'
                html += "</div>"
                return html

            for bloco in estrutura_reportes:
                if bloco["departamento"] != fd:
                    continue

                ids_bloco = {p.get("id") for p in bloco["lideres"]}
                gerencia_extra_rep = [g for g in gerencia_geral if g.get("id") not in ids_bloco]

                def _conta_secao(secao):
                    total = 1
                    for ga in secao["grupos_analistas"]:
                        total += 1 + len(ga["reportes"])
                    total += len(secao["reportes_diretos"])
                    return total

                secoes = bloco.get("secoes_lider", [])
                sem_aloc = bloco.get("sem_alocacao", [])
                grupos_sem_lider = bloco.get("grupos_sem_lider", [])

                if fu != "Todas":
                    def _filtra_secao(secao):
                        lider_ok = str(secao["lider"].get("unidade") or "") == fu
                        grupos_f = [
                            {
                                "analista": g["analista"],
                                "reportes": [
                                    p for p in g["reportes"]
                                    if str(p.get("unidade") or "") == fu
                                ],
                            }
                            for g in secao["grupos_analistas"]
                            if str(g["analista"].get("unidade") or "") == fu
                            or any(str(p.get("unidade") or "") == fu for p in g["reportes"])
                        ]
                        rd_f = [p for p in secao["reportes_diretos"] if str(p.get("unidade") or "") == fu]
                        if lider_ok or grupos_f or rd_f:
                            return {**secao, "grupos_analistas": grupos_f, "reportes_diretos": rd_f}
                        return None

                    secoes = [s for s in [_filtra_secao(s) for s in secoes] if s]
                    grupos_sem_lider = [
                        {
                            "analista": g["analista"],
                            "reportes": [
                                p for p in g["reportes"]
                                if str(p.get("unidade") or "") == fu
                            ],
                        }
                        for g in grupos_sem_lider
                        if str(g["analista"].get("unidade") or "") == fu
                        or any(str(p.get("unidade") or "") == fu for p in g["reportes"])
                    ]
                    sem_aloc = [p for p in sem_aloc if str(p.get("unidade") or "") == fu]

                dept_total = (
                    len(gerencia_extra_rep)
                    + sum(_conta_secao(s) for s in secoes)
                    + sum(1 + len(g["reportes"]) for g in grupos_sem_lider)
                    + len(sem_aloc)
                )

                with st.expander(
                    f"**{bloco['departamento']}** | {dept_total} pessoas",
                    expanded=True,
                ):
                    if gerencia_extra_rep:
                        st.markdown('<div class="nivel-label">Gerencia</div>', unsafe_allow_html=True)
                        h = '<div class="report-leaders">'
                        for p in gerencia_extra_rep:
                            h += card_para_nivel(p)
                        h += "</div>"
                        st.markdown(h, unsafe_allow_html=True)

                    for secao in secoes:
                        lider = secao["lider"]
                        grupos_a = secao["grupos_analistas"]
                        rep_dir = secao["reportes_diretos"]

                        html = '<div class="lider-secao">'
                        html += '<div class="lider-secao-topo">'
                        html += card_para_nivel(lider)
                        html += "</div>"

                        if grupos_a:
                            html += '<div class="report-grid">'
                            for grupo in grupos_a:
                                html += _html_grupo_analista(grupo)
                            html += "</div>"

                        if rep_dir:
                            html += '<div class="report-stack" style="margin-top:10px">'
                            for p in rep_dir:
                                html += _card_reporte_subordinado(p)
                            html += "</div>"

                        html += "</div>"
                        st.markdown(html, unsafe_allow_html=True)

                    if grupos_sem_lider:
                        st.markdown('<div class="nivel-label">Analistas (sem lideranca definida)</div>', unsafe_allow_html=True)
                        html = '<div class="report-grid">'
                        for grupo in grupos_sem_lider:
                            html += _html_grupo_analista(grupo)
                        html += "</div>"
                        st.markdown(html, unsafe_allow_html=True)

                    if sem_aloc:
                        st.markdown('<div class="nivel-label">Sem alocacao definida</div>', unsafe_allow_html=True)
                        html = '<div class="report-leaders">'
                        for p in sem_aloc:
                            html += card_para_nivel(p)
                        html += "</div>"
                        st.markdown(html, unsafe_allow_html=True)

        with tab_quadro:
            _render_quadro(fd, fu, _ks)

        with tab_gestao:
            st.subheader("Gestao de equipe")
            st.caption("Registre entradas, saidas e consulte o histórico consolidado da equipe.")

            subtab_contrat, subtab_desl, subtab_hist = st.tabs(
                ["Contratações", "Saídas", "Histórico"]
            )

            with subtab_contrat:
                st.subheader("Nova Contratação")
                st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

                with st.form(f"form_contratacao_{_ks}", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_novo = st.text_input("Nome completo", key=f"cont_nome_{_ks}")
                        dept_sel = st.selectbox(
                            "Departamento",
                            options=[d["nome"] for d in departamentos],
                            key=f"gest_dept_contrat_{_ks}",
                        )
                        dept_id_sel = next((d["id"] for d in departamentos if d["nome"] == dept_sel), None)
                        cargos_dept = listar_cargos(dept_id_sel)
                        cargo_options = {c["nome"]: c["id"] for c in cargos_dept}
                        cargo_nomes = list(cargo_options.keys())
                        cargo_sel = st.selectbox("Cargo", options=cargo_nomes, disabled=not cargo_nomes, key=f"cont_cargo_{_ks}")
                        if not cargo_nomes:
                            st.info("Cadastre ao menos um cargo nesse departamento antes de registrar.")
                    with col2:
                        unidade_c = st.selectbox("Unidade", ["Novo Hamburgo", "Itajaí"], key=f"cont_unidade_{_ks}")
                        gestor = st.text_input("Gestor direto", key=f"cont_gestor_{_ks}")
                        data_entrada = st.date_input("Data de entrada", value=date.today(), key=f"cont_data_{_ks}")
                        obs = st.text_area("Observacao (opcional)", height=68, key=f"cont_obs_{_ks}")

                    if st.form_submit_button("Registrar contratação", type="primary", disabled=not cargo_options):
                        if nome_novo.strip() and cargo_sel:
                            novo_id = contratar(
                                nome=nome_novo.strip(),
                                cargo_id=cargo_options[cargo_sel],
                                departamento_id=dept_id_sel,
                                empresa=unidade_c,
                                cidade=unidade_c,
                                gestor_direto=gestor,
                                data_entrada=data_entrada,
                                observacao=obs,
                            )
                            st.success(f"**{nome_novo}** registrado(a) com sucesso! (ID: {novo_id})")
                            st.balloons()
                        else:
                            st.warning("Preencha nome e cargo.")

            with subtab_desl:
                st.subheader("Registrar Saída")
                st.caption("Ao registrar, o sistema atualiza automaticamente: Organograma + Log + Manpower + Performance")

                ativos_desl = listar_colaboradores(status="Ativo")
                if ativos_desl:
                    nomes_ativos = {
                        f"{c['nome']} ({c['cargo_nome']} -- {c['departamento_nome']})": c["id"]
                        for c in ativos_desl
                    }
                    with st.form(f"form_saida_{_ks}"):
                        pessoa_sel = st.selectbox("Colaborador", options=list(nomes_ativos.keys()), key=f"desl_pessoa_{_ks}")
                        data_saida = st.date_input("Data de saida", value=date.today(), key=f"desl_data_{_ks}")
                        obs_saida = st.text_area("Observacao (opcional)", height=68, key=f"desl_obs_{_ks}")
                        col1_desl, col2_desl = st.columns([1, 3])
                        with col1_desl:
                            confirmar = st.checkbox("Confirmo a saída", key=f"desl_confirm_{_ks}")
                        submitted_desl = st.form_submit_button("Registrar saída", type="primary")

                        if submitted_desl:
                            if confirmar:
                                desligar(
                                    colab_id=nomes_ativos[pessoa_sel],
                                    data_saida=data_saida,
                                    observacao=obs_saida,
                                )
                                nome_simples = pessoa_sel.split(" (")[0]
                                st.success(f"Saída de **{nome_simples}** registrada com sucesso.")
                                st.rerun()
                            else:
                                st.warning("Marque a confirmacao para prosseguir.")
                else:
                    st.info("Nenhum colaborador ativo encontrado.")

            with subtab_hist:
                st.subheader("Log de Movimentações")
                historico = listar_historico()
                if historico and fd != "Todos":
                    _id_to_dept = {p["id"]: p.get("departamento_nome", "") for p in todos_ativos}
                    historico = [h for h in historico if _id_to_dept.get(h.get("colaborador_id")) == fd]
                if historico:
                    df_hist = pd.DataFrame(historico)
                    datas = pd.to_datetime(df_hist["data"], errors="coerce")
                    df_hist["data"] = datas.apply(
                        lambda val: f"{MESES_PT_ORG[val.month]}/{val.year}" if pd.notna(val) else ""
                    )
                    df_hist = df_hist[["data", "tipo", "nome", "cargo", "observacao"]]
                    df_hist.columns = ["Periodo", "Evento", "Nome", "Cargo", "Observacao"]

                    def _estilo_evento(val):
                        if val == "Entrada":
                            return "color: green; font-weight: bold"
                        return "color: red; font-weight: bold"

                    styled_hist = df_hist.style.map(_estilo_evento, subset=["Evento"])
                    renderizar_dataframe(styled_hist, use_container_width=True, hide_index=True)
                    st.caption(f"{len(df_hist)} registros")
                else:
                    st.info("Nenhum registro no historico.")


# ── Abas por departamento ─────────────────────────────────────────────────────

_opcoes_dept = ["Todos"] + [d["nome"] for d in departamentos]
_tabs_dept = st.tabs(_opcoes_dept)
for _tab_dept_widget, _dept_opt in zip(_tabs_dept, _opcoes_dept):
    with _tab_dept_widget:
        _render_views(_dept_opt)
