# 🧭 AGENTS.md – Arquitetura de Agentes do Projeto GuardaMaterial

## Visão Geral
O projeto **GuardaMaterial** é uma aplicação Streamlit integrada com **Airtable**, destinada à gestão centralizada de materiais, ferramentas e equipamentos utilizados nas atividades dos escuteiros.  
A estrutura baseia-se em agentes funcionais independentes, responsáveis por tarefas específicas, garantindo modularidade e fácil manutenção.

---

## 🧩 Estrutura de Agentes

### 1. `AgentAirtable`
**Função:** Comunicação direta com a API Airtable.  
**Responsabilidades:**
- Autenticar usando `st.secrets["airtable"]["api_key"]`.
- Ler, criar, atualizar e eliminar registos.
- Manter integridade de dados e tipos (datas, quantidades, estados).
- Gerir exceções de rede e erros de API.

**Principais funções:**
```python
get_data()
add_record(record_dict)
update_record(record_id, updates)
delete_record(record_id)
```

### 2. `AgentInventory`
**Função:** Orquestrar a lógica de negócio do inventário.  
**Responsabilidades:**
- Agregar dados provenientes do `AgentAirtable`.
- Calcular métricas derivadas (quantidade disponível, itens em manutenção, histórico de movimentações).
- Normalizar e validar dados recebidos da API antes de os disponibilizar à interface.
- Fornecer métodos de alto nível para operações críticas, como reserva, devolução e baixa de materiais.

**Padrões de implementação:**
- As funções devem ser puras sempre que possível; efeitos colaterais devem ser explícitos.
- Retornar `pandas.DataFrame` para coleções tabulares e `dict` para objetos simples.

### 3. `AgentUI`
**Função:** Construção da interface Streamlit.  
**Responsabilidades:**
- Renderizar dashboards, filtros, tabelas e formulários de forma responsiva.
- Guardar estado na `st.session_state` sem expor detalhes das APIs subjacentes.
- Delegar operações de escrita e leitura ao `AgentInventory`.

**Boas práticas:**
- Utilizar componentes reutilizáveis (`st.container`, `st.columns`) para manter consistência visual.
- Isolar cada secção da página em funções próprias (ex.: `render_header()`, `render_inventory_table()`).

### 4. `AgentAuth`
**Função:** Geração e validação de sessões de utilizadores.  
**Responsabilidades:**
- Recolher credenciais (email e palavra-passe) e validá-las junto do Airtable ou serviço auxiliar.
- Reutilizar as funções já presentes em `inventario_escuteiros.utils.auth`.
- Atualizar `st.session_state["user"]` de forma segura, removendo dados sensíveis.

### 5. `AgentSync`
**Função:** Sincronização assíncrona de alterações relevantes.  
**Responsabilidades:**
- Monitorizar filas de operações (ex.: uploads em lote) e reenviá-las quando necessário.
- Implementar backoff exponencial para falhas de rede.
- Persistir estado temporário em ficheiros locais (ex.: JSON) sempre que a sessão Streamlit seja reiniciada.

---

## 📐 Convenções de Código
- Escrever docstrings em português, seguindo o padrão Google ou reStructuredText.
- Manter nomes de funções e variáveis descritivos (`snake_case`).
- Evitar duplicação de lógica entre agentes; preferir helpers localizados em `inventario_escuteiros/utils`.
- Adicionar testes unitários quando novas responsabilidades forem introduzidas.

## ✅ Fluxo de Desenvolvimento
1. Criar/atualizar o agente relevante com foco na responsabilidade única definida.
2. Ajustar ou criar testes em `tests/` garantindo cobertura para o comportamento esperado.
3. Validar a interface executando `streamlit run app.py`.
4. Atualizar esta documentação quando novos agentes forem introduzidos ou responsabilidades forem alteradas.

## 📎 Observações
- Cada novo módulo deve expor funções públicas documentadas na secção correspondente deste ficheiro.
- As interações com Airtable devem ser mockadas nos testes para evitar dependência de rede.
- Respeitar limites de taxa da API utilizando caching (`st.cache_data`) quando apropriado.
