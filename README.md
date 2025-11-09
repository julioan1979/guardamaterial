# Guardamaterial Airtable Utilities

This project provides a small helper package for reading Airtable credentials
from the local `secrets` directory (or environment variables) and for fetching
records from the Airtable REST API. A tiny CLI is included to demonstrate the
functionality.

## Usage

1. Provide the Airtable credentials via environment variables or files inside a
   secrets directory:

   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `AIRTABLE_DEFAULT_TABLE` (optional)
   - `AIRTABLE_VIEW` (optional)

   When using files, create a directory (default: `secrets/`) where each file
   contains the raw secret value (e.g. `secrets/airtable_api_key`). JSON and
   TOML files named `airtable.json` or `airtable.toml` are also supported.

2. Run the CLI:

   ```bash
   python -m guardamaterial list <TABLE_NAME>
   ```

   The command prints a JSON payload with the retrieved records.

## Development

Install the dependencies and run the tests with:

```bash
pip install -e .[dev]
pytest
```
