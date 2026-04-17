# Prompt para Implementação do Novo Módulo: Processos Judiciais e Administrativos

## Objetivo
Criar um novo módulo no Portal do Gestor chamado **Processos Judiciais e Administrativos**, clonando a lógica e estrutura do módulo existente de **Restituições**, mas com adaptações específicas de campos, status e restrição de acesso.

---

## 1. Referência de Base (Módulo Restituições)
O novo módulo deve ser inspirado no arquivo que gerencia as **Restituições** (provavelmente `pages/Restituicoes.py` ou similar).
- **Layout:** Manter o uso de `st.tabs` (Ativos, Concluídos, Indeferidos, Novo).
- **Visualização:** Manter os cards expansíveis com resumo (Cliente, Número, Status, Valor) e detalhes (Histórico/Comentários).
- **Ações:** Manter as funcionalidades de **Visualizar (👁)**, **Editar (✎)** e **Adicionar Novo**.

---

## 2. Especificações do Novo Módulo: Processos Judiciais e Administrativos

### A. Restrição de Acesso
Este módulo deve ser **exclusivo** para os usuários:
- `bruno.picinini@3scorporate.com`
- `gabriel.spohr@3scorporate.com` (ou conforme o campo de email no banco de dados/sessão).
> Se outro usuário tentar acessar, deve exibir uma mensagem de "Acesso Negado" ou o item não deve aparecer no menu lateral.

### B. Estrutura de Dados e Campos
Abaixo estão os campos mapeados a partir da planilha de origem:

| Campo | Tipo | Descrição/Exemplo |
| :--- | :--- | :--- |
| **Título/Tarefa** | Texto Curto | Ex: "Intimação ref. Ganchos do Uruguai" |
| **Tipo do Processo** | Select/Dropdown | Administrativo (ECAC), Judicial, Extrajudicial |
| **Parte Contrária** | Texto Curto | Ex: "RFB", "AMTRANS", "BREGALDA E SOMPO" |
| **Cliente** | Texto Curto | Ex: "WINNING", "BHIO", "LEADERLOG" |
| **Número do Processo** | Texto Curto | Ex: "10265.487828/2024-99" |
| **Prazo Final** | Data | Data de vencimento da tarefa/prazo |
| **Valor** | Moeda (BRL) | Valor envolvido no processo |
| **Último Comentário** | Texto Longo | Histórico de atualizações |
| **Decadência** | Data | Data de decadência (se aplicável) |

### C. Status e Categorização
Os processos devem ser agrupados pelos seguintes status (substituindo os de Restituições) e manter as mesmas cores:
1. **ANÁLISE / TRIAGEM** (Equivalente a um status inicial)
2. **INTIMAÇÃO RECEBIDA / PENDENTE** (Quando uma intimação é recebida e o prazo para cumprimento é crítico. O campo **Prazo Final** deve ser destacado para este status.)
3. **INTIMAÇÃO RESPONDIDA** (Após o cumprimento da intimação.)
4. **JUDICIALIZADO**
5. **ETAPA FINALIZADA** (Mover para a aba "Concluídos")
6. **ENCERRADO EM DEFINITIVO** (Mover para a aba "Concluídos")

---

## 3. Instruções de Implementação para o Claude Code

1.  **Novo Arquivo:** Crie `pages/Processos_Judiciais.py` (ou o padrão do projeto).
2.  **Menu Lateral:** Adicione o ícone `gavel` (ou similar) para o novo módulo, respeitando a trava de usuário.
3.  **Banco de Dados:** 
    - Crie uma nova tabela `processos_judiciais` ou adapte a estrutura existente para suportar os novos campos.
    - Certifique-se de que o histórico de comentários funcione da mesma forma que em Restituições.
4.  **Interface Streamlit:**
    - Utilize os componentes de KPI no topo (Total em Análise, Total Judicializado, etc.).
    - Implemente os filtros por Cliente e Tipo de Processo.
    - No formulário de "Novo" e "Edição", utilize os campos listados na tabela acima.
5.  **Migração Inicial:** Prepare um script ou função para importar os dados da planilha `ProcessosJudiciais.xlsx` (anexada) para a nova estrutura.
    - **Importante:** NÃO migrar os processos **Extrajudiciais** que estão com status **ANÁLISE / TRIAGEM**, pois estes serão descontinuados. Migrar apenas os demais processos conforme a lógica de status definida.

---

## 4. Diferenças Chave para Validar
- **Restituições:** Foca em Protocolo, Intimação, Deferido, Pago.
- **Processos Judiciais e Administrativos:** Foca em Administrativo/Judicial/Extrajudicial, Intimação Recebida/Pendente, Intimação Respondida e nos status de Triagem/Judicializado/Finalizado/Encerrado.
- **Acesso:** Restituições é mais aberto; Processos Judiciais é restrito a Bruno e Gabriel.
