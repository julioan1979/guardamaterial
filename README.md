# Sistema de Gestão de Inventário - Escuteiros 🎯

Sistema completo de gestão de stock e inventário para agrupamentos de escuteiros, com sincronização em tempo real com Airtable.

## 🌟 Funcionalidades

### 📦 Gestão de Itens
- Adicionar, editar e eliminar materiais
- Categorização e estados personalizados
- Controlo de quantidades em tempo real
- Pesquisa e filtros avançados

### 🔄 Controlo de Movimentos
- Registo de entradas e saídas
- Associação a eventos e secções
- Histórico completo de movimentações
- Rastreabilidade total

### 📊 Dashboard e Relatórios
- Métricas em tempo real
- Gráficos interativos
- Análises por categoria, estado e secção
- Exportação de dados (CSV, ZIP)

### 📍 Gestão de Locais
- Organização de espaços de armazenamento
- Localização hierárquica
- Controlo de contenções

### 👥 Gestão de Secções
- Múltiplas secções do agrupamento
- Associação de utilizadores
- Estatísticas por secção

### 🔐 Sistema de Autenticação
- Login seguro com bcrypt
- Perfis de utilizador (Administrador, Gestor, Utilizador)
- Controlo de permissões

### ⚙️ Administração
- Gestão de utilizadores
- Configurações do sistema
- Registos de atividade

## 🚀 Instalação e Execução

### Requisitos
- Python 3.8 ou superior
- Conta Airtable com API key
- Base de dados Airtable configurada

### Instalação Local

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/guardamaterial.git
cd guardamaterial
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as credenciais:**

Crie o ficheiro `.streamlit/secrets.toml`:
```toml
AIRTABLE_API_KEY = "sua_chave_aqui"
AIRTABLE_BASE_ID = "sua_base_id_aqui"
AIRTABLE_USERS_TABLE = "Usuarios"
```

5. **Execute a aplicação:**
```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## ☁️ Deploy no Streamlit Cloud

1. **Faça push do código para GitHub**

2. **Aceda a [share.streamlit.io](https://share.streamlit.io)**

3. **Conecte o seu repositório**

4. **Configure os secrets:**
   - Vá a Settings → Secrets
   - Adicione as suas credenciais:
   ```toml
   AIRTABLE_API_KEY = "sua_chave"
   AIRTABLE_BASE_ID = "sua_base"
   AIRTABLE_USERS_TABLE = "Usuarios"
   ```

5. **Deploy!**

## 📊 Estrutura do Airtable

A aplicação espera as seguintes tabelas no Airtable:

### Tabelas Principais
- **Usuarios** - Utilizadores do sistema
- **Seccoes** - Secções do agrupamento
- **Local** - Locais de armazenamento
- **Itens** - Materiais do inventário
- **Movimentos** - Histórico de movimentações

### Campos por Tabela

**Usuarios:**
- Nome do Usuário
- Email
- Função (Administrador/Gestor/Utilizador)
- Telefone
- Palavra-passe (hash bcrypt)
- Secções associadas (link)

**Itens:**
- Material
- Categoria
- Estado
- Unidade
- Entradas Totais (rollup)
- Saídas Totais (rollup)
- Quantidade Atual (formula)

**Movimentos:**
- Item (link)
- Quantidade
- Motivo
- Data
- Responsável (link)
- Secção (link)
- Local (link)
- Notas

## 🎨 Personalização

### Tema
Edite `.streamlit/config.toml` para personalizar cores e aparência.

### Perfis de Utilizador
Modifique `src/config.py` para ajustar permissões de cada perfil.

## 📖 Estrutura do Projeto

```
guardamaterial/
├── app.py                      # Aplicação principal
├── requirements.txt            # Dependências
├── README.md                   # Este ficheiro
├── .streamlit/
│   ├── config.toml            # Configurações Streamlit
│   └── secrets.toml.example   # Exemplo de secrets
└── src/
    ├── config.py              # Configurações gerais
    ├── auth.py                # Autenticação
    ├── data_manager.py        # Gestão de dados Airtable
    ├── ui/
    │   ├── sidebar.py         # Navegação
    │   └── theme.py           # Estilos customizados
    └── pages/
        ├── dashboard.py       # Dashboard principal
        ├── items.py           # Gestão de itens
        ├── movements.py       # Movimentos
        ├── locations.py       # Locais
        ├── sections.py        # Secções
        ├── reports.py         # Relatórios
        └── admin.py           # Administração
```

## 🔒 Segurança

- Passwords armazenadas com hash bcrypt
- Autenticação obrigatória
- Controlo de permissões por perfil
- Secrets geridos através do Streamlit
- Validação de dados em todas as operações

## 🤝 Contribuir

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para a sua feature
3. Commit das suas alterações
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o ficheiro LICENSE para mais detalhes.

## 👤 Autor

Desenvolvido para os Escuteiros com ❤️

## 📞 Suporte

Para questões ou suporte, contacte o administrador do sistema.

---

**Nota:** Este sistema foi desenvolvido especificamente para gestão de inventário de agrupamentos de escuteiros, mas pode ser adaptado para outras organizações.
