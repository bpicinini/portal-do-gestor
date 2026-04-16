# Prompt Mestre: Construção do Módulo de Restituições (Streamlit) para o Portal 3S

**Objetivo:**
Construir um novo módulo (aba) de "Gestão de Restituições" para o portal existente em **Streamlit**. O sistema deve ser profissional, objetivo e seguir rigorosamente a identidade visual do portal (tons de bege, dourado, cards arredondados e fontes limpas).

---

## 1. Contexto Técnico e Visual
- **Framework:** Streamlit (Python).
- **Identidade Visual:** Basear-se na UI atual (conforme imagem de referência). Usar `st.metric` para KPIs, `st.dataframe` ou `st.data_editor` para a lista de processos, e `st.expander` ou `st.tabs` para detalhes.
- **Integração:** O código deve ser modular para ser importado como uma nova página ou aba no arquivo principal do portal.

## 2. Estrutura de Dados (Schema Sugerido)
Implementar uma estrutura (pode ser via SQLite ou integração com o DB atual) com os campos:
- **Processos:** Código (OE/OC/OP), Cliente, Número e-CAC, Valor Principal, Valor Corrigido (Selic), Status, Data Protocolo, Prazo Fatal (Intimação), Motivo (Divergência NCM, Seguro, etc), Desencaixe (3S/Cliente).
- **Logs/Timeline:** Histórico de atualizações por processo.

## 3. Fluxo de Status (Taxonomia Profissional)
O sistema deve gerir os seguintes estados:
1. **Abertura de Dossiê**
2. **Pendência Documental** (Alerta visual de bloqueio)
3. **Pedido Protocolado** (Aguardando RFB)
4. **Intimação em Aberto** (Prioridade Crítica - Destaque em Vermelho/Alerta)
5. **Resposta Protocolada** (Defesa enviada)
6. **Pedido Deferido** (Direito reconhecido)
7. **Crédito Programado** (Aguardando depósito)
8. **Processo Extinto (Sucesso)**
9. **Despacho Decisório Negativo** (Indeferido)
10. **Processo Arquivado** (Desistência)

## 4. Funcionalidades de Interface (UI/UX no Streamlit)

### A. Dashboard de Cabeçalho
- Usar `st.columns` para exibir métricas: **Total em Recuperação**, **Total Recuperado**, **Intimações Críticas**.
- Aplicar CSS customizado para manter os cards com bordas arredondadas e cores do portal.

### B. Gestão e Edição
- **Filtros:** Sidebar ou topo com filtros por Status e Cliente.
- **Tabela Interativa:** Usar `st.data_editor` para permitir atualizações rápidas de status e valores diretamente na grade.
- **Timeline e Anexos:** Um formulário ou expander para cada processo que permita:
    - Inserir notas de progresso.
    - Upload de arquivos (PDF/Imagens) usando `st.file_uploader`.

### C. Alertas de Prazo
- Lógica em Python para calcular a diferença entre `hoje` e `Prazo Fatal`.
- Exibir um `st.warning` ou `st.error` no topo da página caso existam intimações vencendo em menos de 48h.

---

**Instrução para o Claude Code:**
"Claude, aja como um Desenvolvedor Python Sênior especialista em Streamlit. Construa o módulo de Restituições para o Portal 3S. O código deve ser limpo, modular e esteticamente idêntico ao portal atual (tons de bege/dourado). Priorize a usabilidade: o analista deve conseguir atualizar um status com o mínimo de cliques possível. Use `st.data_editor` para a gestão principal e garanta que a lógica de prazos fatais seja o destaque do sistema."
