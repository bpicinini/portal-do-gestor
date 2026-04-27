"""Lógica de negócio para Exportação: Visão 360 (CSV) e KPIs de Embarcados (XLSX)."""

from __future__ import annotations

import json
import os
import shutil
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.excel_io import github_persist

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_BACKUP_DIR = _DATA_DIR / "backups"
_CSV_360_PATH = _DATA_DIR / "exportacao_360.csv"
_XLSX_EMB_PATH = _DATA_DIR / "exportacao_embarcados.xlsx"
_META_360_PATH = _DATA_DIR / "exportacao_360_meta.json"
_META_EMB_PATH = _DATA_DIR / "exportacao_emb_meta.json"

STATUS_ORDEM_EXP = [
    "Ag.Instruções",
    "Pré-Embarque",
    "Embarque",
    "Ag.Desembaraço",
    "Sem etapa",
]

COLUNAS_OBRIGATORIAS_360 = [
    "Processo", "Status", "Account Responsável", "Cliente", "Tipo", "Modalidade",
]

COLUNAS_OBRIGATORIAS_EMB = [
    "Processo", "Account", "Classificação", "Modal", "DT Abertura",
]

COLUNAS_DATA_360 = [
    "Data do follow",
    "Dead Draft", "Dead Draft Confirmado",
    "Dead Carga", "Dead Carga Confirmada",
    "Dead VGM", "VGM Confirmado",
    "Data Liberação Da DUE",
    "Previsão de embarque", "Data de embarque",
    "Envio de documentos",
    "Data de Registro DUE", "Data averbação",
    "Prev. Transbordo", "Chegada Transbordo",
    "Liberado p/ faturamento", "Data de faturamento",
]

COLUNAS_DATA_EMB = [
    "DT Abertura", "DT Encer.", "DT DUE",
    "DT Liberação", "DT Embarque", "DT Lib. Fat.", "DT Fat.",
]

PESOS: dict[str, float] = {
    "Desembaraço": 2.0,
    "Frete": 1.0,
    "Documentos": 0.5,
}


# ── Helpers internos ─────────────────────────────────────────────────


def _parse_datas(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, dayfirst=True, format="mixed", errors="coerce")
    mask = parsed.notna() & ((parsed.dt.year < 2000) | (parsed.dt.year > 2050))
    parsed[mask] = pd.NaT
    return parsed


def _mtime_360() -> float:
    try:
        return os.path.getmtime(_CSV_360_PATH)
    except OSError:
        return 0.0


def _mtime_emb() -> float:
    try:
        return os.path.getmtime(_XLSX_EMB_PATH)
    except OSError:
        return 0.0


# ══════════════════════════════════════════════════════════════════════
# VISÃO 360 — CSV
# ══════════════════════════════════════════════════════════════════════


def dados_360_existem() -> bool:
    return _CSV_360_PATH.exists()


@st.cache_data(show_spinner="Carregando processos de exportação...", ttl=300)
def _carregar_360(_mtime_key: float = 0) -> pd.DataFrame:
    if not _CSV_360_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(_CSV_360_PATH, encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()

    # Remover coluna duplicada gerada pelo sistema
    if "Liberado p/ faturamento.1" in df.columns:
        df = df.drop(columns=["Liberado p/ faturamento.1"])

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    for col in COLUNAS_DATA_360:
        if col in df.columns:
            df[col] = _parse_datas(df[col])

    return df


def obter_processos_360() -> pd.DataFrame:
    return _carregar_360(_mtime_key=_mtime_360())


def validar_360_csv(df: pd.DataFrame) -> tuple[bool, list[str]]:
    avisos: list[str] = []
    faltantes = [c for c in COLUNAS_OBRIGATORIAS_360 if c not in df.columns]
    if faltantes:
        return False, [f"Colunas obrigatórias ausentes: {', '.join(faltantes)}"]
    if len(df) == 0:
        return False, ["O arquivo não contém registros."]
    desconhecidos = set(df["Status"].dropna().unique()) - set(STATUS_ORDEM_EXP)
    if desconhecidos:
        avisos.append(f"Status não reconhecidos (serão exibidos sem cor): {', '.join(desconhecidos)}")
    return True, avisos


def salvar_upload_360(uploaded_file) -> tuple[int, list[str]]:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    conteudo = uploaded_file.getvalue()
    uploaded_file.seek(0)
    df_full = pd.read_csv(uploaded_file, encoding="utf-8-sig", dtype=str)
    uploaded_file.seek(0)

    valido, avisos = validar_360_csv(df_full)
    if not valido:
        return 0, avisos

    with open(_CSV_360_PATH, "wb") as f:
        f.write(conteudo)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(_CSV_360_PATH, _BACKUP_DIR / f"exportacao_360_{ts}.csv")

    meta = {
        "ultimo_upload": datetime.now().isoformat(),
        "arquivo_original": uploaded_file.name,
        "total_registros": len(df_full),
    }
    with open(_META_360_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    github_persist("data/exportacao_360.csv", conteudo, "Upload exportação 360")
    meta_bytes = json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")
    github_persist("data/exportacao_360_meta.json", meta_bytes, "Meta exportação 360")

    _carregar_360.clear()
    return len(df_full), avisos


def carregar_meta_360() -> dict | None:
    if not _META_360_PATH.exists():
        return None
    with open(_META_360_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_backups_360() -> list[dict]:
    if not _BACKUP_DIR.exists():
        return []
    backups = []
    for arquivo in sorted(_BACKUP_DIR.glob("exportacao_360_*.csv"), reverse=True):
        stat = arquivo.stat()
        backups.append({
            "nome": arquivo.name,
            "caminho": arquivo,
            "tamanho": stat.st_size,
            "data": datetime.fromtimestamp(stat.st_mtime),
        })
    return backups


def calcular_alertas_360(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calcula alertas de prazos e inconsistências no 360 de Exportação."""
    hoje = pd.Timestamp.now().normalize()
    alertas: dict[str, pd.DataFrame] = {}

    # Dead Draft vencido sem confirmação
    if "Dead Draft" in df.columns:
        mask = df["Dead Draft"].notna() & (df["Dead Draft"] < hoje)
        if "Dead Draft Confirmado" in df.columns:
            mask = mask & df["Dead Draft Confirmado"].isna()
        alertas["dead_draft"] = df[mask].copy()
    else:
        alertas["dead_draft"] = pd.DataFrame()

    # Dead Carga vencida sem confirmação
    if "Dead Carga" in df.columns:
        mask = df["Dead Carga"].notna() & (df["Dead Carga"] < hoje)
        if "Dead Carga Confirmada" in df.columns:
            mask = mask & df["Dead Carga Confirmada"].isna()
        alertas["dead_carga"] = df[mask].copy()
    else:
        alertas["dead_carga"] = pd.DataFrame()

    # Dead VGM vencido sem confirmação
    if "Dead VGM" in df.columns:
        mask = df["Dead VGM"].notna() & (df["Dead VGM"] < hoje)
        if "VGM Confirmado" in df.columns:
            mask = mask & df["VGM Confirmado"].isna()
        alertas["dead_vgm"] = df[mask].copy()
    else:
        alertas["dead_vgm"] = pd.DataFrame()

    # Previsão de embarque vencida sem data de embarque real
    if "Previsão de embarque" in df.columns:
        mask = df["Previsão de embarque"].notna() & (df["Previsão de embarque"] < hoje)
        if "Data de embarque" in df.columns:
            mask = mask & df["Data de embarque"].isna()
        alertas["prev_embarque_vencida"] = df[mask].copy()
    else:
        alertas["prev_embarque_vencida"] = pd.DataFrame()

    # DUE registrada sem averbação
    if "Data de Registro DUE" in df.columns:
        mask = df["Data de Registro DUE"].notna()
        if "Data averbação" in df.columns:
            mask = mask & df["Data averbação"].isna()
        alertas["due_sem_avercacao"] = df[mask].copy()
    else:
        alertas["due_sem_avercacao"] = pd.DataFrame()

    # Processos sem etapa
    if "Status" in df.columns:
        alertas["sem_etapa"] = df[df["Status"] == "Sem etapa"].copy()
    else:
        alertas["sem_etapa"] = pd.DataFrame()

    # Follow desatualizado > 10 dias
    if "Data do follow" in df.columns:
        dias = (hoje - df["Data do follow"]).dt.days
        mask = dias.notna() & (dias > 10)
        resultado = df[mask].copy()
        resultado["Dias sem Follow"] = dias[mask].astype(int)
        alertas["follow_desatualizado"] = resultado
    else:
        alertas["follow_desatualizado"] = pd.DataFrame()

    return alertas


# ══════════════════════════════════════════════════════════════════════
# EMBARCADOS — XLSX (KPIs / Performance)
# ══════════════════════════════════════════════════════════════════════


def calcular_score(classificacao: str) -> float:
    """Soma pesos por tipo encontrado na string de Classificação."""
    if not isinstance(classificacao, str) or not classificacao.strip() or classificacao.strip() == "0":
        return 0.0
    total = 0.0
    for parte in classificacao.split("+"):
        total += PESOS.get(parte.strip(), 0.0)
    return total


def data_referencia(row: pd.Series) -> pd.Timestamp | None:
    """Data de referência para KPI mensal, conforme prioridade de classificação."""
    cls = str(row.get("Classificação", "")).lower()
    if "desembaraço" in cls:
        val = row.get("DT DUE")
        if pd.notna(val):
            return val
    if "frete" in cls:
        val = row.get("DT Embarque")
        if pd.notna(val):
            return val
    if "documentos" in cls:
        val = row.get("DT Encer.")
        if pd.notna(val):
            return val
    val = row.get("DT Abertura")
    return val if pd.notna(val) else None


def dados_embarcados_existem() -> bool:
    return _XLSX_EMB_PATH.exists()


@st.cache_data(show_spinner="Carregando embarcados de exportação...", ttl=300)
def _carregar_embarcados(_mtime_key: float = 0) -> pd.DataFrame:
    if not _XLSX_EMB_PATH.exists():
        return pd.DataFrame()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(_XLSX_EMB_PATH, dtype=str)

    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    for col in COLUNAS_DATA_EMB:
        if col in df.columns:
            df[col] = _parse_datas(df[col])

    # Deduplicar por Processo: manter linha com DT Fat. mais recente
    if "Processo" in df.columns:
        df = (
            df.sort_values("DT Fat.", na_position="first")
            .drop_duplicates(subset=["Processo"], keep="last")
            .reset_index(drop=True)
        )

    # Colunas derivadas
    if "Classificação" in df.columns:
        df["score"] = df["Classificação"].apply(calcular_score)
        df["data_ref"] = df.apply(data_referencia, axis=1)
        df["ano_ref"] = df["data_ref"].apply(lambda v: int(v.year) if pd.notna(v) else None)
        df["mes_ref"] = df["data_ref"].apply(lambda v: int(v.month) if pd.notna(v) else None)

    return df


def obter_processos_embarcados() -> pd.DataFrame:
    return _carregar_embarcados(_mtime_key=_mtime_emb())


def validar_embarcados_xlsx(df: pd.DataFrame) -> tuple[bool, list[str]]:
    avisos: list[str] = []
    faltantes = [c for c in COLUNAS_OBRIGATORIAS_EMB if c not in df.columns]
    if faltantes:
        return False, [f"Colunas obrigatórias ausentes: {', '.join(faltantes)}"]
    if len(df) == 0:
        return False, ["O arquivo não contém registros."]
    return True, avisos


def salvar_upload_embarcados(uploaded_file) -> tuple[bool, str]:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        conteudo = uploaded_file.getvalue()
        uploaded_file.seek(0)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_full = pd.read_excel(uploaded_file, dtype=str)
        df_full.columns = df_full.columns.str.strip()
        df_full = df_full.dropna(how="all")

        valido, avisos = validar_embarcados_xlsx(df_full)
        if not valido:
            return False, "; ".join(avisos)

        with open(_XLSX_EMB_PATH, "wb") as f:
            f.write(conteudo)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(_XLSX_EMB_PATH, _BACKUP_DIR / f"exportacao_emb_{ts}.xlsx")

        meta = {
            "ultimo_upload": datetime.now().isoformat(),
            "arquivo_original": uploaded_file.name,
            "total_registros": len(df_full),
        }
        with open(_META_EMB_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        github_persist("data/exportacao_embarcados.xlsx", conteudo, "Upload embarcados exportação")
        meta_bytes = json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8")
        github_persist("data/exportacao_emb_meta.json", meta_bytes, "Meta embarcados exportação")

        _carregar_embarcados.clear()
        return True, f"Upload concluído! {len(df_full)} registros importados."
    except Exception as exc:
        return False, f"Erro no upload: {exc}"


def carregar_meta_emb() -> dict | None:
    if not _META_EMB_PATH.exists():
        return None
    with open(_META_EMB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_backups_emb() -> list[dict]:
    if not _BACKUP_DIR.exists():
        return []
    backups = []
    for arquivo in sorted(_BACKUP_DIR.glob("exportacao_emb_*.xlsx"), reverse=True):
        stat = arquivo.stat()
        backups.append({
            "nome": arquivo.name,
            "caminho": arquivo,
            "tamanho": stat.st_size,
            "data": datetime.fromtimestamp(stat.st_mtime),
        })
    return backups


# ── Agregações KPI ───────────────────────────────────────────────────


def kpis_mensais(df: pd.DataFrame, ano: int | None = None) -> pd.DataFrame:
    """Retorna processos e score agregados por (ano, mes)."""
    if df.empty or "score" not in df.columns:
        return pd.DataFrame(columns=["ano", "mes", "processos", "score"])

    mask = df["ano_ref"].notna() & df["mes_ref"].notna()
    if ano is not None:
        mask = mask & (df["ano_ref"] == ano)

    df_f = df[mask].copy()
    if df_f.empty:
        return pd.DataFrame(columns=["ano", "mes", "processos", "score"])

    result = (
        df_f.groupby(["ano_ref", "mes_ref"])
        .agg(processos=("Processo", "count"), score=("score", "sum"))
        .reset_index()
        .rename(columns={"ano_ref": "ano", "mes_ref": "mes"})
        .sort_values(["ano", "mes"])
        .reset_index(drop=True)
    )
    return result


def kpis_por_account(df: pd.DataFrame, ano: int | None = None) -> pd.DataFrame:
    """Score e processos por Account."""
    if df.empty or "Account" not in df.columns:
        return pd.DataFrame()
    mask = df["ano_ref"].notna()
    if ano is not None:
        mask = mask & (df["ano_ref"] == ano)
    return (
        df[mask]
        .groupby("Account")
        .agg(processos=("Processo", "count"), score=("score", "sum"))
        .reset_index()
        .sort_values("score", ascending=False)
        .reset_index(drop=True)
    )


def obter_anos_embarcados(df: pd.DataFrame | None = None) -> list[int]:
    """Lista de anos disponíveis nos embarcados."""
    if df is None:
        df = obter_processos_embarcados()
    if df.empty or "ano_ref" not in df.columns:
        return []
    return sorted(df["ano_ref"].dropna().unique().astype(int).tolist(), reverse=True)
