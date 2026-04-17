"""Módulo de Restituições — gestão de processos de restituição de impostos
junto à Receita Federal, substituindo o antigo controle via ClickUp.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from utils.auth import garantir_autenticado
from utils.restituicoes import (
    STATUS_ATIVO,
    STATUS_CONCLUIDO,
    STATUS_INDEFERIDO,
    intimacoes_pendentes,
    listar_restituicoes,
)
from utils.ui import aplicar_estilos_globais, renderizar_cabecalho_pagina


garantir_autenticado()
aplicar_estilos_globais()


# ── Formatação ───────────────────────────────────────────────────────


def _br_moeda(valor) -> str:
    if valor is None or pd.isna(valor):
        return "—"
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "—"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _br_data(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _soma(registros, campo: str) -> float:
    total = 0.0
    for r in registros:
        v = r.get(campo)
        if v is None:
            continue
        try:
            total += float(v)
        except (TypeError, ValueError):
            continue
    return total


# ── Carregamento de dados ────────────────────────────────────────────

registros = listar_restituicoes()

ativos = [r for r in registros if r.get("status") in STATUS_ATIVO]
concluidos = [r for r in registros if r.get("status") in STATUS_CONCLUIDO]
indeferidos = [r for r in registros if r.get("status") in STATUS_INDEFERIDO]
pendentes = intimacoes_pendentes()

# "Total em recuperação" = valor principal dos ativos
# "Aguardando pagamento" = valor corrigido (ou principal) dos Deferidos não pagos
# "Recuperado" = valor corrigido (ou principal) dos Pago
total_recuperacao = _soma(ativos, "valor_principal")

deferidos = [r for r in concluidos if r.get("status") == "Deferido"]
pagos = [r for r in concluidos if r.get("status") == "Pago"]

total_deferido = sum(
    float(r.get("valor_corrigido") or r.get("valor_principal") or 0) for r in deferidos
)
total_pago = sum(
    float(r.get("valor_corrigido") or r.get("valor_principal") or 0) for r in pagos
)


# ── Cabeçalho ────────────────────────────────────────────────────────

renderizar_cabecalho_pagina(
    "Restituições",
    "Gestão dos processos de restituição de impostos junto à Receita Federal.",
    badge=f"{len(registros)} processos",
)


# ── Banner de alerta ─────────────────────────────────────────────────

if pendentes:
    qtd = len(pendentes)
    rotulo = "intimação pendente" if qtd == 1 else "intimações pendentes"
    valor = _br_moeda(_soma(pendentes, "valor_principal"))
    st.error(
        f"**⚠ {qtd} {rotulo}** aguardando resposta — total de {valor} em jogo. "
        f"Abra a aba **Ativos** e filtre por status *Intimação Pendente* para responder.",
        icon="🚨",
    )


# ── KPIs ─────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Em recuperação",
    _br_moeda(total_recuperacao),
    help=f"{len(ativos)} processos em andamento",
)
c2.metric(
    "Aguardando pagamento",
    _br_moeda(total_deferido),
    help=f"{len(deferidos)} deferidos, pagamento pendente",
)
c3.metric(
    "Já recuperado",
    _br_moeda(total_pago),
    help=f"{len(pagos)} processos pagos",
)
c4.metric(
    "Intimações pendentes",
    str(len(pendentes)),
    help="Processos com resposta em aberto para a RFB",
)


# ── Construção de DataFrames para exibição ──────────────────────────


COLUNAS_BASE = [
    ("numero_processo", "Nº Processo"),
    ("cliente", "Cliente"),
    ("status", "Status"),
    ("processo_ecac", "Processo e-CAC"),
    ("divisao", "Divisão"),
    ("desencaixe", "Desencaixe"),
    ("valor_principal", "Valor Principal"),
    ("responsavel", "Responsável"),
    ("data_protocolo", "Data Protocolo"),
    ("prazo_fatal", "Prazo Fatal"),
    ("motivo_retificacao", "Motivo Retificação"),
]

COLUNAS_CONCLUIDOS = [
    ("numero_processo", "Nº Processo"),
    ("cliente", "Cliente"),
    ("status", "Status"),
    ("processo_ecac", "Processo e-CAC"),
    ("divisao", "Divisão"),
    ("desencaixe", "Desencaixe"),
    ("valor_principal", "Valor Principal"),
    ("valor_corrigido", "Valor Corrigido"),
    ("responsavel", "Responsável"),
    ("data_protocolo", "Data Protocolo"),
    ("motivo_retificacao", "Motivo Retificação"),
]


def _montar_df(lista: list[dict], colunas: list[tuple[str, str]]) -> pd.DataFrame:
    if not lista:
        return pd.DataFrame(columns=[rotulo for _, rotulo in colunas])
    linhas = []
    for r in lista:
        linha = {}
        for campo, rotulo in colunas:
            valor = r.get(campo)
            if campo in ("valor_principal", "valor_corrigido"):
                linha[rotulo] = _br_moeda(valor)
            elif campo in ("data_protocolo", "data_retificacao", "prazo_fatal"):
                linha[rotulo] = _br_data(valor)
            elif valor is None:
                linha[rotulo] = "—"
            else:
                linha[rotulo] = valor
        linhas.append(linha)
    return pd.DataFrame(linhas)


# ── Abas ─────────────────────────────────────────────────────────────

tab_ativos, tab_concluidos, tab_indeferidos = st.tabs(
    [
        f"Ativos ({len(ativos)})",
        f"Concluídos ({len(concluidos)})",
        f"Indeferidos ({len(indeferidos)})",
    ]
)

with tab_ativos:
    if not ativos:
        st.info("Nenhum processo ativo no momento.")
    else:
        df = _montar_df(ativos, COLUNAS_BASE)
        st.dataframe(df, hide_index=True, use_container_width=True)

with tab_concluidos:
    if not concluidos:
        st.info("Nenhum processo concluído ainda.")
    else:
        df = _montar_df(concluidos, COLUNAS_CONCLUIDOS)
        st.dataframe(df, hide_index=True, use_container_width=True)

with tab_indeferidos:
    if not indeferidos:
        st.info("Nenhum processo indeferido.")
    else:
        df = _montar_df(indeferidos, COLUNAS_BASE)
        st.dataframe(df, hide_index=True, use_container_width=True)


st.caption(
    "Visão somente leitura. A edição direta na tabela, timeline de comentários, "
    "filtros avançados e criação de novos processos chegam nos próximos passos."
)
