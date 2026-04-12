"""Lógica de negócio para KPIs do setor de Agenciamento.

Carrega e parseia a planilha de relatório de processos do setor de agenciamento,
extraindo dados de processos em andamento, chegadas confirmadas e faturados.
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
_XLSX_PATH = _DATA_DIR / "agenciamento_processos.xlsx"
_BACKUP_DIR = _DATA_DIR / "backups"
_META_PATH = _DATA_DIR / "agenciamento_meta.json"

ETAPAS_ANDAMENTO = ["Ag booking", "Ag embarque", "Embarcado", "Ag faturamento"]

ETAPAS_CORES = {
    "Ag booking": "#4a8ab5",
    "Ag embarque": "#c79536",
    "Embarcado": "#234055",
    "Ag faturamento": "#5e8668",
}

SENIORIDADE_CORES = {
    "Senior": "#234055",
    "Pleno": "#4a8ab5",
    "Junior": "#c79536",
    "Assistente": "#8a9ba8",
    "Supervisor": "#5e8668",
    "Coordenador": "#6f7a84",
}

MODAL_CORES = {
    "Marítimo": "#234055",
    "Aéreo": "#c79536",
    "Terrestre": "#5e8668",
    "Demurrage": "#b5423a",
}

CARGA_CORES = {
    "FCL": "#234055",
    "LCL": "#4a8ab5",
    "Aéreo": "#c79536",
    "Rodoviário": "#5e8668",
}


# ── Helpers ──────────────────────────────────────────────────────────


def dados_existem() -> bool:
    """Verifica se o arquivo de dados existe."""
    return _XLSX_PATH.exists()


def _mtime() -> float:
    try:
        return os.path.getmtime(_XLSX_PATH)
    except OSError:
        return 0


def _parse_meta(s) -> tuple[int, int]:
    """Parse meta string like '110-140', '70- 80', '010-20' into (min, max)."""
    if pd.isna(s):
        return (0, 0)
    s = str(s).strip().replace(" ", "")
    if "-" in s:
        parts = s.split("-")
        try:
            lo = int(parts[0].lstrip("0") or "0")
            hi = int(parts[1].lstrip("0") or "0")
            return (lo, hi)
        except (ValueError, IndexError):
            return (0, 0)
    try:
        v = int(float(s))
        return (v, v)
    except ValueError:
        return (0, 0)


# ── Carregamento e parsing ───────────────────────────────────────────


def _obter_sheets() -> list[str]:
    """Retorna lista de sheet names disponíveis."""
    try:
        xls = pd.ExcelFile(_XLSX_PATH)
        return xls.sheet_names
    except Exception:
        return []


def obter_anos_disponiveis() -> list[int]:
    """Retorna lista de anos disponíveis, mais recente primeiro."""
    if not dados_existem():
        return []
    anos = []
    for s in _obter_sheets():
        if s.startswith("Resumo "):
            try:
                anos.append(int(s.replace("Resumo ", "")))
            except ValueError:
                pass
    return sorted(anos, reverse=True)


@st.cache_data(show_spinner="Carregando resumo agenciamento...", ttl=300)
def _carregar_resumo_sheet(sheet_name: str, _mtime_key: float = 0) -> dict:
    """Parse um sheet de Resumo e retorna dados estruturados."""
    df = pd.read_excel(_XLSX_PATH, sheet_name=sheet_name, header=None)

    resultado = {
        "data_referencia": "",
        "andamento": [],
        "capacidade_min": 0,
        "capacidade_max": 0,
        "chegadas": [],
        "totais_mes": {},
        "total_andamento": 0,
    }

    # --- Processos em andamento ---
    header_idx = None
    for i in range(len(df)):
        c0 = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ""
        c1 = str(df.iloc[i, 1]) if len(df.columns) > 1 and pd.notna(df.iloc[i, 1]) else ""

        if "Processos em andamento" in c0:
            resultado["data_referencia"] = c1

        if c0 == "Analista" and "Senioridade" in c1:
            header_idx = i
            break

    if header_idx is not None:
        for i in range(header_idx + 1, min(header_idx + 20, len(df))):
            row = df.iloc[i]
            analista = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not analista or analista == "nan":
                total_val = pd.to_numeric(row.iloc[6], errors="coerce")
                if pd.notna(total_val):
                    resultado["total_andamento"] = int(total_val)
                break

            senioridade = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            meta_min, meta_max = _parse_meta(row.iloc[7])

            resultado["andamento"].append({
                "analista": analista,
                "senioridade": senioridade,
                "ag_booking": int(pd.to_numeric(row.iloc[2], errors="coerce") or 0),
                "ag_embarque": int(pd.to_numeric(row.iloc[3], errors="coerce") or 0),
                "embarcado": int(pd.to_numeric(row.iloc[4], errors="coerce") or 0),
                "ag_faturamento": int(pd.to_numeric(row.iloc[5], errors="coerce") or 0),
                "total": int(pd.to_numeric(row.iloc[6], errors="coerce") or 0),
                "meta_min": meta_min,
                "meta_max": meta_max,
            })

    # --- Capacidade ---
    for i in range(len(df)):
        if len(df.columns) <= 7:
            continue
        c7 = str(df.iloc[i, 7]).strip().lower() if pd.notna(df.iloc[i, 7]) else ""
        if c7 in ("minimo", "mínimo"):
            if i + 1 < len(df):
                cap_row = df.iloc[i + 1]
                resultado["capacidade_min"] = int(pd.to_numeric(cap_row.iloc[7], errors="coerce") or 0)
                resultado["capacidade_max"] = int(pd.to_numeric(cap_row.iloc[8], errors="coerce") or 0)
            break

    # --- Chegadas confirmadas ---
    janeiro_row = None
    janeiro_col = None
    for i in range(len(df)):
        for j in range(len(df.columns)):
            val = str(df.iloc[i, j]).strip().lower() if pd.notna(df.iloc[i, j]) else ""
            if val == "janeiro":
                janeiro_row = i
                janeiro_col = j
                break
        if janeiro_col is not None:
            break

    if janeiro_row is not None and janeiro_col is not None:
        total_col_idx = janeiro_col + 12  # 12 meses depois de Janeiro

        for i in range(janeiro_row + 1, min(janeiro_row + 20, len(df))):
            row = df.iloc[i]
            analista = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""

            if "Total" in analista:
                # Linha de totais mensais
                for m in range(1, 13):
                    col = janeiro_col + m - 1
                    if col < len(row):
                        v = pd.to_numeric(row.iloc[col], errors="coerce")
                        if pd.notna(v):
                            resultado["totais_mes"][m] = int(v)
                break

            if not analista or analista == "nan":
                continue

            meses = {}
            for m in range(1, 13):
                col = janeiro_col + m - 1
                if col < len(row):
                    v = pd.to_numeric(row.iloc[col], errors="coerce")
                    if pd.notna(v) and v > 0:
                        meses[m] = int(v)

            total_val = pd.to_numeric(
                row.iloc[total_col_idx], errors="coerce"
            ) if total_col_idx < len(row) else None
            total = int(total_val) if pd.notna(total_val) else sum(meses.values())

            if total > 0 or meses:
                resultado["chegadas"].append({
                    "analista": analista,
                    "meses": meses,
                    "total": total,
                })

    return resultado


@st.cache_data(show_spinner="Carregando faturados...", ttl=300)
def _carregar_faturados_sheet(sheet_name: str, _mtime_key: float = 0) -> pd.DataFrame:
    """Parse um sheet de Faturados."""
    df = pd.read_excel(_XLSX_PATH, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()

    # A coluna "Unnamed: 1" contém o modal (Marítimo importação, etc.)
    if "Unnamed: 1" in df.columns:
        df = df.rename(columns={"Unnamed: 1": "modal_raw"})
        df["modal"] = df["modal_raw"].str.replace(r"\s*importação", "", case=False, regex=True).str.strip()

    rename_map = {
        "Nº processo house": "processo",
        "N° processo house": "processo",
        "Cliente": "cliente",
        "OPERACIONAL": "analista",
        "MÊS": "mes",
        "Data faturado": "data_faturado",
        "Lucro bruto momento processo": "lucro_bruto",
        "Lucro estimado corrente": "lucro_estimado",
        "Total pagamento processo": "total_pagamento",
        "Total recebimento processo": "total_recebimento",
        "Total TEUS": "teus",
        "Origem": "origem",
        "Destino": "destino",
        "Tipo carga": "tipo_carga",
        "Peso bruto": "peso_bruto",
        "Metros cúbicos": "metros_cubicos",
    }
    for old, new in rename_map.items():
        if old in df.columns:
            df = df.rename(columns={old: new})

    num_cols = [
        "lucro_bruto", "lucro_estimado", "total_pagamento",
        "total_recebimento", "teus", "peso_bruto", "metros_cubicos",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "mes" in df.columns:
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce")

    return df


def carregar_dados(ano: int) -> dict | None:
    """Carrega todos os dados de um ano específico."""
    if not dados_existem():
        return None

    mt = _mtime()
    sheets = _obter_sheets()
    sheet_resumo = f"Resumo {ano}"
    sheet_faturados = f"Faturados {ano} HS"

    resultado = {"ano": ano}

    if sheet_resumo in sheets:
        resultado["resumo"] = _carregar_resumo_sheet(sheet_resumo, _mtime_key=mt)
    else:
        return None

    if sheet_faturados in sheets:
        resultado["faturados"] = _carregar_faturados_sheet(sheet_faturados, _mtime_key=mt)

    return resultado


# ── Upload ───────────────────────────────────────────────────────────


def salvar_upload(uploaded_file) -> tuple[bool, str]:
    """Processa upload de nova planilha de agenciamento."""
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        conteudo = uploaded_file.getvalue()

        # Validar que é um Excel válido com sheets esperados
        uploaded_file.seek(0)
        xls = pd.ExcelFile(uploaded_file)
        tem_resumo = any(s.startswith("Resumo ") for s in xls.sheet_names)
        if not tem_resumo:
            return False, "Planilha não contém sheets 'Resumo YYYY'. Verifique o formato."

        # Salvar arquivo principal
        with open(_XLSX_PATH, "wb") as f:
            f.write(conteudo)

        # Backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = _BACKUP_DIR / f"agenciamento_{ts}.xlsx"
        shutil.copy2(_XLSX_PATH, backup_path)

        # Metadados
        meta = {
            "ultimo_upload": datetime.now().isoformat(),
            "arquivo_original": uploaded_file.name,
            "sheets": xls.sheet_names,
        }
        with open(_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Limpar caches
        _carregar_resumo_sheet.clear()
        _carregar_faturados_sheet.clear()

        return True, f"Upload realizado com sucesso! Sheets: {', '.join(xls.sheet_names)}"

    except Exception as e:
        return False, f"Erro no upload: {e}"


def carregar_meta() -> dict | None:
    """Carrega metadados do último upload."""
    if not _META_PATH.exists():
        return None
    with open(_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Performance (Eficiência) — persistência JSON ────────────────────

_PERF_PATH = _DATA_DIR / "agenciamento_performance.json"

# MP padrão da equipe (conforme quadro atual)
MP_PADRAO = 9.75  # 7.0 analistas + 2.75 performance (assistentes + estagiário)


def listar_performance() -> list[dict]:
    """Lista todos os registros de performance do agenciamento."""
    if not _PERF_PATH.exists():
        return []
    with open(_PERF_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_performance(ano: int, mes: int, volume_score: float, manpower: float, meta: float, eficiencia: float | None = None):
    """Upsert de um registro de performance mensal do agenciamento.

    Se *eficiencia* for informada, usa o valor diretamente (vindo do BI).
    Caso contrário calcula como volume_score / manpower.
    """
    records = listar_performance()

    if eficiencia is not None and eficiencia > 0:
        performance = round(eficiencia, 2)
    else:
        performance = round(volume_score / manpower, 2) if manpower and manpower > 0 else 0
    pct_meta = round(performance / meta, 4) if meta and meta > 0 else None

    # Buscar registro existente
    found = False
    for r in records:
        if r["ano"] == ano and r["mes"] == mes:
            r["volume_score"] = volume_score
            r["manpower"] = round(manpower, 2)
            r["performance"] = performance
            r["meta"] = meta
            r["pct_meta"] = pct_meta
            found = True
            break

    if not found:
        records.append({
            "ano": ano, "mes": mes,
            "volume_score": volume_score,
            "manpower": round(manpower, 2),
            "performance": performance,
            "meta": meta,
            "pct_meta": pct_meta,
        })

    records.sort(key=lambda r: (r["ano"], r["mes"]))
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_PERF_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def obter_mp_atual() -> float:
    """Retorna o MP atual calculado do quadro de agenciamento."""
    return MP_PADRAO
