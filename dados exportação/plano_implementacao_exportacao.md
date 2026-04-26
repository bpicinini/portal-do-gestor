# Módulo Exportação — Visão 360 + KPIs (Volume & Performance)

## Contexto

A pasta `dados exportação/` foi inserida nessa branch com 4 arquivos para destravar o módulo de Exportação do Portal do Gestor:

- `360 Exportação.csv` (211 linhas, dados operacionais em curso — 34 colunas: Status, Account, Cliente, Booking, Dead Draft, Previsão de embarque, etc.)
- `Relatório de Processos embarcados em 2025 e 2026..xlsx` (1.409 linhas históricas — Processo, Account, Classificação, Modal, DT Abertura → DT Fat.)
- `dashboard_processos_exportação 2025_2026.html` e `dashboard_processos_ponderado_exportação 2025_2026.html` (referências visuais Plotly — não consumidas pelo portal, só servem de inspiração).
- `projeto_exportacao_portal_cloudcode.md` com pesos (Desembaraço=2, Frete=1, Documentos=0,5), prioridade de data de referência e lista de KPIs.

Hoje o portal tem **placeholders** "Em construção" em duas telas:
- `pages/5_Processos_360.py:1588-1625` → aba Exportação dentro de Visão 360
- `pages/3_Manpower_e_Eficiencia.py:1568-1600` → aba Exportação dentro de KPIs (sub-aba Manpower já funciona com 7.25 fixo no 2026)

**Escopo travado pelo usuário**: apenas Visão 360 Exportação + KPIs Exportação (Volume e Painel de Performance), no padrão da Importação. NÃO tocar em Restituições, Briefing, colaboradores ou Processos Judiciais.

## Decisões confirmadas

| Decisão | Resposta |
|---|---|
| Fonte Visão 360 | CSV `360 Exportação.csv` |
| Fonte KPIs/Performance | XLSX `Relatório de Processos embarcados…` |
| Score quando composto | Somar todos os pesos (ex: "Frete + Documentos + Desembaraço" = 3,5) |
| Atualização futura | Upload na própria UI (igual Importação 360 e Agenciamento) |
| Manpower 2026 Exportação | 7,25 (já fixado no portal, reaproveitar `obter_manpower_para_performance`) |

## Regras de negócio

**Pesos por tipo (do md)**: Desembaraço=2, Frete=1, Documentos=0,5, Trading=0 (não citado no md → tratar como 0; confirmar em runtime se aparecer com volume relevante). `calcular_score("Frete + Documentos + Desembaraço") → 3,5`.

**Data de referência (prioridade do md)**: quando a classificação contém Desembaraço → `DT DUE`; senão se contém Frete → `DT Embarque`; senão (só Documentos) → `DT Encer.`. Fallback: `DT Abertura`.

**KPIs solicitados** (do md): Processos por mês, Score por mês, Score por account, Score por analista, Ranking, Tendência, Comparativo importação x exportação. *Comparativo Imp×Exp fica para a aba KPIs de Exportação como gráfico opcional usando `obter_processos()` da Importação só leitura.*

## Arquivos a criar/editar

### NOVO `utils/exportacao.py`
Espelha o padrão `utils/processos360.py` + `utils/agenciamento.py`. Funções públicas:

- `dados_360_existem() -> bool`
- `obter_processos_360() -> pd.DataFrame` (cache por mtime, parse de datas)
- `validar_360_csv(df) -> (bool, list[str])` — checa colunas obrigatórias: Processo, Status, Account Responsável, Cliente, Tipo, Modalidade
- `salvar_upload_360(uploaded_file) -> (int, list[str])` — salva CSV + backup datado em `data/backups/` + meta JSON + `github_persist()`
- `dados_embarcados_existem() -> bool`
- `obter_processos_embarcados() -> pd.DataFrame` (com colunas derivadas: `score`, `data_ref`, `ano_mes`)
- `validar_embarcados_xlsx(df) -> (bool, list[str])` — colunas: Processo, Account, Classificação, Modal, DT Abertura, DT Encer., DT DUE, DT Embarque, DT Lib. Fat., DT Fat.
- `salvar_upload_embarcados(uploaded_file) -> (bool, str)`
- `calcular_score(classificacao: str) -> float` — split por "+", soma pesos
- `data_referencia(row) -> pd.Timestamp | None`
- `kpis_mensais(df, ano=None) -> pd.DataFrame` — colunas: ano, mes, processos, score
- `kpis_por_account(df, ano=None) -> pd.DataFrame`
- `kpis_por_cliente(df, ano=None, top=10) -> pd.DataFrame`
- `calcular_alertas_360(df) -> dict[str, pd.DataFrame]` — DUE registrada sem averbação, processos "Sem etapa", Dead Draft/Carga/VGM com data passada não confirmada, Previsão de embarque vencida sem Data de embarque
- `carregar_meta() -> dict | None`
- `listar_backups() -> list[dict]`

Constantes: `_CSV_360_PATH = data/exportacao_360.csv`, `_XLSX_EMB_PATH = data/exportacao_embarcados.xlsx`, `_META_PATH = data/exportacao_meta.json`, `PESOS = {"Desembaraço": 2, "Frete": 1, "Documentos": 0.5}`.

### EDIT `pages/5_Processos_360.py` (linhas 1588-1625)
Substituir o bloco placeholder da `tab_exportacao`. Mantém a mesma estrutura de 6 sub-abas que já está esboçada: **Visão Geral · Analistas · Clientes · Alertas e Prazos · Tabela · Upload**.

- **Visão Geral**: cards Total / Por Status (Ag.Desembaraço, Ag.Instruções, Embarque, Pré-Embarque, Sem etapa) + dois gráficos lado-a-lado (Status bar / Modalidade pie) + (Account bar / Tipo pie). Reaproveita helpers de cor já usados na aba Importação (linhas ~259-406).
- **Analistas**: agregação por Account Responsável (processos, clientes únicos), cards com expander para drill-down dos processos do analista — espelha o padrão da Importação (linhas ~434-600).
- **Clientes**: top N por processos com drill-down.
- **Alertas e Prazos**: consome `calcular_alertas_360()`, exibe cada categoria como `st.expander` com `st.dataframe` (mesmo padrão Importação linha ~700+).
- **Tabela**: `st.dataframe` filtrável (Status, Account, Modalidade, Cliente).
- **Upload**: `st.file_uploader(type=["csv"])` → `salvar_upload_360()` → mostra `st.success` + lista `listar_backups()`.

Reaproveitar:
- `utils/excel_io.py::github_persist()` — persistência GitHub (já genérica, usa o mesmo padrão de Importação 360 / Agenciamento).
- `utils/ui.py::renderizar_dataframe()`, `altair_theme_args()` — dark mode aware.

### EDIT `pages/3_Manpower_e_Eficiencia.py` (linhas 1568-1600)
Expandir `_tab_kpi_exp`. Antes era só Overview (placeholder) + Manpower. Vira: **Overview · Volume e Performance · Ranking · Manpower (mantida) · Upload**.

- **Overview**: do mês corrente — cards (Processos, Score, Score/MP) + line chart Altair de tendência mensal (`kpis_mensais` agrupado).
- **Volume e Performance**:
  - Carregar `obter_processos_embarcados()` → `kpis_mensais(df, ano)` por ano (2025 / 2026), reaproveitar `chart_perf_meta`, `chart_volume_yoy`, `chart_mp_ano`, `render_metricas_eficiencia`, `render_tabela_performance` que já existem em `pages/3_Manpower_e_Eficiencia.py` (foram escritos para Importação mas são genéricos quando recebem o df no formato `[ano, mes, volume_score, manpower, performance, meta, pct_meta]`).
  - Performance = score_mes / MP. MP vem de `manpower.obter_manpower_para_performance(ano, mes)` filtrado para `departamento_id` da Exportação (já é 7,25 em 2026, snapshot mensal nos meses passados).
  - Meta: Por enquanto **sem meta histórica** (não tem no md). Renderizar `chart_perf_meta` sem linha de meta ou com meta nula → confirmar em runtime se quebra; se quebrar, usar a meta do mês corrente como referência horizontal.
- **Ranking**: `chart_score_ranking` por Account Responsável (já existe), filtrável por ano.
- **Manpower** (existente, manter): cards + tabela do quadro ativo do depto Exportação. **Não mexer.**
- **Upload**: `st.file_uploader(type=["xlsx"])` → `salvar_upload_embarcados()`.

### NOVOS arquivos de dados (seed inicial)
Copiar uma vez na primeira execução (ou via comando manual no terminal antes do primeiro upload):
- `dados exportação/360 Exportação.csv` → `data/exportacao_360.csv`
- `dados exportação/Relatório de Processos embarcados em 2025 e 2026..xlsx` → `data/exportacao_embarcados.xlsx`

Adicionar ambos ao `.gitignore` no padrão dos outros (`data/processos_360.csv` já tem o pattern `arquivo + !arquivo` que mantém versão fixa no repo). Sigo o mesmo: ignorar mas com `!data/exportacao_360.csv` e `!data/exportacao_embarcados.xlsx` para snapshotar o seed.

### Sem alterações em
- `utils/manpower.py`, `utils/pessoas.py`, `utils/organograma.py`, `utils/auth.py`, `utils/restituicoes.py`, `utils/processos_judiciais.py`, `app.py`, `home.py`, demais páginas. Reuso só por importação.

## Reuso (não duplicar)

| Função existente | Onde | Por quê reusar |
|---|---|---|
| `utils/excel_io.py::github_persist(repo_path, file_bytes, msg)` | persistência | Mesma chamada que `processos360.py:228` faz para CSV |
| `utils/processos360.py` (estrutura) | esqueleto | Copiar arquitetura: cache por mtime, validate, save_upload, backups, meta JSON |
| `pages/3_Manpower_e_Eficiencia.py::chart_perf_meta`, `chart_volume_yoy`, `chart_mp_ano`, `chart_score_ranking`, `render_metricas_eficiencia`, `render_tabela_performance` | gráficos Altair + cards | Já têm tema do portal e dark mode. Recebem df genérico. |
| `utils/manpower.py::obter_manpower_para_performance(ano, mes)`, `calcular_manpower_por_departamento()` | denominador da performance | MP 2026 Exportação = 7.25 já está calibrado |
| `utils/ui.py::renderizar_dataframe`, `altair_theme_args`, `renderizar_cabecalho_pagina` | UI consistente | Padrão visual bege/dourado + dark mode |

## Verificação end-to-end

1. **Iniciar portal**: `python -m streamlit run app.py` (na pasta do projeto, com `requirements.txt` instalado).
2. **Login** com usuário admin (Bruno Picinini).
3. **Visão 360 → Exportação**:
   - Conferir que aba "Visão Geral" mostra **211 processos** distribuídos pelos 5 status (Ag.Desembaraço, Ag.Instruções, Embarque, Pré-Embarque, Sem etapa) e 8 accounts (Eliane, Elizandra, Felipe, Jessica, Liliane, Morysson, Roberta, Sumaia).
   - Aba "Alertas e Prazos" deve listar processos com Dead Draft/VGM passados sem confirmação e DUEs registradas sem averbação.
   - Aba "Upload": subir o mesmo CSV de novo, conferir que backup foi criado em `data/backups/exportacao_360_YYYYMMDD_HHMMSS.csv` e meta atualizado.
4. **KPIs → Exportação → Volume e Performance**:
   - Conferir total de **1.409 processos** com 11 duplicatas tratadas (drop ou flag).
   - Conferir score do mês: pegar 1 mês (ex: 2026-03), filtrar manualmente o XLSX por `data_ref` em março/2026, somar pesos da Classificação, comparar com o card.
   - Performance Mar/2026 ≈ score / 7.25.
   - Ranking deve mostrar os 8 accounts ordenados por score do ano selecionado.
5. **Não-regressão** (smoke test rápido):
   - Abrir Importação (Visão 360 e KPIs) — continua funcionando, MP/score iguais.
   - Abrir Restituições, Processos Judiciais, Organograma, Usuários — sem mudanças visuais nem erros.

## Riscos e pontos de atenção

- **11 duplicatas** no XLSX por número de Processo: dropar mantendo a linha com `DT Fat.` mais recente (ou a com mais campos preenchidos). Documentar no `obter_processos_embarcados()`.
- **Tipo "Trading"** aparece em Classificação mas não tem peso definido no md — assumir 0 e logar warning na validação para Bruno revisar.
- **Linha "0"** em Classificação (1 valor encontrado): score 0, sinalizar como "Sem classificação".
- **Sem meta histórica de Exportação** ainda — `chart_perf_meta` precisa aceitar meta nula. Se não aceitar, renderizar sem linha de meta numa primeira versão e abrir issue para Bruno definir metas.
- Limpar `streamlit.cache_data` após upload (já é feito por mtime busting no padrão Importação).
