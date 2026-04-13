"""CRUD para Colaboradores e Histórico + efeito cascata no Manpower."""
from datetime import date, datetime
from utils.excel_io import (
    carregar_workbook, salvar_workbook, proximo_id,
    sheet_to_list, encontrar_linha,
    SHEET_COLABORADORES, SHEET_HISTORICO, SHEET_CARGOS, SHEET_DEPARTAMENTOS,
)
from utils.manpower import recalcular_manpower_mensal
from utils.status import status_efetivo


def _normalizar_unidade(colab):
    cidade = str(colab.get("cidade") or "").strip()
    if cidade in ("Novo Hamburgo", "Itajaí"):
        return cidade

    empresa = str(colab.get("empresa") or "").strip().upper()
    if any(chave in empresa for chave in (" ITJ", "ITAJAI", "ITAJAI", "SC", "FILIAL")):
        return "Itajaí"
    if any(chave in empresa for chave in ("NH", "NOVO HAMBURGO", "MATRIZ")):
        return "Novo Hamburgo"
    return cidade or "Novo Hamburgo"


def _enriquecer_colaborador(colab, cargos_map, deptos_map):
    """Adiciona nome do cargo e departamento ao dict do colaborador."""
    cargo = cargos_map.get(colab.get("cargo_id"))
    depto = deptos_map.get(colab.get("departamento_id"))
    colab["cargo_nome"] = cargo["nome"] if cargo else "—"
    colab["cargo_nivel"] = cargo["nivel"] if cargo else "—"
    colab["peso_manpower"] = cargo["peso_manpower"] if cargo else None
    colab["departamento_nome"] = depto["nome"] if depto else "—"
    colab["empresa_original"] = colab.get("empresa")
    colab["unidade"] = _normalizar_unidade(colab)
    colab["empresa"] = colab["unidade"]
    colab["status"] = status_efetivo(colab)
    return colab


def listar_colaboradores(status=None, departamento_id=None):
    wb = carregar_workbook()
    colaboradores = sheet_to_list(wb[SHEET_COLABORADORES])
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    deptos = {d["id"]: d for d in sheet_to_list(wb[SHEET_DEPARTAMENTOS])}

    resultado = []
    for c in colaboradores:
        enriquecido = _enriquecer_colaborador(c, cargos, deptos)
        if status and enriquecido.get("status") != status:
            continue
        if departamento_id is not None and enriquecido.get("departamento_id") != departamento_id:
            continue
        resultado.append(enriquecido)
    return resultado


def buscar_colaborador(colab_id):
    wb = carregar_workbook()
    cargos = {c["id"]: c for c in sheet_to_list(wb[SHEET_CARGOS])}
    deptos = {d["id"]: d for d in sheet_to_list(wb[SHEET_DEPARTAMENTOS])}
    for c in sheet_to_list(wb[SHEET_COLABORADORES]):
        if c["id"] == colab_id:
            return _enriquecer_colaborador(c, cargos, deptos)
    return None


def contratar(nome, cargo_id, departamento_id, empresa, cidade,
              gestor_direto, data_entrada, observacao="", tipo_contrato=""):
    """Registra contratação: cria colaborador + histórico + recalcula manpower."""
    wb = carregar_workbook()
    ws_colab = wb[SHEET_COLABORADORES]
    ws_hist = wb[SHEET_HISTORICO]

    # Buscar nome do cargo para o histórico
    cargos = sheet_to_list(wb[SHEET_CARGOS])
    cargo_nome = next((c["nome"] for c in cargos if c["id"] == cargo_id), "—")

    # Novo colaborador
    novo_id = proximo_id(ws_colab)
    if isinstance(data_entrada, str):
        data_entrada = datetime.strptime(data_entrada, "%Y-%m-%d").date()
    ws_colab.append([
        novo_id, nome, cargo_id, departamento_id, empresa, cidade,
        tipo_contrato, gestor_direto, data_entrada, None, "Ativo"
    ])

    # Histórico
    hist_id = proximo_id(ws_hist)
    ws_hist.append([hist_id, novo_id, nome, "Entrada", cargo_nome, data_entrada, observacao])

    salvar_workbook(wb)

    # Efeito cascata: recalcular manpower do mês
    recalcular_manpower_mensal(data_entrada.year, data_entrada.month)

    return novo_id


def desligar(colab_id, data_saida, observacao=""):
    """Registra desligamento: atualiza colaborador + histórico + recalcula manpower."""
    wb = carregar_workbook()
    ws_colab = wb[SHEET_COLABORADORES]
    ws_hist = wb[SHEET_HISTORICO]

    if isinstance(data_saida, str):
        data_saida = datetime.strptime(data_saida, "%Y-%m-%d").date()

    # Buscar colaborador
    row_num = encontrar_linha(ws_colab, 1, colab_id)
    if not row_num:
        raise ValueError(f"Colaborador {colab_id} não encontrado.")

    nome = ws_colab.cell(row=row_num, column=2).value
    cargo_id = ws_colab.cell(row=row_num, column=3).value

    # Buscar cargo para histórico
    cargos = sheet_to_list(wb[SHEET_CARGOS])
    cargo_nome = next((c["nome"] for c in cargos if c["id"] == cargo_id), "—")

    # Atualizar colaborador
    ws_colab.cell(row=row_num, column=10, value=data_saida)  # data_saida
    ws_colab.cell(row=row_num, column=11, value="Inativo")  # status

    # Histórico
    hist_id = proximo_id(ws_hist)
    ws_hist.append([hist_id, colab_id, nome, "Saída", cargo_nome, data_saida, observacao])

    salvar_workbook(wb)

    # Efeito cascata
    recalcular_manpower_mensal(data_saida.year, data_saida.month)


def atualizar_colaborador(colab_id, nome=None, cargo_id=None, departamento_id=None,
                          empresa=None, cidade=None, gestor_direto=None):
    """Atualiza campos editáveis de um colaborador."""
    wb = carregar_workbook()
    ws = wb[SHEET_COLABORADORES]
    row_num = encontrar_linha(ws, 1, colab_id)
    if not row_num:
        raise ValueError(f"Colaborador {colab_id} não encontrado.")

    if nome is not None:
        ws.cell(row=row_num, column=2, value=nome)
    if cargo_id is not None:
        ws.cell(row=row_num, column=3, value=cargo_id)
    if departamento_id is not None:
        ws.cell(row=row_num, column=4, value=departamento_id)
    if empresa is not None:
        ws.cell(row=row_num, column=5, value=empresa)
    if cidade is not None:
        ws.cell(row=row_num, column=6, value=cidade)
    if gestor_direto is not None:
        ws.cell(row=row_num, column=8, value=gestor_direto)

    salvar_workbook(wb)


def _coluna_idx(ws, nome_header):
    """Retorna o índice (1-based) da coluna pelo nome do header, ou None se não encontrar."""
    for col in range(1, ws.max_column + 1):
        if ws.cell(row=1, column=col).value == nome_header:
            return col
    return None


def atualizar_responsavel_direto(colab_id, responsavel_nome):
    """Atualiza o campo responsavel_direto de um colaborador (usado para reportes no organograma)."""
    wb = carregar_workbook()
    ws = wb[SHEET_COLABORADORES]
    row_num = encontrar_linha(ws, 1, colab_id)
    if not row_num:
        raise ValueError(f"Colaborador {colab_id} não encontrado.")
    col = _coluna_idx(ws, "responsavel_direto")
    if col:
        ws.cell(row=row_num, column=col, value=responsavel_nome or None)
    salvar_workbook(wb)


def listar_historico(colaborador_id=None):
    wb = carregar_workbook()
    historico = sheet_to_list(wb[SHEET_HISTORICO])
    if colaborador_id is not None:
        historico = [h for h in historico if h["colaborador_id"] == colaborador_id]
    # Ordenar por data decrescente
    historico.sort(key=lambda h: h.get("data") or "", reverse=True)
    return historico
