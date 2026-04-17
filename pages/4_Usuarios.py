from html import escape

import pandas as pd
import streamlit as st

from utils.auth import (
    PERFIS_ACESSO,
    alterar_perfil_usuario,
    alterar_status_usuario,
    criar_usuario,
    excluir_usuario,
    garantir_autenticado,
    listar_usuarios,
    obter_usuario_atual,
    redefinir_senha_usuario,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina, renderizar_dataframe


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
        border: 1px solid #E5E5EA;
        border-radius: 22px;
        padding: 16px 18px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        margin-bottom: 18px;
    }

    .user-panel {
        background: #FFFFFF;
        border: 1px solid #E5E5EA;
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        margin-bottom: 18px;
    }

    .user-panel-title {
        color: #111111;
        font-size: 22px;
        font-weight: 800;
        margin: 0;
    }

    .user-panel-sub {
        color: #6E6E73;
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
        color: #6E6E73;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 12px 10px;
        border-bottom: 1px solid #e8ddca;
        background: #f7f2e8;
    }

    .user-table td {
        padding: 14px 10px;
        border-bottom: 1px solid #E5E5EA;
        vertical-align: top;
        color: #111111;
    }

    .user-name {
        font-weight: 800;
        color: #111111;
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
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFA 100%);
        border: 1px solid #E5E5EA;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
    }

    .profile-title {
        color: #111111;
        font-size: 16px;
        font-weight: 800;
        margin: 0;
    }

    .profile-desc {
        color: #6E6E73;
        font-size: 13px;
        margin-top: 8px;
        line-height: 1.55;
    }

    @media (max-width: 768px) {
        .profile-grid {
            grid-template-columns: 1fr;
        }
        .user-table {
            font-size: 12px;
        }
        .user-table th,
        .user-table td {
            padding: 10px 8px;
        }
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
            <strong style="color:#111111;">Gestão inicial de usuários</strong>
            <div style="color:#6E6E73; font-size:13px; margin-top:4px;">
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

    st.markdown(
        """
        <div class="user-panel">
            <div class="user-panel-title">Usuários</div>
            <div class="user-panel-sub">Acesso ao portal por email e senha, com módulos base por perfil.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_usuarios = pd.DataFrame(
        [
            {
                "Nome": usuario.get("nome", "—"),
                "Email": usuario.get("email", "—"),
                "Perfil": usuario.get("perfil", "—"),
                "Status": usuario.get("status", "—"),
                "Último login": _fmt_data(usuario.get("ultimo_login")),
            }
            for usuario in usuarios
        ]
    )

    def estilo_status(valor):
        if valor == "Ativo":
            return "color: #5e8668; font-weight: 800"
        return "color: #8a6f49; font-weight: 800"

    def estilo_perfil(valor):
        if valor == "Admin":
            return "color: #8a661b; font-weight: 800"
        return "color: #4d6c57; font-weight: 800"

    styled = (
        df_usuarios.style
        .map(estilo_status, subset=["Status"])
        .map(estilo_perfil, subset=["Perfil"])
    )
    renderizar_dataframe(styled, use_container_width=True, hide_index=True)

    # ── Gerenciar usuário ──────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
    with st.expander("⚙️ Gerenciar usuário", expanded=False):
        eu = obter_usuario_atual() or {}
        opcoes = {f"{u.get('nome')} — {u.get('email')}": u for u in usuarios}
        selecionado_label = st.selectbox("Selecionar usuário", list(opcoes.keys()), key="sel_usuario")
        alvo = opcoes[selecionado_label]
        email_alvo = alvo.get("email", "")

        aba_perfil, aba_senha, aba_status, aba_excluir = st.tabs(
            ["Alterar perfil", "Redefinir senha", "Ativar / Desativar", "Excluir"]
        )

        with aba_perfil:
            perfil_atual = alvo.get("perfil", "Usuário")
            novo_perfil = st.selectbox(
                "Novo perfil",
                list(PERFIS_ACESSO.keys()),
                index=list(PERFIS_ACESSO.keys()).index(perfil_atual) if perfil_atual in PERFIS_ACESSO else 1,
                key="novo_perfil",
            )
            if st.button("Salvar perfil", key="btn_perfil", type="primary"):
                try:
                    alterar_perfil_usuario(email_alvo, novo_perfil)
                    st.success(f"Perfil de {alvo.get('nome')} alterado para {novo_perfil}.")
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))

        with aba_senha:
            nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")
            confirmar = st.text_input("Confirmar senha", type="password", key="confirmar_senha")
            if st.button("Redefinir senha", key="btn_senha", type="primary"):
                if nova_senha != confirmar:
                    st.warning("As senhas não coincidem.")
                else:
                    try:
                        redefinir_senha_usuario(email_alvo, nova_senha)
                        st.success(f"Senha de {alvo.get('nome')} redefinida.")
                    except ValueError as exc:
                        st.warning(str(exc))

        with aba_status:
            status_atual = alvo.get("status", "Ativo")
            novo_status = "Inativo" if status_atual == "Ativo" else "Ativo"
            label_btn = f"Desativar {alvo.get('nome')}" if status_atual == "Ativo" else f"Reativar {alvo.get('nome')}"
            if st.button(label_btn, key="btn_status", type="primary"):
                try:
                    alterar_status_usuario(email_alvo, novo_status)
                    st.success(f"Status de {alvo.get('nome')} alterado para {novo_status}.")
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))

        with aba_excluir:
            st.warning(f"Isso remove permanentemente o usuário **{alvo.get('nome')}** do sistema.")
            confirmacao = st.text_input("Digite EXCLUIR para confirmar", key="confirmar_excluir")
            if st.button("Excluir usuário", key="btn_excluir"):
                if confirmacao != "EXCLUIR":
                    st.warning("Digite exatamente EXCLUIR para confirmar.")
                else:
                    try:
                        excluir_usuario(email_alvo, eu.get("email", ""))
                        st.success(f"Usuário {alvo.get('nome')} excluído.")
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))

with tab_perfis:
    st.markdown(
        """
        <div class="user-panel">
            <div class="user-panel-title">Perfis de acesso</div>
            <div class="user-panel-sub">Estrutura inicial pronta para evoluir futuramente para permissões mais granulares.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    perfis = list(PERFIS_ACESSO.items())
    cols = st.columns(2)
    for idx, (perfil, dados) in enumerate(perfis):
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="profile-card">
                    <div class="profile-title">{escape(perfil)}</div>
                    <div class="profile-desc">{escape(dados["descricao"])}</div>
                    <div style="margin-top:14px;">{_render_modulos_tags(dados["modulos"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
