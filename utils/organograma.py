import os
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache

from openpyxl import load_workbook


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MEGAZORD_PATH = os.path.join(_PROJECT_ROOT, "arquivos base", "PROJETO MEGAZORD.xlsx")


def _nivel(pessoa):
    try:
        return float(pessoa.get("cargo_nivel", 99) or 99)
    except (TypeError, ValueError):
        return 99.0


def _unidade_meta(pessoa):
    unidade = str(pessoa.get("unidade") or pessoa.get("empresa") or "").strip()
    cidade = str(pessoa.get("cidade") or "").strip()
    return unidade or cidade


def normalizar_nome(valor):
    texto = str(valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _chaves_nome(valor):
    base = normalizar_nome(valor)
    if not base:
        return set()
    partes = base.split()
    chaves = {base}
    if partes:
        chaves.add(partes[0])
        chaves.add(partes[-1])
    if len(partes) >= 2:
        chaves.add(f"{partes[0]} {partes[-1]}")
    return {item for item in chaves if item}


def _pontuar_nome(candidato, referencia):
    cand = normalizar_nome(candidato)
    ref = normalizar_nome(referencia)
    if not cand or not ref:
        return -1
    if cand == ref:
        return 100
    if ref in cand or cand in ref:
        return 80
    cand_tokens = set(cand.split())
    ref_tokens = set(ref.split())
    inter = len(cand_tokens & ref_tokens)
    if inter:
        return inter * 10
    return -1


def _buscar_melhor_pessoa(candidatos, referencia):
    melhor = None
    melhor_score = -1
    for pessoa in candidatos:
        score = _pontuar_nome(pessoa.get("nome"), referencia)
        if score > melhor_score:
            melhor = pessoa
            melhor_score = score
    return melhor if melhor_score >= 10 else None


@lru_cache(maxsize=1)
def carregar_sementes_megazord():
    """Lê a planilha-base para obter os reportes já explicitados no organograma."""
    sementes = defaultdict(list)
    if not os.path.exists(_MEGAZORD_PATH):
        return {}

    wb = load_workbook(_MEGAZORD_PATH, data_only=True, read_only=True)
    try:
        if "Estrutura Gabriel" in wb.sheetnames:
            ws = wb["Estrutura Gabriel"]
            # Mapeamentos explícitos visíveis na seção de assistentes.
            for linha in range(21, 27):
                subordinado = ws[f"C{linha}"].value
                analista = ws[f"D{linha}"].value
                if subordinado and analista:
                    sementes["Importação"].append((str(subordinado), str(analista)))
    finally:
        wb.close()

    return dict(sementes)


def construir_estrutura_reportes(colaboradores):
    sementes = carregar_sementes_megazord()
    por_departamento = defaultdict(list)
    for pessoa in colaboradores:
        por_departamento[pessoa["departamento_nome"]].append(pessoa)

    estrutura = []
    for departamento, pessoas in sorted(por_departamento.items()):
        pessoas_ordenadas = sorted(pessoas, key=lambda p: (_nivel(p), normalizar_nome(p["nome"])))
        lideres = [p for p in pessoas_ordenadas if 1 < _nivel(p) <= 2.5]
        analistas = [p for p in pessoas_ordenadas if 3 <= _nivel(p) < 7]
        base = [p for p in pessoas_ordenadas if _nivel(p) >= 7]

        grupos = {analista["id"]: [] for analista in analistas}
        usados = set()

        for subordinado_hint, analista_hint in sementes.get(departamento, []):
            subordinado = _buscar_melhor_pessoa([p for p in base if p["id"] not in usados], subordinado_hint)
            analista = _buscar_melhor_pessoa(analistas, analista_hint)
            if subordinado and analista:
                grupos[analista["id"]].append({"pessoa": subordinado, "origem": "Planilha-base"})
                usados.add(subordinado["id"])

        restantes = [p for p in base if p["id"] not in usados]
        for subordinado in restantes:
            candidatos = analistas[:]
            if not candidatos and lideres:
                candidatos = lideres[:]
            if not candidatos:
                continue

            gestor_ref = normalizar_nome(subordinado.get("gestor_direto"))
            if gestor_ref:
                mesmos_lideres = [
                    cand for cand in candidatos
                    if normalizar_nome(cand.get("gestor_direto")) == gestor_ref
                ]
                if mesmos_lideres:
                    candidatos = mesmos_lideres

            unidade_ref = normalizar_nome(_unidade_meta(subordinado))
            if unidade_ref:
                mesma_unidade = [
                    cand for cand in candidatos
                    if normalizar_nome(_unidade_meta(cand)) == unidade_ref
                ]
                if mesma_unidade:
                    candidatos = mesma_unidade

            alvo = min(
                candidatos,
                key=lambda cand: (
                    len(grupos.setdefault(cand["id"], [])),
                    _nivel(cand),
                    normalizar_nome(cand["nome"]),
                ),
            )
            grupos.setdefault(alvo["id"], []).append({"pessoa": subordinado, "origem": "Distribuição provisória"})

        estrutura.append(
            {
                "departamento": departamento,
                "lideres": lideres,
                "analistas": analistas,
                "grupos": [
                    {
                        "analista": analista,
                        "reportes": sorted(
                            grupos.get(analista["id"], []),
                            key=lambda item: (_nivel(item["pessoa"]), normalizar_nome(item["pessoa"]["nome"])),
                        ),
                    }
                    for analista in analistas
                ],
                "sem_analista": [p for p in base if p["id"] not in usados and not analistas],
            }
        )

    return estrutura
