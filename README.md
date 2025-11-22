# Gestão de Stock - Escuteiros

Aplicação em [Streamlit](https://streamlit.io/) para gerir o inventário das diferentes secções de um agrupamento de escuteiros, com persistência dos dados no [Airtable](https://airtable.com/).

## Guia rápido para utilizadores
1. Abra a aplicação e escolha a secção que pretende consultar.
2. Entre com o seu email e palavra-passe para aceder ao inventário.
3. Crie um novo artigo ou edite um existente sempre que precisar de atualizar o stock.
4. Registe entradas ou saídas para manter o histórico de movimentos em dia.
5. Exporte os artigos e os movimentos para CSV a partir do menu lateral.

## Funcionalidades
- Dashboard com resumo de artigos, quantidade total e alertas de stock baixo.
- Gestão de artigos: criar, atualizar ou remover itens do inventário.
- Registo de movimentos (entradas/saídas) com histórico completo.
- Personalização das secções do agrupamento diretamente na aplicação.
- Exportação do inventário e dos movimentos em formato CSV.

## Configuração (admin)
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

## Verificar a estrutura do Airtable
Execute a verificação automática para confirmar se a base contém todas as tabelas
e campos esperados pela aplicação:

```bash
python scripts/check_airtable_tables.py
```

O comando apresenta um relatório detalhado das tabelas e colunas. O código de saída
é `0` quando tudo está conforme e `1` quando são detetadas discrepâncias, permitindo
a integração em pipelines de CI/CD.

## Estrutura do repositório
- `app.py` – código da aplicação Streamlit.
- `requirements.txt` – dependências Python.
- `README.md` – este guia rápido.

Bom trabalho e boas caçadas!
