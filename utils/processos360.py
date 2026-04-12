"""Lógica de negócio para a aba Processos 360.

Responsável por: parsing do CSV, validação, cálculo de alertas,
upload/backup e metadados.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_BACKUP_DIR = _DATA_DIR / "backups"
_CSV_PATH = _DATA_DIR / "processos_360.csv"
_META_PATH = _DATA_DIR / "processos_360_meta.json"

STATUS_ORDEM = [
    "Pré-embarque",
    "Embarque",
    "Chegada",
    "Registrado/Ag.Desembaraço",
    "Carregamento",
    "Encerramento",
]

COLUNAS_OBRIGATORIAS = ["Status", "Processo", "Account", "Cliente"]

COLUNAS_MOEDA = ["Saldo", "Valor Aduaneiro", "Numerário"]

COLUNAS_DATA = [
    "Abertura",
    "Data do Follow",
    "Prev. de embarque",
    "Conf. de embarque",
    "Prev. Chegada",
    "Conf. Chegada",
    "Prev. Chegada Final",
    "Conf. Chegada Final",
    "Presença de Carga",
    "Recebido Original",
    "Registro LI",
    "LPCO Data",
    "Previsão de registro",
    "Registro da DI",
    "Desembaraço",
    "Liberação siscarga",
    "Prev. de Carregamento",
    "Conf. Carregamento",
    "Liberado p/ faturamento",
    "Faturamento",
    "Limite Dev. Container",
    "Devolução do container",
    "Limite para Perdimento",
    "Encerramento Operacional",
]

COLUNAS_NUMERICAS = ["Adições", "Qtd. Container", "Free-time"]


# ── Helpers ──────────────────────────────────────────────────────────


def _parse_moeda(val):
    """Converte 'R$ 1.237.566,22' ou '-R$ 39,94' para float."""
    if pd.isna(val) or str(val).strip() == "":
        return None
    s = str(val).replace("R$", "").replace("\xa0", "").strip()
    negativo = s.startswith("-")
    s = s.lstrip("-").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        resultado = float(s)
        return -resultado if negativo else resultado
    except ValueError:
        return None


def _parse_datas(series: pd.Series) -> pd.Series:
    """Parseia séries com formatos mistos DD/MM/YYYY e DD/MM/YY."""
    parsed = pd.to_datetime(series, dayfirst=True, format="mixed", errors="coerce")
    mask = parsed.notna() & ((parsed.dt.year < 2000) | (parsed.dt.year > 2050))
    parsed[mask] = pd.NaT
    return parsed


def _br(val, dec=2):
    """Formata número para padrão brasileiro."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _br_moeda(val, dec=2):
    """Formata como moeda brasileira R$."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"R$ {_br(val, dec)}"


# ── Carregamento e parsing ───────────────────────────────────────────


def dados_existem() -> bool:
    """Verifica se o arquivo de dados existe."""
    return _CSV_PATH.exists()


def _mtime() -> float:
    """Retorna o mtime do CSV ou 0 se não existir."""
    try:
        return os.path.getmtime(_CSV_PATH)
    except OSError:
        return 0


@st.cache_data(show_spinner="Carregando processos...", ttl=300)
def carregar_processos(_mtime_key: float = 0) -> pd.DataFrame:
    """Lê e parseia o CSV de processos."""
    if not _CSV_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(_CSV_PATH, encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()

    # Dropar coluna duplicada
    if "pQuatAdicoes1" in df.columns:
        df = df.drop(columns=["pQuatAdicoes1"])

    # Strip em colunas string
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Parsear moeda
    for col in COLUNAS_MOEDA:
        if col in df.columns:
            df[col] = df[col].apply(_parse_moeda)

    # Parsear datas
    for col in COLUNAS_DATA:
        if col in df.columns:
            df[col] = _parse_datas(df[col])

    # Parsear numéricos
    for col in COLUNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def obter_processos() -> pd.DataFrame:
    """Wrapper que passa o mtime atual para bust do cache."""
    return carregar_processos(_mtime_key=_mtime())


# ── Validação ────────────────────────────────────────────────────────


def validar_csv(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Valida o DataFrame do CSV. Retorna (válido, avisos)."""
    avisos = []

    colunas_faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if colunas_faltantes:
        return False, [f"Colunas obrigatórias ausentes: {', '.join(colunas_faltantes)}"]

    if len(df) == 0:
        return False, ["O arquivo não contém registros."]

    if "Status" in df.columns:
        status_validos = set(STATUS_ORDEM)
        status_encontrados = set(df["Status"].dropna().unique())
        desconhecidos = status_encontrados - status_validos
        if desconhecidos:
            avisos.append(f"Status não reconhecidos: {', '.join(desconhecidos)}")

    return True, avisos


# ── Upload e backup ──────────────────────────────────────────────────


def salvar_upload(uploaded_file) -> tuple[int, list[str]]:
    """Processa upload: salva CSV, cria backup, atualiza meta."""
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    conteudo = uploaded_file.getvalue()
    df_test = pd.read_csv(
        uploaded_file, encoding="utf-8-sig", dtype=str, nrows=5
    )
    uploaded_file.seek(0)

    df_full = pd.read_csv(uploaded_file, encoding="utf-8-sig", dtype=str)
    uploaded_file.seek(0)

    valido, avisos = validar_csv(df_full)
    if not valido:
        return 0, avisos

    # Salvar arquivo principal
    with open(_CSV_PATH, "wb") as f:
        f.write(conteudo)

    # Backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = _BACKUP_DIR / f"processos_360_{ts}.csv"
    shutil.copy2(_CSV_PATH, backup_path)

    # Metadados
    meta = {
        "ultimo_upload": datetime.now().isoformat(),
        "arquivo_original": uploaded_file.name,
        "total_registros": len(df_full),
    }
    with open(_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Limpar cache
    carregar_processos.clear()

    return len(df_full), avisos


def carregar_meta() -> dict | None:
    """Carrega metadados do último upload."""
    if not _META_PATH.exists():
        return None
    with open(_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_backups() -> list[dict]:
    """Lista backups disponíveis, mais recente primeiro."""
    if not _BACKUP_DIR.exists():
        return []
    backups = []
    for arquivo in sorted(_BACKUP_DIR.glob("processos_360_*.csv"), reverse=True):
        stat = arquivo.stat()
        backups.append({
            "nome": arquivo.name,
            "caminho": arquivo,
            "tamanho": stat.st_size,
            "data": datetime.fromtimestamp(stat.st_mtime),
        })
    return backups


# ── Alertas ──────────────────────────────────────────────────────────


def calcular_alertas(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calcula todos os alertas e retorna dict com DataFrames filtrados."""
    hoje = pd.Timestamp.now().normalize()
    alertas = {}

    # 1. Saldo negativo (apenas abaixo de -R$ 1.000)
    if "Saldo" in df.columns:
        mask = df["Saldo"].notna() & (df["Saldo"] <= -1000)
        alertas["saldo_negativo"] = df[mask].copy()
    else:
        alertas["saldo_negativo"] = pd.DataFrame()

    # 2. Valor aduaneiro alto (>R$1M)
    if "Valor Aduaneiro" in df.columns:
        mask = df["Valor Aduaneiro"].notna() & (df["Valor Aduaneiro"] > 1_000_000)
        alertas["valor_alto"] = df[mask].copy()
    else:
        alertas["valor_alto"] = pd.DataFrame()

    # 3. Follow-up desatualizado (>10 dias, exceto Encerramento)
    if "Data do Follow" in df.columns:
        dias_sem_follow = (hoje - df["Data do Follow"]).dt.days
        mask = (
            dias_sem_follow.notna()
            & (dias_sem_follow > 10)
            & (df["Status"] != "Encerramento")
        )
        resultado = df[mask].copy()
        resultado["Dias sem Follow"] = dias_sem_follow[mask].astype(int)
        alertas["follow_desatualizado"] = resultado
    else:
        alertas["follow_desatualizado"] = pd.DataFrame()

    # 4a. Container VENCIDO (data limite já passou, sem devolução registrada)
    if "Limite Dev. Container" in df.columns:
        dias_restantes = (df["Limite Dev. Container"] - hoje).dt.days
        # Vencido: data limite passou E sem devolução registrada
        mask_vencido = dias_restantes.notna() & (dias_restantes < 0)
        if "Devolução do container" in df.columns:
            mask_vencido = mask_vencido & df["Devolução do container"].isna()
        resultado_vencido = df[mask_vencido].copy()
        resultado_vencido["Dias Vencido"] = (-dias_restantes[mask_vencido]).astype(int)
        alertas["container_vencido"] = resultado_vencido
    else:
        alertas["container_vencido"] = pd.DataFrame()

    # 4b. Container vencendo (<= 5 dias)
    if "Limite Dev. Container" in df.columns:
        mask = dias_restantes.notna() & (dias_restantes >= 0) & (dias_restantes <= 5)
        resultado = df[mask].copy()
        resultado["Dias Restantes"] = dias_restantes[mask].astype(int)
        alertas["container_vencendo"] = resultado
    else:
        alertas["container_vencendo"] = pd.DataFrame()

    # 5. Perdimento próximo (<= 10 dias)
    if "Limite para Perdimento" in df.columns:
        dias_restantes = (df["Limite para Perdimento"] - hoje).dt.days
        mask = dias_restantes.notna() & (dias_restantes >= 0) & (dias_restantes <= 10)
        resultado = df[mask].copy()
        resultado["Dias Restantes"] = dias_restantes[mask].astype(int)
        alertas["perdimento_proximo"] = resultado
    else:
        alertas["perdimento_proximo"] = pd.DataFrame()

    # 6. Canal vermelho e Canal amarelo
    if "Canal" in df.columns:
        canal_lower = df["Canal"].str.strip().str.lower()
        alertas["canal_vermelho"] = df[canal_lower == "vermelho"].copy()
        alertas["canal_amarelo"]  = df[canal_lower == "amarelo"].copy()
    else:
        alertas["canal_vermelho"] = pd.DataFrame()
        alertas["canal_amarelo"]  = pd.DataFrame()

    # 7. LI/LPCO indeferida
    if "Situação" in df.columns:
        mask = df["Situação"].fillna("").str.lower().str.contains("indeferid")
        alertas["li_indeferida"] = df[mask].copy()
    else:
        alertas["li_indeferida"] = pd.DataFrame()

    return alertas
