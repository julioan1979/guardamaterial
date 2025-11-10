# Inventário Escuteiros

Aplicação Streamlit para gestão de inventário das secções dos Escuteiros, com sincronização em tempo real com a base **"Inventário Escuteiros"** do Airtable.

## 📦 Estrutura do projeto

```
inventario_escuteiros/
├── streamlit_app.py
├── airtable_client.py
├── requirements.txt
├── utils/
│   ├── layout.py
│   └── helpers.py
├── pages/
│   ├── 1_Visão_Geral.py
│   ├── 2_Gestão_de_Itens.py
│   ├── 3_Auditorias.py
│   ├── 4_Movimentos.py
│   └── 5_Dashboard.py
├── .streamlit/
│   └── secrets.toml
└── README.md
```

## 🔐 Configuração de credenciais

Crie o ficheiro `.streamlit/secrets.toml` com as credenciais da API do Airtable:

```toml
AIRTABLE_API_KEY="chave_pessoal"
AIRTABLE_BASE_ID="id_da_base"
# Opcional: nome personalizado da tabela de utilizadores
AIRTABLE_USERS_TABLE="Utilizadores"
```

O Streamlit lê automaticamente estes valores através de `st.secrets`.

Também pode organizar as credenciais numa secção `[airtable]`, utilizando chaves como `users_table` para indicar o nome da tabela de autenticação:

```toml
[airtable]
api_key="chave_pessoal"
base_id="id_da_base"
users_table="Utilizadores"
```

## ▶️ Executar localmente

1. Crie e ative um ambiente virtual (opcional, mas recomendado).
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Inicie a aplicação Streamlit:

   ```bash
   streamlit run streamlit_app.py
   ```

A aplicação será aberta no navegador (normalmente em `http://localhost:8501`).

## ☁️ Deploy na Streamlit Cloud

1. Publique o projeto no GitHub.
2. No [Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app), crie uma nova aplicação apontando para o repositório.
3. Adicione as variáveis `AIRTABLE_API_KEY` e `AIRTABLE_BASE_ID` na secção **Secrets** da Streamlit Cloud, utilizando o mesmo formato do ficheiro `secrets.toml`.
4. Faça o deploy. A aplicação estará pronta a usar sem alterações adicionais.

---

Com esta aplicação é possível consultar a hierarquia completa do inventário, adicionar novos itens, registar auditorias, controlar movimentos e acompanhar indicadores essenciais em dashboards interativos.
