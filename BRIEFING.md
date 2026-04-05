# Briefing — Portal do Gestor v1

## Visão Geral
Portal privado de gestão de equipe para Bruno Picinini (Gerente de Operações, 3S Corporate).
Substitui planilhas Excel, BI e controles manuais por uma aplicação web centralizada.

---

## Estrutura Organizacional (Organograma)

Bruno tem 3 reportes diretos e 3 setores sob sua gestão:

### 1. Agenciamento
- **Gabriel Hilgert** — Coordenador de Agenciamento
  - Matheus Ropelato — Supervisor
  - Demais: analistas e assistentes

### 2. Exportação
- **Liliane Maus** — Supervisora de Exportação
  - Time abaixo dela

### 3. Importação (maior setor — foco principal do portal)
- **Patrice (Patrice Zeidler Basso)** — Coordenadora de Importação
  - **Mariana Strick** — Supervisora (Itajaí)
  - **Adir Gomes Carvalho** — Especialista (Novo Hamburgo)
  - Demais: analistas, assistentes e estagiários espalhados entre NH e Itajaí

> Nota: Bruna Klauck foi redistribuída para outra gestão — ignorar no organograma.

### Requisitos do Organograma no Portal
- Aba dedicada, editável, dinâmica
- Possibilidade de expandir/colapsar por setor
- Visualizar um setor isoladamente ou todos
- Ao comunicar entrada/saída, atualiza em tempo real
- Flexibilidade para manuseio direto pelo Bruno

---

## Manpower (Pesos por Cargo)

Cada cargo tem um peso de Manpower que representa a capacidade produtiva relativa:

| Nível | Cargo | Peso |
|-------|-------|------|
| 2 | Coordenador | - (não entra no cálculo) |
| 2.5 | Supervisor | - |
| 3 | Especialista | 1.5 |
| 4 | Analista Sênior | 1.3 |
| 5 | Analista Pleno | 1.15 |
| 6 | Analista Júnior | 1.0 |
| 7 | Assistente | 0.5 |
| 8 | Estagiário | 0.25 |
| 9 | Jovem Aprendiz | 0.25 |

- Manpower total atual (importação): **24.8**
- Pessoas com "-" não contam no Manpower (gestão, carregamento, câmbio, seguro)
- Filtro principal: **Departamento de Importação**, mas exibir todos os times com filtro por departamento/setor

### Dados Adicionais do Manpower
Cada colaborador possui: tipo contrato (CLT/PJ), empresa (Leader NH, Leader SC, Winning Trading ITJ, 3S Corp), cidade (Novo Hamburgo / Itajaí), negócio, departamento, gestor direto.

---

## Log de Movimentações

Histórico de entradas e saídas com: Data, Evento (Entrada/Saída), Pessoa, Cargo.
Foco no departamento de Importação.

### Efeito Cascata
Quando Bruno comunica um desligamento ou contratação, deve atualizar automaticamente:
1. **Organograma** — adiciona/remove pessoa
2. **Log** — registra o evento
3. **Manpower** — recalcula o total baseado nos pesos
4. **Performance** — atualiza a coluna Manpower do mês correspondente

---

## Performance (Eficiência da Equipe)

### Fórmula Central
```
Performance = Volume (Score) / Manpower do mês
```

### Estrutura das Abas
- **Performance 2025**: dados de jul/2024 a dez/2025 + média + meta
- **Performance 2026**: resultado 2025 (referência) + projeção/realizado 2026

### Colunas
| Coluna | Descrição |
|--------|-----------|
| Ano | Ano de referência |
| Mês | Nome do mês |
| Est. Processos | Estimativa de processos (em 2026 aparece) |
| Volume (Score) | Somatória ponderada dos processos realizados — vem do BI |
| Manpower | Total de Manpower ativo naquele mês |
| Performance | Volume / Manpower |
| % Meta | Performance / Meta (>1 = superou) |

### Meta
- **Meta 2025**: 335.56 (baseada em +20% da média de 2024 S2)
- **Meta 2026 S1**: 361.42 (baseada na média 2025 S1 × 1.10)
- **Meta 2026 S2**: 439.59 (baseada na média 2025 S2 × 1.20)

### Problema Atual
A coluna Manpower na performance é **manual** — Bruno tem que atualizar a cada evento (contratação, desligamento, promoção). Quer automação: ao registrar um evento, o Manpower do mês se recalcula automaticamente.

### Volume (Score) — Como é Obtido
O Volume vem de um BI externo. É a somatória dos processos de cada analista, ponderados por etapas e multiplicadores:

**Pesos por Etapa do Processo de Importação:**
| Etapa | Peso | O que representa |
|-------|------|-----------------|
| Aberturas | 2 | Análise inicial, abertura no ilog, follow inicial, capa, tratamentos administrativos |
| Embarcados | 4 | NCMs, conferência de docs, dados iniciais, registro de LIs, follow-up |
| Chegadas | 6 | Lançamento no ilog, CE, tracking, remoção, numerário, chegada/desova/MAPA, frete |
| Registros | 7 | Revisão e registro DI, exigências, espelho de nota, ICMS, AFRMM, liberação |
| Lib. Faturamento | 1 | Carregamento, averbação, comprovantes, encerramento |

**Multiplicadores adicionais:**
- Código de Frete Modo (1, 2, 3, 10): determina um peso (Weight) — ex: modo 1 = peso 1, modo 2 = 0.75, modo 3 = 0.5
- Tipo de Operação: Por Conta Própria (1x), Por Conta e Ordem (1.5x), Por Encomenda (2x)
- Score final = etapas × weight × multiplicador de operação

> **Nota do Bruno**: esse BI de score vai ser refeito num projeto futuro. Por enquanto, o portal aceita input manual do Volume mensal (Bruno pega do BI e digita). No futuro, será substituído por integração automática.

### Coluna "Est. Processos" em 2026
Estimativa de processos do mês. O Volume é calculado como: `Est. Processos × 20` (multiplicador fixo atual). Isso também será refinado futuramente.

---

## Arquivos de Referência (Pasta "Arquivos Base")

| Arquivo | Conteúdo |
|---------|----------|
| PROJETO MEGAZORD.xlsx | Planilha principal — organograma, manpower, log, performance |
| organograma (4).png | Imagem do organograma atual completo |
| PAINEL DE PERFORMANCE.xlsx | Lógica do BI de score — pesos por etapa, multiplicadores, exemplos |
| Detalhes Auditoria Pesos.xlsx | Detalhamento por analista × frete × operação |
| Análise de Performance (1).xlsx | Extração BI: processos por analista × cliente × etapa (2026) |
| Análise de performance (2).xlsx | Extração BI: score + média mensal por analista (2026) |
| Análise de performance.xlsx | Idem (2) — mesma extração |
