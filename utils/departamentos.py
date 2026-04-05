"""CRUD para Departamentos e Cargos."""
from utils.excel_io import (
    carregar_workbook, salvar_workbook, proximo_id,
    sheet_to_list, encontrar_linha,
    SHEET_DEPARTAMENTOS, SHEET_CARGOS, SHEET_COLABORADORES,
)


def listar_departamentos():
    wb = carregar_workbook()
    return sheet_to_list(wb[SHEET_DEPARTAMENTOS])


def listar_cargos(departamento_id=None):
    wb = carregar_workbook()
    cargos = sheet_to_list(wb[SHEET_CARGOS])
    if departamento_id is not None:
        cargos = [c for c in cargos if c["departamento_id"] == departamento_id]
    return cargos


def buscar_departamento(dept_id):
    wb = carregar_workbook()
    for d in sheet_to_list(wb[SHEET_DEPARTAMENTOS]):
        if d["id"] == dept_id:
            return d
    return None


def buscar_cargo(cargo_id):
    wb = carregar_workbook()
    for c in sheet_to_list(wb[SHEET_CARGOS]):
        if c["id"] == cargo_id:
            return c
    return None


def salvar_departamento(nome, dept_id=None):
    wb = carregar_workbook()
    ws = wb[SHEET_DEPARTAMENTOS]
    if dept_id is not None:
        row_num = encontrar_linha(ws, 1, dept_id)
        if row_num:
            ws.cell(row=row_num, column=2, value=nome)
            salvar_workbook(wb)
            return dept_id
    novo_id = proximo_id(ws)
    ws.append([novo_id, nome])
    salvar_workbook(wb)
    return novo_id


def salvar_cargo(nome, nivel, peso_manpower, departamento_id, cargo_id=None):
    wb = carregar_workbook()
    ws = wb[SHEET_CARGOS]
    if cargo_id is not None:
        row_num = encontrar_linha(ws, 1, cargo_id)
        if row_num:
            ws.cell(row=row_num, column=2, value=nome)
            ws.cell(row=row_num, column=3, value=nivel)
            ws.cell(row=row_num, column=4, value=peso_manpower)
            ws.cell(row=row_num, column=5, value=departamento_id)
            salvar_workbook(wb)
            return cargo_id
    novo_id = proximo_id(ws)
    ws.append([novo_id, nome, nivel, peso_manpower, departamento_id])
    salvar_workbook(wb)
    return novo_id


def excluir_departamento(dept_id):
    wb = carregar_workbook()
    # Verificar dependências em Cargos
    cargos = sheet_to_list(wb[SHEET_CARGOS])
    if any(c["departamento_id"] == dept_id for c in cargos):
        raise ValueError("Não é possível excluir: existem cargos vinculados a este departamento.")
    ws = wb[SHEET_DEPARTAMENTOS]
    row_num = encontrar_linha(ws, 1, dept_id)
    if row_num:
        ws.delete_rows(row_num)
        salvar_workbook(wb)


def excluir_cargo(cargo_id):
    wb = carregar_workbook()
    # Verificar dependências em Colaboradores
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    if any(c["cargo_id"] == cargo_id for c in colaboradores):
        raise ValueError("Não é possível excluir: existem colaboradores vinculados a este cargo.")
    ws = wb[SHEET_CARGOS]
    row_num = encontrar_linha(ws, 1, cargo_id)
    if row_num:
        ws.delete_rows(row_num)
        salvar_workbook(wb)
