# Copilot Instructions: Sistema de Gestão de Inventário - Escuteiros

## Project Overview
Sistema completo e moderno de gestão de inventário para Escuteiros, desenvolvido em Streamlit com sincronização em tempo real com Airtable. Interface user-friendly com autenticação robusta, dashboard interativo, e funcionalidades avançadas de relatórios. Idioma português usado em toda a aplicação.

## Architecture & Data Flow

### Core Components
- **`app.py`**: Entry point principal com gate de autenticação e routing dinâmico de páginas via importlib
- **`src/config.py`**: Configurações centralizadas (credenciais Airtable, perfis de utilizador, cache TTL)
- **`src/auth.py`**: Sistema de autenticação com bcrypt, gestão de sessões e verificação de permissões
- **`src/data_manager.py`**: Camada de abstração para Airtable com cache inteligente (@st.cache_data) e métodos CRUD
- **`src/ui/`**: Componentes de UI (sidebar com navegação, tema customizado, mensagens de feedback)
- **`src/pages/*.py`**: Cada página implementa `render(data_manager)` - importadas dinamicamente pelo app principal

### Airtable Schema (5 tables)
1. **Usuarios** - Utilizadores com autenticação (email, função, password hash bcrypt, secções associadas)
2. **Seccoes** - Secções do agrupamento (nome, observações, links para utilizadores e movimentos)
3. **Local** - Locais de armazenamento (local, orientação, contenção, notas)
4. **Itens** - Materiais do inventário (material, categoria, estado, unidade, rollup de entradas/saídas)
5. **Movimentos** - Histórico de movimentações (item, quantidade, motivo, data, responsável, secção, local)

**Critical**: Todos os links Airtable são arrays de IDs (e.g., `{"Item": ["recABC123"]}`), mesmo para relações 1:1. A aplicação usa o campo "Localizacao" (formula) como display name dos locais.

## Development Patterns

### Data Loading & Caching
```python
# Sempre usar DataManager para acesso aos dados
data_manager = DataManager()

# Carregar dados com cache automático (TTL de 5 minutos)
items_df = data_manager.get_items()
movements_df = data_manager.get_movements()

# Criar/atualizar/deletar limpa cache automaticamente
data_manager.create_item({"Material": "Corda", "Categoria": "Equipamento"})
# Cache cleared e st.rerun() necessário na página

# Forçar reload sem cache
items_df = data_manager.get_items(reload=True)
```

### Autenticação e Permissões
```python
# Verificar autenticação (já feito no app.py)
if not authenticator.check_authentication():
    authenticator.show_login_page()
    return

# Obter utilizador da sessão
user = st.session_state.get("user", {})
user_role = user.get("funcao", "Utilizador")

# Verificar permissões específicas
if user_role != "Administrador":
    theme.show_error("Acesso negado!")
    return
```

### UI Patterns & Components
```python
# Usar componentes de theme para mensagens consistentes
from src.ui import theme

theme.show_success("Operação concluída!")
theme.show_error("Erro ao processar!")
theme.show_warning("Atenção: verifique os dados")
theme.show_info("Informação adicional")

# Estrutura de página com tabs
tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "✏️ Editar"])

with tab1:
    # Conteúdo da tab lista
    pass

# Formulários com validação
with st.form("form_name", clear_on_submit=True):
    campo = st.text_input("Label *")  # * indica obrigatório
    submitted = st.form_submit_button("💾 Guardar", type="primary")

if submitted:
    if not campo:
        theme.show_error("Campo obrigatório!")
    else:
        # Processar dados
        pass
```

### Filtros e Pesquisa
```python
# Pattern de filtros em colunas
col1, col2, col3 = st.columns(3)

with col1:
    search = st.text_input("🔍 Pesquisar", placeholder="Nome...")

with col2:
    categories = ["Todas"] + sorted(df["Categoria"].dropna().unique().tolist())
    selected = st.selectbox("🏷️ Categoria", categories)

# Aplicar filtros
filtered_df = df.copy()

if search:
    mask = filtered_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
    filtered_df = filtered_df[mask]

if selected != "Todas":
    filtered_df = filtered_df[filtered_df["Categoria"] == selected]
```

## Critical Conventions

### Portuguese Language
- Usar português para todos os elementos visíveis ao utilizador (labels, mensagens, placeholders)
- Usar português para nomes de variáveis de negócio (items_df, movimentos_df, secções)
- Inglês permitido para funções técnicas (render, get_data, filter_df)

### Error Handling & User Feedback
```python
# SEMPRE usar try-except em operações Airtable
try:
    result = data_manager.create_item(data)
    if result:
        theme.show_success("Item criado com sucesso!")
        st.balloons()  # Feedback visual positivo
        st.rerun()
except Exception as e:
    theme.show_error(f"Erro ao criar item: {e}")
```

### Access Control
```python
# Perfis definidos em src/config.py USER_ROLES
# - Administrador: acesso total, incluindo gestão de utilizadores
# - Gestor: acesso a todas as páginas exceto administração
# - Utilizador: acesso apenas a dashboard, itens, movimentos e relatórios (read-only)

# Verificar role na página
user_role = st.session_state.get("user", {}).get("funcao", "Utilizador")
if user_role != "Administrador":
    theme.show_error("⛔ Acesso restrito a administradores")
    return
```

## Running & Testing

```bash
# Desenvolvimento local
cd /workspaces/guardamaterial
pip install -r requirements.txt
streamlit run app.py

# Credenciais em .streamlit/secrets.toml (já configurado para dev)
# Para produção, configurar secrets no Streamlit Cloud dashboard

# Verificar estrutura Airtable
python -c "from src.data_manager import DataManager; dm = DataManager(); print(dm.get_items())"
```

**Sem testes automatizados** - verificar alterações executando a app e validando no Airtable diretamente.

## Common Tasks

### Adicionar nova página
1. Criar `src/pages/nova_pagina.py` com função `render(data_manager)`
2. Importar em `app.py`: `from src.pages import nova_pagina`
3. Adicionar routing no main():
   ```python
   elif page == "🆕 Nova Página":
       nova_pagina.render(data_manager)
   ```
4. Adicionar ao sidebar em `src/ui/sidebar.py` na lista `all_pages`
5. Configurar permissões em `src/config.py` USER_ROLES se necessário

### Adicionar nova tabela Airtable
1. Adicionar nome em `src/config.py` TABLES dict
2. Criar métodos em `DataManager` (`get_novatabela()`, `create_novatabela()`, etc.)
3. Usar em páginas via `data_manager.get_novatabela()`

### Modificar autenticação
- Tabela de utilizadores configurável via `AIRTABLE_USERS_TABLE` (default: "Usuarios")
- Passwords devem ser hash bcrypt antes de guardar no Airtable
- Formula escaping em `src/auth.py`: substituir `'` por `\\'` em queries Airtable
- Credenciais carregadas de `st.secrets` ou variáveis de ambiente

### Adicionar gráficos
```python
import plotly.express as px

# Bar chart
fig = px.bar(df, x="Categoria", y="Quantidade", text="Quantidade", color="Quantidade")
fig.update_layout(showlegend=False, height=350)
st.plotly_chart(fig, use_container_width=True)

# Pie chart
fig = px.pie(df, values="Quantidade", names="Categoria", hole=0.4)
st.plotly_chart(fig, use_container_width=True)

# Line chart (timeline)
fig = px.line(df, x="Mês", y="Movimentos", markers=True)
st.plotly_chart(fig, use_container_width=True)
```

## Dependencies
- **streamlit >= 1.31**: Framework principal
- **pyairtable >= 2.1.0**: Cliente oficial Airtable Python
- **pandas >= 2.1**: Manipulação de dados (todos os records convertidos para DataFrames)
- **plotly >= 5.18.0**: Gráficos interativos (dashboard e relatórios)
- **bcrypt >= 4.1.0**: Hash de passwords para autenticação
- **requests >= 2.31.0**: HTTP client para API Airtable

## Key Files Reference
- `app.py` - Entry point e routing principal
- `src/config.py` - Configurações e constantes
- `src/auth.py` - Sistema de autenticação completo
- `src/data_manager.py` - Camada de acesso aos dados
- `src/ui/sidebar.py` - Navegação e informações do utilizador
- `src/ui/theme.py` - Estilos customizados e componentes de feedback
- `src/pages/dashboard.py` - Dashboard com métricas e gráficos
- `src/pages/items.py` - Gestão CRUD de itens
- `src/pages/movements.py` - Registo de movimentações
- `src/pages/reports.py` - Relatórios e exportações
- `src/pages/admin.py` - Administração (apenas Administrador)
