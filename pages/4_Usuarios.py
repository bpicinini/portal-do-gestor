from html import escape

import pandas as pd
import streamlit as st

from utils.auth import PERFIS_ACESSO, criar_usuario, garantir_autenticado, listar_usuarios
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


def _fmt_data(valor):
    if valor in (None, "", "None"):
        return "Nunca"
    try:
        dt = pd.to_datetime(valor)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(valor)


def _render_modulos_tags(modulos):
    return "".join(f'<span class="user-tag">{escape(str(modulo))}</span>' for modulo in modulos)


garantir_autenticado(admin=True)
aplicar_estilos_globais()
renderizar_cabecalho_pagina(
    "Usuários",
    "Controle inicial de acessos do portal, com login por email e senha e perfis prontos para evolucao.",
    badge="Acesso protegido",
    pills=["Login individual", "Admin e Usuário", "Cadastro inicial"],
)

st.markdown(
    """
    <style>
    .user-toolbar {
        background: linear-gradient(135deg, rgba(255,253,248,0.98) 0%, rgba(243,237,226,0.95) 100%);
        border: 1px solid #e3d8c5;
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        margin-bottom: 18px;
    }

    .user-panel {
        background: #fffdf8;
        border: 1px solid #e3d8c5;
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        margin-bottom: 18px;
    }

    .user-panel-title {
        color: #234055;
        font-size: 22px;
        font-weight: 800;
        margin: 0;
    }

    .user-panel-sub {
        color: #6f7a84;
        font-size: 13px;
        margin-top: 4px;
    }

    .user-table-wrap {
        overflow-x: auto;
        margin-top: 14px;
    }

    .user-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    .user-table th {
        text-align: left;
        color: #6f7a84;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 12px 10px;
        border-bottom: 1px solid #e8ddca;
        background: #f7f2e8;
    }

    .user-table td {
        padding: 14px 10px;
        border-bottom: 1px solid #efe7da;
        vertical-align: top;
        color: #223645;
    }

    .user-name {
        font-weight: 800;
        color: #234055;
    }

    .user-email {
        color: #5d6973;
    }

    .user-role {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.3rem 0.65rem;
        font-size: 11px;
        font-weight: 800;
        border: 1px solid #d7c39b;
        background: #f7ecd0;
        color: #8a661b;
    }

    .user-role.user {
        background: #edf4ef;
        border-color: #d7e2da;
        color: #4d6c57;
    }

    .user-status {
        font-weight: 800;
        color: #5e8668;
    }

    .user-status.inativo {
        color: #8a6f49;
    }

    .user-tag {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.22rem 0.52rem;
        margin: 0 0.3rem 0.3rem 0;
        font-size: 10px;
        font-weight: 800;
        background: #f6ecda;
        border: 1px solid #e8d7b6;
        color: #6f5520;
    }

    .profile-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 14px;
        margin-top: 14px;
    }

    .profile-card {
        background: linear-gradient(180deg, #fffdf8 0%, #f5eee2 100%);
        border: 1px solid #e3d8c5;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
    }

    .profile-title {
        color: #234055;
        font-size: 16px;
        font-weight: 800;
        margin: 0;
    }

    .profile-desc {
        color: #6f7a84;
        font-size: 13px;
        margin-top: 8px;
        line-height: 1.55;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

usuarios = listar_usuarios()
usuarios_ativos = [usuario for usuario in usuarios if usuario.get("status") == "Ativo"]
admins = [usuario for usuario in usuarios if usuario.get("perfil") == "Admin"]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Usuários cadastrados", len(usuarios))
with c2:
    st.metric("Ativos", len(usuarios_ativos))
with c3:
    st.metric("Admins", len(admins))

tab_usuarios, tab_perfis = st.tabs(["Usuários", "Perfis de acesso"])

with tab_usuarios:
    st.markdown(
        """
        <div class="user-toolbar">
            <strong style="color:#234055;">Gestão inicial de usuários</strong>
            <div style="color:#6f7a84; font-size:13px; margin-top:4px;">
                Nesta primeira etapa, o portal já exige login e senha e permite cadastrar novos acessos manualmente.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("+ Novo Usuário", expanded=False):
        with st.form("form_novo_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome")
                email = st.text_input("Email")
            with col2:
                perfil = st.selectbox("Perfil", list(PERFIS_ACESSO.keys()))
                senha = st.text_input("Senha inicial", type="password")

            confirmar_senha = st.text_input("Confirmar senha", type="password")
            submitted = st.form_submit_button("Cadastrar usuário", type="primary")

            if submitted:
                if senha != confirmar_senha:
                    st.warning("As senhas nao coincidem.")
                else:
                    try:
                        novo_id = criar_usuario(nome, email, perfil, senha)
                        st.success(f"Usuário cadastrado com sucesso. ID: {novo_id}")
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))

    rows_html = []
    for usuario in usuarios:
        perfil_class = "user" if usuario.get("perfil") == "Usuário" else ""
        status_class = "inativo" if usuario.get("status") != "Ativo" else ""
        rows_html.append(
            f"""
            <tr>
                <td>
                    <div class="user-name">{escape(str(usuario.get("nome", "—")))}</div>
                </td>
                <td>
                    <div class="user-email">{escape(str(usuario.get("email", "—")))}</div>
                </td>
                <td>
                    <span class="user-role {perfil_class}">{escape(str(usuario.get("perfil", "—")))}</span>
                </td>
                <td>
                    {_render_modulos_tags(usuario.get("modulos", []))}
                </td>
                <td>
                    <span class="user-status {status_class}">{escape(str(usuario.get("status", "—")))}</span>
                </td>
                <td>{escape(_fmt_data(usuario.get("ultimo_login")))}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <div class="user-panel">
            <div class="user-panel-title">Usuários</div>
            <div class="user-panel-sub">Acesso ao portal por email e senha, com módulos base por perfil.</div>
            <div class="user-table-wrap">
                <table class="user-table">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Email</th>
                            <th>Perfil</th>
                            <th>Módulos</th>
                            <th>Status</th>
                            <th>Último login</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_perfis:
    cards_html = []
    for perfil, dados in PERFIS_ACESSO.items():
        cards_html.append(
            f"""
            <div class="profile-card">
                <div class="profile-title">{escape(perfil)}</div>
                <div class="profile-desc">{escape(dados["descricao"])}</div>
                <div style="margin-top:14px;">{_render_modulos_tags(dados["modulos"])}</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="user-panel">
            <div class="user-panel-title">Perfis de acesso</div>
            <div class="user-panel-sub">Estrutura inicial pronta para evoluir futuramente para permissões mais granulares.</div>
            <div class="profile-grid">
                {"".join(cards_html)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
