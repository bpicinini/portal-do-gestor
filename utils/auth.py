from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime

import streamlit as st

from utils.excel_io import (
    SHEET_USUARIOS,
    carregar_workbook,
    encontrar_linha,
    proximo_id,
    salvar_workbook,
    sheet_to_list,
)
from utils.ui import aplicar_estilos_globais


PERFIS_ACESSO = {
    "Admin": {
        "descricao": "Acesso total ao portal, incluindo cadastro de usuarios e configuracoes operacionais.",
        "modulos": ["Home", "Organograma", "KPIs", "Controle de Pessoas", "Usuarios"],
    },
    "Usuário": {
        "descricao": "Acesso operacional ao portal com consulta e uso das areas principais.",
        "modulos": ["Home", "Organograma", "KPIs", "Controle de Pessoas"],
    },
}

USUARIOS_INICIAIS = [
    {
        "nome": "Bruno Picinini",
        "email": "bruno.picinini@3scorporate.com",
        "perfil": "Admin",
        "senha": "luga2015@bp",
    },
    {
        "nome": "Gabriel Spohr",
        "email": "gabriel.spohr@3scorporate.com",
        "perfil": "Usuário",
        "senha": "3s@2026",
    },
    {
        "nome": "Celso Petry",
        "email": "celso.petry@3scorporate.com",
        "perfil": "Usuário",
        "senha": "3s@2026",
    },
    {
        "nome": "Patrice Basso",
        "email": "patrice.basso@3scorporate.com",
        "perfil": "Usuário",
        "senha": "3s@2026",
    },
    {
        "nome": "Gabriel Hilgert",
        "email": "gabriel.hilgert@leaderlog.com.br",
        "perfil": "Usuário",
        "senha": "3s@2026",
    },
]

SESSION_USER_KEY = "auth_usuario"


def _normalizar_email(email: str | None) -> str:
    return str(email or "").strip().lower()


def _modulos_por_perfil(perfil: str) -> list[str]:
    return PERFIS_ACESSO.get(perfil, PERFIS_ACESSO["Usuário"])["modulos"][:]


def _gerar_hash_senha(senha: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 240000)
    return digest.hex(), salt.hex()


def _senha_confere(senha: str, senha_hash: str, senha_salt: str) -> bool:
    digest, _ = _gerar_hash_senha(senha, senha_salt)
    return hmac.compare_digest(digest, str(senha_hash or ""))


def _parse_modulos(modulos):
    if isinstance(modulos, (list, tuple)):
        return [str(item).strip() for item in modulos if str(item).strip()]
    return [parte.strip() for parte in str(modulos or "").split("|") if parte.strip()]


def _serializar_modulos(modulos: list[str] | None, perfil: str) -> str:
    base = modulos or _modulos_por_perfil(perfil)
    return "|".join(base)


def _sanitizar_usuario(usuario: dict) -> dict:
    user = dict(usuario)
    user["email"] = _normalizar_email(user.get("email"))
    user["modulos"] = _parse_modulos(user.get("modulos"))
    user.pop("senha_hash", None)
    user.pop("senha_salt", None)
    return user


def seed_usuarios_iniciais():
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    usuarios_existentes = sheet_to_list(ws)
    emails_existentes = {_normalizar_email(usuario.get("email")) for usuario in usuarios_existentes}
    alterou = False

    for usuario in USUARIOS_INICIAIS:
        email = _normalizar_email(usuario["email"])
        if email in emails_existentes:
            continue

        senha_hash, senha_salt = _gerar_hash_senha(usuario["senha"])
        ws.append(
            [
                proximo_id(ws),
                usuario["nome"],
                email,
                usuario["perfil"],
                "Ativo",
                _serializar_modulos(None, usuario["perfil"]),
                senha_hash,
                senha_salt,
                None,
                datetime.now(),
            ]
        )
        emails_existentes.add(email)
        alterou = True

    if alterou:
        salvar_workbook(wb)


def listar_usuarios(apenas_ativos: bool = False) -> list[dict]:
    seed_usuarios_iniciais()
    wb = carregar_workbook()
    usuarios = [_sanitizar_usuario(usuario) for usuario in sheet_to_list(wb[SHEET_USUARIOS])]
    usuarios.sort(key=lambda item: (_normalizar_email(item.get("email")), item.get("nome", "")))
    if apenas_ativos:
        usuarios = [usuario for usuario in usuarios if usuario.get("status") == "Ativo"]
    return usuarios


def buscar_usuario_por_email(email: str) -> dict | None:
    email_norm = _normalizar_email(email)
    if not email_norm:
        return None

    seed_usuarios_iniciais()
    wb = carregar_workbook()
    for usuario in sheet_to_list(wb[SHEET_USUARIOS]):
        if _normalizar_email(usuario.get("email")) == email_norm:
            return usuario
    return None


def autenticar_usuario(email: str, senha: str) -> dict | None:
    usuario = buscar_usuario_por_email(email)
    if not usuario or usuario.get("status") != "Ativo":
        return None

    if not _senha_confere(senha, usuario.get("senha_hash"), usuario.get("senha_salt")):
        return None

    return _sanitizar_usuario(usuario)


def registrar_login(email: str):
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    usuario = buscar_usuario_por_email(email)
    if not usuario:
        return

    row_num = encontrar_linha(ws, 3, _normalizar_email(email))
    if row_num:
        ws.cell(row=row_num, column=9, value=datetime.now())
        salvar_workbook(wb)


def criar_usuario(nome: str, email: str, perfil: str, senha: str, status: str = "Ativo"):
    email_norm = _normalizar_email(email)
    if not nome.strip():
        raise ValueError("Informe o nome do usuario.")
    if not email_norm:
        raise ValueError("Informe um email valido.")
    if buscar_usuario_por_email(email_norm):
        raise ValueError("Ja existe um usuario cadastrado com esse email.")
    if perfil not in PERFIS_ACESSO:
        raise ValueError("Perfil de acesso invalido.")
    if len(senha or "") < 6:
        raise ValueError("A senha precisa ter pelo menos 6 caracteres.")

    senha_hash, senha_salt = _gerar_hash_senha(senha)
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    novo_id = proximo_id(ws)
    ws.append(
        [
            novo_id,
            nome.strip(),
            email_norm,
            perfil,
            status,
            _serializar_modulos(None, perfil),
            senha_hash,
            senha_salt,
            None,
            datetime.now(),
        ]
    )
    salvar_workbook(wb)
    return novo_id


def iniciar_sessao(usuario: dict):
    st.session_state[SESSION_USER_KEY] = _sanitizar_usuario(usuario)


def sair_sessao():
    st.session_state.pop(SESSION_USER_KEY, None)


def obter_usuario_atual() -> dict | None:
    usuario = st.session_state.get(SESSION_USER_KEY)
    if not usuario:
        return None
    return _sanitizar_usuario(usuario)


def usuario_admin() -> bool:
    usuario = obter_usuario_atual()
    return bool(usuario and usuario.get("perfil") == "Admin")


def garantir_autenticado(admin: bool = False) -> dict:
    usuario = obter_usuario_atual()
    if not usuario:
        st.warning("Acesso protegido. Faça login para continuar.")
        st.stop()
    if admin and usuario.get("perfil") != "Admin":
        st.error("Esta área é restrita a administradores.")
        st.stop()
    return usuario


def renderizar_login():
    aplicar_estilos_globais()
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        .login-layout {
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 24px;
            min-height: calc(100vh - 110px);
        }

        .login-brand {
            background: linear-gradient(180deg, #fcfaf5 0%, #f4ecdf 100%);
            border: 1px solid #e3d8c5;
            border-radius: 28px;
            padding: 28px 22px;
            box-shadow: 0 18px 40px rgba(35, 64, 85, 0.08);
        }

        .login-brand-mark {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-size: 28px;
            font-weight: 800;
            color: #234055;
            letter-spacing: -0.03em;
        }

        .login-brand-sub {
            margin-top: 16px;
            color: #6f7a84;
            font-size: 14px;
            line-height: 1.6;
        }

        .login-brand-stack {
            margin-top: 26px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .login-brand-pill {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid #e3d8c5;
            color: #36586f;
            border-radius: 16px;
            padding: 12px 14px;
            font-size: 13px;
            font-weight: 700;
        }

        .login-main {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .login-topbar {
            background: linear-gradient(135deg, rgba(255,253,248,0.98) 0%, rgba(243,237,226,0.95) 100%);
            border: 1px solid #e3d8c5;
            border-radius: 24px;
            padding: 22px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 18px 40px rgba(35, 64, 85, 0.08);
        }

        .login-topbar-title {
            color: #234055;
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin: 0;
        }

        .login-topbar-sub {
            color: #6f7a84;
            font-size: 14px;
            margin-top: 6px;
        }

        .login-status {
            border-radius: 999px;
            padding: 10px 16px;
            background: linear-gradient(135deg, #e3f0de 0%, #eff8ea 100%);
            border: 1px solid #cddfc8;
            color: #5e8668;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .login-panel {
            background: #fffdf8;
            border: 1px solid #e3d8c5;
            border-radius: 28px;
            padding: 26px 24px;
            box-shadow: 0 18px 40px rgba(35, 64, 85, 0.08);
        }

        .login-panel-title {
            color: #234055;
            font-size: 24px;
            font-weight: 800;
            margin: 0;
        }

        .login-panel-sub {
            color: #6f7a84;
            font-size: 14px;
            margin-top: 6px;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-layout">
            <div class="login-brand">
                <div class="login-brand-mark">3S <span style="color:#c79536;">Portal</span></div>
                <div class="login-brand-sub">
                    Acesso protegido ao Portal do Gestor, com login individual e trilha inicial de controle de usuários.
                </div>
                <div class="login-brand-stack">
                    <div class="login-brand-pill">Login com email corporativo</div>
                    <div class="login-brand-pill">Perfis Admin e Usuário</div>
                    <div class="login-brand-pill">Base inicial pronta para evolução</div>
                </div>
            </div>
            <div class="login-main">
                <div class="login-topbar">
                    <div>
                        <div class="login-topbar-title">Acesso ao Portal</div>
                        <div class="login-topbar-sub">Faça login para entrar no ambiente de gestão da operação.</div>
                    </div>
                    <div class="login-status">Acesso restrito</div>
                </div>
                <div class="login-panel">
                    <div class="login-panel-title">Login e senha</div>
                    <div class="login-panel-sub">Somente usuários cadastrados conseguem acessar o portal.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_col, info_col = st.columns([1.25, 1], gap="large")
    with login_col:
        with st.form("form_login"):
            email = st.text_input("Email", placeholder="voce@empresa.com")
            senha = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submitted:
            usuario = autenticar_usuario(email, senha)
            if usuario:
                iniciar_sessao(usuario)
                registrar_login(usuario["email"])
                st.rerun()
            st.error("Email ou senha inválidos.")

    with info_col:
        st.info("Os acessos iniciais já estão cadastrados e podem ser gerenciados por um perfil Admin.")


def renderizar_usuario_sidebar():
    usuario = obter_usuario_atual()
    if not usuario:
        return

    st.sidebar.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,253,248,0.98) 0%, rgba(243,237,226,0.95) 100%);
            border: 1px solid #e3d8c5;
            border-radius: 20px;
            padding: 14px 14px 12px;
            margin-bottom: 14px;
            box-shadow: 0 14px 35px rgba(35, 64, 85, 0.08);
        ">
            <div style="font-size:12px; color:#6f7a84; text-transform:uppercase; letter-spacing:.08em; font-weight:800;">Sessão ativa</div>
            <div style="margin-top:6px; font-size:16px; color:#234055; font-weight:800;">{usuario.get("nome", "Usuário")}</div>
            <div style="margin-top:2px; font-size:12px; color:#6f7a84;">{usuario.get("email", "")}</div>
            <div style="margin-top:10px; display:inline-flex; border-radius:999px; padding:6px 10px; background:#eef5f0; border:1px solid #d9e7de; color:#36586f; font-size:11px; font-weight:800;">
                {usuario.get("perfil", "Usuário")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Sair", use_container_width=True):
        sair_sessao()
        st.rerun()
