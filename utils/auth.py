from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime

import json as _json

import streamlit as st
import streamlit.components.v1 as _components
from streamlit_js_eval import streamlit_js_eval as _sje

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
    {
        "nome": "Mariana Strick",
        "email": "mariana.strick@3scorporate.com",
        "perfil": "Usuário",
        "senha": "mari@3s2026",
    },
]

SESSION_USER_KEY = "auth_usuario"
_QP_TOKEN        = "s"    # query param para token de sessão
_QP_EMAIL        = "e"    # query param para lembrar email

# Chaves do localStorage do browser (persistência além da URL)
_LS_TOKEN = "portal_auth_token"
_LS_EMAIL = "portal_remember_email"


def _ler_ls() -> tuple[str | None, str]:
    """Lê token e email do localStorage via streamlit_js_eval.
    Retorna (None, "") enquanto o JS ainda não executou (primeiro render).
    Retorna ("", "") se localStorage está vazio.
    """
    raw = _sje(
        js_expressions=(
            f"JSON.stringify([localStorage.getItem('{_LS_TOKEN}'),"
            f"localStorage.getItem('{_LS_EMAIL}')])"
        ),
        key="_ls_read",
        want_output=True,
    )
    if raw is None:
        return None, ""  # JS ainda não executou
    try:
        parts = _json.loads(raw)
        return parts[0] or "", parts[1] or ""
    except Exception:
        return "", ""


def _salvar_ls(token: str, email: str = "", lembrar: bool = False):
    """Salva token (e opcionalmente email) no localStorage."""
    email_js = (
        f"localStorage.setItem('{_LS_EMAIL}', {repr(str(email))});"
        if lembrar and email
        else f"localStorage.removeItem('{_LS_EMAIL}');"
    )
    _sje(
        js_expressions=(
            f"localStorage.setItem('{_LS_TOKEN}', {repr(str(token))});"
            f"{email_js} true;"
        ),
        key="_ls_save",
    )


def _limpar_ls():
    """Remove token e email do localStorage (logout)."""
    _sje(
        js_expressions=(
            f"localStorage.removeItem('{_LS_TOKEN}');"
            f"localStorage.removeItem('{_LS_EMAIL}'); true;"
        ),
        key="_ls_clear",
    )


def processar_pendencias():
    """Executa salvamentos no localStorage pendentes do ciclo de login.
    Deve ser chamado em app.py logo após confirmar que o usuário está logado.
    """
    if "_pending_ls" in st.session_state:
        token, email, lembrar = st.session_state.pop("_pending_ls")
        _salvar_ls(token, email, lembrar)


def _secret_key() -> str:
    try:
        return str(st.secrets.get("SECRET_KEY", "portal-do-gestor-2026"))
    except Exception:
        return "portal-do-gestor-2026"


def _gerar_token(email: str) -> str:
    email_b64 = base64.urlsafe_b64encode(email.encode()).decode()
    sig = hmac.new(_secret_key().encode(), email_b64.encode(), hashlib.sha256).hexdigest()
    return f"{email_b64}.{sig}"


def _validar_token(token: str) -> str | None:
    try:
        email_b64, sig = token.rsplit(".", 1)
        expected = hmac.new(_secret_key().encode(), email_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return base64.urlsafe_b64decode(email_b64).decode()
    except Exception:
        return None


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


def alterar_perfil_usuario(email: str, novo_perfil: str):
    if novo_perfil not in PERFIS_ACESSO:
        raise ValueError("Perfil inválido.")
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    row_num = encontrar_linha(ws, 3, _normalizar_email(email))
    if not row_num:
        raise ValueError("Usuário não encontrado.")
    ws.cell(row=row_num, column=4, value=novo_perfil)
    ws.cell(row=row_num, column=6, value=_serializar_modulos(None, novo_perfil))
    salvar_workbook(wb)


def redefinir_senha_usuario(email: str, nova_senha: str):
    if len(nova_senha or "") < 6:
        raise ValueError("A senha precisa ter pelo menos 6 caracteres.")
    senha_hash, senha_salt = _gerar_hash_senha(nova_senha)
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    row_num = encontrar_linha(ws, 3, _normalizar_email(email))
    if not row_num:
        raise ValueError("Usuário não encontrado.")
    ws.cell(row=row_num, column=7, value=senha_hash)
    ws.cell(row=row_num, column=8, value=senha_salt)
    salvar_workbook(wb)


def alterar_status_usuario(email: str, novo_status: str):
    if novo_status not in ("Ativo", "Inativo"):
        raise ValueError("Status inválido.")
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    row_num = encontrar_linha(ws, 3, _normalizar_email(email))
    if not row_num:
        raise ValueError("Usuário não encontrado.")
    ws.cell(row=row_num, column=5, value=novo_status)
    salvar_workbook(wb)


def excluir_usuario(email: str, email_solicitante: str):
    if _normalizar_email(email) == _normalizar_email(email_solicitante):
        raise ValueError("Não é possível excluir sua própria conta.")
    wb = carregar_workbook()
    ws = wb[SHEET_USUARIOS]
    row_num = encontrar_linha(ws, 3, _normalizar_email(email))
    if not row_num:
        raise ValueError("Usuário não encontrado.")
    ws.delete_rows(row_num)
    salvar_workbook(wb)


def iniciar_sessao(usuario: dict):
    st.session_state[SESSION_USER_KEY] = _sanitizar_usuario(usuario)
    # Token assinado no query param — sobrevive a F5 (URL mantida) e a navegação
    # entre páginas (Streamlit preserva query params no st.navigation())
    try:
        st.query_params[_QP_TOKEN] = _gerar_token(usuario["email"])
    except Exception:
        pass


def sair_sessao():
    st.session_state.pop(SESSION_USER_KEY, None)
    st.session_state["_logout"] = True
    try:
        st.query_params.clear()
    except Exception:
        pass


def restaurar_sessao():
    """Lê o query param 's' e restaura a sessão sem depender de cookies."""
    if obter_usuario_atual():
        return
    try:
        token = st.query_params.get(_QP_TOKEN)
    except Exception:
        return
    if not token:
        return
    email = _validar_token(str(token))
    if not email:
        return
    usuario = buscar_usuario_por_email(email)
    if usuario and usuario.get("status") == "Ativo":
        st.session_state[SESSION_USER_KEY] = _sanitizar_usuario(usuario)


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

        .block-container {
            padding-top: 1.2rem !important;
        }

        .login-shell {
            max-width: 560px;
            margin: 0 auto;
        }

        .login-topbar {
            background: #FFFFFF;
            border: 1px solid #E5E5EA;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            margin-bottom: 14px;
        }

        .login-topbar-title {
            color: #111111;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin: 0;
        }

        .login-topbar-sub {
            color: #6E6E73;
            font-size: 14px;
            margin-top: 6px;
            font-weight: 400;
        }

        .login-panel {
            background: #FFFFFF;
            border: 1px solid #E5E5EA;
            border-radius: 16px;
            padding: 22px 24px 24px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }

        .login-panel-title {
            color: #111111;
            font-size: 22px;
            font-weight: 700;
            margin: 0;
        }

        .login-panel-sub {
            color: #6E6E73;
            font-size: 14px;
            margin-top: 6px;
            margin-bottom: 2px;
            font-weight: 400;
        }

        .login-mini {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 0.36rem 0.7rem;
            background: #F2F2F7;
            border: 1px solid #E5E5EA;
            color: #6E6E73;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }

        /* centraliza o form nativo do Streamlit */
        [data-testid="stForm"] {
            max-width: 420px;
            margin: 0 auto;
        }

        @media (max-width: 768px) {
            .login-shell {
                max-width: 100%;
                padding: 0 0.25rem;
            }
            .login-topbar,
            .login-panel {
                border-radius: 18px;
                padding: 16px 16px;
            }
            .login-topbar-title {
                font-size: 22px;
            }
            [data-testid="stForm"] {
                max-width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-shell">
            <div class="login-topbar">
                <div class="login-mini">Acesso restrito</div>
                <div class="login-topbar-title">Portal do Gestor</div>
                <div class="login-topbar-sub">Entre com seu email e senha.</div>
            </div>
            <div class="login-panel">
                <div class="login-panel-title">Login</div>
                <div class="login-panel-sub">Use seu acesso cadastrado.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Logout: limpar localStorage
    if st.session_state.pop("_logout", False):
        _limpar_ls()
        ls_token, ls_email = "", ""
    else:
        # Ler localStorage — primeiro render retorna (None, ""), aguardar
        ls_token, ls_email = _ler_ls()

        if ls_token is None:
            # JS ainda não executou: mostrar loading e aguardar rerun automático
            st.markdown(
                "<div style='text-align:center;padding:4rem;color:#6f7a84;"
                "font-size:1rem;font-weight:500;'>Carregando...</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        if ls_token:
            # Tentar restaurar sessão automaticamente
            email_from_token = _validar_token(str(ls_token))
            if email_from_token:
                usuario = buscar_usuario_por_email(email_from_token)
                if usuario and usuario.get("status") == "Ativo":
                    st.session_state[SESSION_USER_KEY] = _sanitizar_usuario(usuario)
                    st.rerun()
                    return
            # Token inválido ou usuário inativo: limpar
            _limpar_ls()
            ls_token, ls_email = "", ""

    with st.form("form_login"):
        email = st.text_input("Email", value=ls_email, placeholder="voce@empresa.com")
        senha = st.text_input("Senha", type="password")
        col_check, col_btn = st.columns([1, 1])
        with col_check:
            lembrar = st.checkbox("Lembrar email", value=bool(ls_email))
        with col_btn:
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if submitted:
        usuario = autenticar_usuario(email, senha)
        if usuario:
            iniciar_sessao(usuario)
            registrar_login(usuario["email"])
            token = _gerar_token(usuario["email"])
            # Salva no localStorage no próximo render (evita race condition com st.rerun)
            st.session_state["_pending_ls"] = (token, _normalizar_email(email), lembrar)
            st.rerun()
        st.error("Email ou senha inválidos.")


def renderizar_usuario_sidebar():
    usuario = obter_usuario_atual()
    if not usuario:
        return

    dark = st.session_state.get("dark_mode", False)
    if dark:
        card_bg = "#161b22"
        card_border = "#30363d"
        card_shadow = "0 2px 10px rgba(0, 0, 0, 0.2)"
        label_color = "#8b949e"
        name_color = "#c9d6e0"
        email_color = "#8b949e"
        badge_bg = "rgba(255, 255, 255, 0.08)"
        badge_border = "rgba(255, 255, 255, 0.1)"
        badge_color = "#e6e6e6"
    else:
        card_bg = "#FFFFFF"
        card_border = "#E5E5EA"
        card_shadow = "0 2px 10px rgba(0, 0, 0, 0.04)"
        label_color = "#6E6E73"
        name_color = "#111111"
        email_color = "#6E6E73"
        badge_bg = "#F2F2F7"
        badge_border = "#E5E5EA"
        badge_color = "#6E6E73"

    st.sidebar.markdown(
        f"""
        <div style="
            background: {card_bg};
            border: 1px solid {card_border};
            border-radius: 16px;
            padding: 12px 12px 10px;
            margin-bottom: 12px;
            box-shadow: {card_shadow};
        ">
            <div style="font-size:12px; color:{label_color}; text-transform:uppercase; letter-spacing:.08em; font-weight:800;">Sessão ativa</div>
            <div style="margin-top:6px; font-size:16px; color:{name_color}; font-weight:800;">{usuario.get("nome", "Usuário")}</div>
            <div style="margin-top:2px; font-size:12px; color:{email_color};">{usuario.get("email", "")}</div>
            <div style="margin-top:10px; display:inline-flex; border-radius:999px; padding:6px 10px; background:{badge_bg}; border:1px solid {badge_border}; color:{badge_color}; font-size:11px; font-weight:800;">
                {usuario.get("perfil", "Usuário")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Sair", use_container_width=True):
        sair_sessao()
        st.rerun()
