"""Manpower mensal e Performance — cálculos e persistência."""
from datetime import date
from utils.excel_io import (
    carregar_workbook, salvar_workbook, proximo_id,
    sheet_to_list, encontrar_linha,
    SHEET_COLABORADORES, SHEET_CARGOS, SHEET_DEPARTAMENTOS,
    SHEET_MANPOWER_MENSAL, SHEET_PERFORMANCE, SHEET_PERFORMANCE_EXP,
)
from utils.status import colaborador_ativo_em, fim_do_mes


def _departamentos_performance_ids(deptos):
    ids = [d["id"] for d in deptos if str(d.get("nome", "")).strip().lower() == "importação"]
    return ids or [d["id"] for d in deptos]


def _atualizar_performance_do_mes(ws, ano, mes, manpower):
    """Sincroniza o manpower da performance mensal já cadastrada."""
    for row in ws.iter_rows(min_row=2):
        if row[0].value == ano and row[1].value == mes:
            volume_score = row[2].value or 0
            meta = row[5].value
            performance = round(volume_score / manpower, 2) if manpower and volume_score else 0
            pct_meta = round(performance / meta, 4) if meta and meta > 0 else None
            ws.cell(row=row[0].row, column=4, value=round(manpower, 2))
            ws.cell(row=row[0].row, column=5, value=performance)
            ws.cell(row=row[0].row, column=7, value=pct_meta)
            break


def calcular_manpower_atual(departamento_id=None):
    """Calcula o manpower total baseado nos colaboradores ativos agora."""
    wb = carregar_workbook()
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    hoje = date.today()

    total = 0.0
    for c in colaboradores:
        if not colaborador_ativo_em(c, referencia=hoje):
            continue
        if departamento_id is not None and c.get("departamento_id") != departamento_id:
            continue
        cargo = cargos.get(c.get("cargo_id"))
        peso = cargo.get("peso_manpower") if cargo else None
        if peso is not None:
            total += float(peso)
    return round(total, 2)


def calcular_manpower_por_departamento():
    """Retorna dict {departamento_id: manpower_total} para ativos."""
    wb = carregar_workbook()
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    deptos = sheet_to_list(wb[SHEET_DEPARTAMENTOS])
    hoje = date.today()

    resultado = {}
    for d in deptos:
        resultado[d["id"]] = 0.0

    for c in colaboradores:
        if not colaborador_ativo_em(c, referencia=hoje):
            continue
        cargo = cargos.get(c.get("cargo_id"))
        peso = cargo.get("peso_manpower") if cargo else None
        if peso is not None:
            dept_id = c.get("departamento_id")
            if dept_id in resultado:
                resultado[dept_id] += float(peso)

    for dept_id in resultado:
        resultado[dept_id] = round(resultado[dept_id], 2)
    return resultado


def recalcular_manpower_mensal(ano, mes):
    """Recalcula e salva o snapshot de manpower do mês para cada departamento.
    Chamado automaticamente pelo efeito cascata de entradas/saídas."""
    wb = carregar_workbook()
    ws = wb[SHEET_MANPOWER_MENSAL]
    ws_perf = wb[SHEET_PERFORMANCE]
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    deptos = sheet_to_list(wb[SHEET_DEPARTAMENTOS])
    referencia = fim_do_mes(ano, mes)

    # Usa o fechamento do mês como referência do quadro ativo.
    manpower_dept = {d["id"]: 0.0 for d in deptos}
    for c in colaboradores:
        if not colaborador_ativo_em(c, referencia=referencia):
            continue
        cargo = cargos.get(c.get("cargo_id"))
        peso = cargo.get("peso_manpower") if cargo else None
        if peso is not None:
            dept_id = c.get("departamento_id")
            if dept_id in manpower_dept:
                manpower_dept[dept_id] += float(peso)

    # Upsert por (ano, mes, departamento_id)
    for dept_id, mp_total in manpower_dept.items():
        row_found = None
        for row in ws.iter_rows(min_row=2):
            r_ano = row[0].value
            r_mes = row[1].value
            r_dept = row[2].value
            if r_ano == ano and r_mes == mes and r_dept == dept_id:
                row_found = row[0].row
                break
        if row_found:
            ws.cell(row=row_found, column=4, value=round(mp_total, 2))
        else:
            ws.append([ano, mes, dept_id, round(mp_total, 2)])

    perf_ids = _departamentos_performance_ids(deptos)
    manpower_perf = sum(manpower_dept.get(dept_id, 0.0) for dept_id in perf_ids)
    _atualizar_performance_do_mes(ws_perf, ano, mes, manpower_perf)

    salvar_workbook(wb)


def listar_manpower_mensal(departamento_id=None):
    """Lista snapshots mensais de manpower."""
    wb = carregar_workbook()
    dados = sheet_to_list(wb[SHEET_MANPOWER_MENSAL])
    if departamento_id is not None:
        dados = [d for d in dados if d.get("departamento_id") == departamento_id]
    return dados


def calcular_manpower_mensal_depto(dep_id, ano: int) -> dict:
    """Retorna {mes: manpower_total} para cada mês do ano para o departamento.

    Usa fim_do_mes como data de referência para saber quem estava ativo em cada mês.
    Útil para calcular eficiência histórica correta quando o quadro variou ao longo do ano.
    """
    wb = carregar_workbook()
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    result = {}
    for mes in range(1, 13):
        ref = fim_do_mes(ano, mes)
        total = 0.0
        for c in colaboradores:
            if str(c.get("departamento_id")) != str(dep_id):
                continue
            if not colaborador_ativo_em(c, referencia=ref):
                continue
            cargo = cargos.get(c.get("cargo_id"))
            peso = cargo.get("peso_manpower") if cargo else None
            if peso is not None:
                total += float(peso)
        result[mes] = round(total, 2)
    return result


# === PERFORMANCE ===

def listar_performance():
    """Lista todos os registros de performance."""
    wb = carregar_workbook()
    return sheet_to_list(wb[SHEET_PERFORMANCE])


def salvar_performance(ano, mes, volume_score, manpower, meta=None):
    """Upsert de um registro de performance mensal."""
    wb = carregar_workbook()
    ws = wb[SHEET_PERFORMANCE]

    performance = round(volume_score / manpower, 2) if manpower and manpower > 0 else 0
    pct_meta = round(performance / meta, 4) if meta and meta > 0 else None

    # Buscar linha existente (ano, mes)
    row_found = None
    for row in ws.iter_rows(min_row=2):
        if row[0].value == ano and row[1].value == mes:
            row_found = row[0].row
            break

    if row_found:
        ws.cell(row=row_found, column=3, value=volume_score)
        ws.cell(row=row_found, column=4, value=manpower)
        ws.cell(row=row_found, column=5, value=performance)
        ws.cell(row=row_found, column=6, value=meta)
        ws.cell(row=row_found, column=7, value=pct_meta)
    else:
        ws.append([ano, mes, volume_score, manpower, performance, meta, pct_meta])

    salvar_workbook(wb)


def obter_manpower_para_performance(ano, mes):
    """Obtém o manpower total (todos os deptos que contam) para um dado mês.
    Primeiro tenta snapshot mensal, senão calcula do atual."""
    wb = carregar_workbook()
    dados = sheet_to_list(wb[SHEET_MANPOWER_MENSAL])
    deptos = sheet_to_list(wb[SHEET_DEPARTAMENTOS])
    perf_ids = _departamentos_performance_ids(deptos)
    # Somar todos os departamentos para o mês
    total = 0.0
    encontrou = False
    for d in dados:
        if d.get("ano") == ano and d.get("mes") == mes and d.get("departamento_id") in perf_ids:
            total += float(d.get("manpower_total", 0))
            encontrou = True
    if encontrou:
        return round(total, 2)
    # Fallback: manpower atual
    return round(sum(calcular_manpower_atual(dept_id) for dept_id in perf_ids), 2)


def salvar_performance_exportacao(ano, mes, volume_score, manpower, meta=None):
    """Upsert de um registro de performance mensal de exportação."""
    wb = carregar_workbook()
    ws = wb[SHEET_PERFORMANCE_EXP]

    performance = round(volume_score / manpower, 2) if manpower and manpower > 0 else 0
    pct_meta = round(performance / meta, 4) if meta and meta > 0 else None

    row_found = None
    for row in ws.iter_rows(min_row=2):
        if row[0].value == ano and row[1].value == mes:
            row_found = row[0].row
            break

    if row_found:
        ws.cell(row=row_found, column=3, value=volume_score)
        ws.cell(row=row_found, column=4, value=manpower)
        ws.cell(row=row_found, column=5, value=performance)
        ws.cell(row=row_found, column=6, value=meta)
        ws.cell(row=row_found, column=7, value=pct_meta)
    else:
        ws.append([ano, mes, volume_score, manpower, performance, meta, pct_meta])

    salvar_workbook(wb)


def listar_performance_exportacao():
    """Lista todos os registros de performance de exportação."""
    wb = carregar_workbook()
    return sheet_to_list(wb[SHEET_PERFORMANCE_EXP])
