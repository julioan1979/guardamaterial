# Gestão de Stock - Escuteiros

Aplicação em [Streamlit](https://streamlit.io/) para gerir o inventário das diferentes secções de um agrupamento de escuteiros, com persistência dos dados no [Airtable](https://airtable.com/).

## Funcionalidades
- Dashboard com resumo de artigos, quantidade total e alertas de stock baixo.
- Gestão de artigos: criar, atualizar ou remover itens do inventário.
- Registo de movimentos (entradas/saídas) com histórico completo e exportação para CSV.
- Personalização das secções do agrupamento diretamente na aplicação.
- Download do inventário e dos movimentos em formato CSV.

## Configuração
1. Crie (ou reutilize) uma base no Airtable com duas tabelas:
   - **Inventário** com campos `Artigo`, `Secção`, `Quantidade`, `Stock Mínimo`, `Localização`, `Notas`, `Atualizado em`.
   - **Movimentos** com campos `Data`, `Artigo`, `Secção`, `Quantidade`, `Responsável`, `Tipo`, `Notas`.
2. Guarde os identificadores:
   - API Key: disponível em [https://airtable.com/account](https://airtable.com/account).
   - Base ID (formato `appXXXXXXXXXXXXXX`).
   - Nomes das tabelas (ou personalize-os na aplicação).
3. Defina as variáveis de ambiente ou crie um ficheiro `.streamlit/secrets.toml`:

   ```toml
   AIRTABLE_API_KEY = "key..."
   AIRTABLE_BASE_ID = "app..."
   AIRTABLE_INVENTORY_TABLE = "Inventário"
   AIRTABLE_TRANSACTIONS_TABLE = "Movimentos"
   AIRTABLE_USERS_TABLE = "Utilizadores"
   ```

   Também é possível utilizar uma secção dedicada:

   ```toml
   [airtable]
   api_key = "key..."
   base_id = "app..."
   inventory_table = "Inventário"
   transactions_table = "Movimentos"
   users_table = "Utilizadores"
   ```

   A aplicação lê automaticamente estes valores (quer estejam numa secção `[airtable]` ou na raiz do ficheiro/variáveis de ambiente), continuando a permitir a sua edição no menu lateral. Para o módulo de autenticação, o nome da tabela de utilizadores pode ser personalizado através de `AIRTABLE_USERS_TABLE` ou `st.secrets["airtable"]["users_table"]`; na ausência de configuração é utilizado o nome predefinido **"Utilizadores"**.

## Execução local
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Arranque a aplicação Streamlit:
   ```bash
   streamlit run app.py
   ```
3. Configure o Airtable através do menu lateral e comece a gerir o inventário.

## Estrutura do repositório
- `app.py` – código da aplicação Streamlit.
- `requirements.txt` – dependências Python.
- `README.md` – este guia rápido.

Bom trabalho e boas caçadas!
