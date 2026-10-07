# MAVIS — Welding Process Monitoring

A Python dashboard for exploring welding process indicators, comparing production recipes, and turning spreadsheet data into visual summaries for industrial quality analysis.

**Python · Pandas · Streamlit · Pyecharts**

> **Em português:** dashboard de indicadores de solda, com filtros por receita, normalização de dados e análise de tendências.

## What it does

- Tracks five process variables: speed, current, temperature, welding pressure, and hammer pressure.
- Loads Excel workbooks from local files or HTTP/HTTPS URLs.
- Normalizes dates, recipe identifiers, and sensor scales before displaying the data.
- Supports recipe selection and daily, weekly, monthly, and annual datasets. The current page navigation includes executive, daily, monthly, and annual views.
- Caches data-loading operations with Streamlit to avoid repeating the same reads for unchanged inputs.
- Produces trend descriptions, rule-based indicator scores, and visual summaries.
- Reads configurable operational costs and a knowledge base of possible causes and actions from JSON files.

## Technical decisions

| Concern | Implementation | Source |
| --- | --- | --- |
| Data ingestion and normalization | Pandas readers, date parsing, recipe selection, and sensor unit conversions | [data_loader.py](app/data_loader.py) |
| Repeated data reads | Streamlit `st.cache_data` | [data_loader.py](app/data_loader.py) |
| Trend interpretation | Changes between initial and final averages, plus stepwise percentage changes | [analysis.py](app/analysis.py) |
| Presentation | Streamlit multipage interface and Pyecharts components | [ui_components.py](app/ui_components.py) |
| Runtime configuration | Environment variables, Streamlit secrets, and JSON configuration | [config.py](app/config.py) |
| Access gate | Session state and password input on the entry page | [inicio.py](inicio.py) |

The current dashboard uses **rule-based scoring**. Its risk scores are heuristic indicators, rather than calibrated failure probabilities. Financial values are estimates derived from configured costs, rather than measured savings.

The repository also contains a loader for external model artifacts in [ml_models.py](app/ml_models.py). No trained model artifacts, training pipeline, or model evaluation results are included in this repository.

## Project structure

- `inicio.py`: application entry point and access page.
- `pages/`: dashboard views.
- `app/data_loader.py`: spreadsheet loading, selection, and normalization.
- `app/analysis.py`: trend calculations, heuristic scoring, and cost estimates.
- `app/ui_components.py`: charts, filters, and layout helpers.
- `app/config.py`: paths, sensor metadata, and configuration loading.
- `config/`: operational cost and possible-cause configuration.
- `data/`: data files; see the workbook requirements below.

## Run locally

Use a Python environment compatible with the dependencies in [requirements.txt](requirements.txt).

```bash
git clone https://github.com/oluisjr/mavis.git
cd mavis
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` locally:

```toml
VALID_PASSWORDS = "replace-with-a-local-development-password"
```

The entry page reads `VALID_PASSWORDS` from **Streamlit secrets**. Setting it only in `.env` does not configure the entry-page password check. Keep this local file out of version control.

Start the application:

```bash
streamlit run inicio.py
```

### Workbook configuration

Without an HTTP/HTTPS `caminho_excel` value, the configuration uses `data/dados_resumidos_gerado.xlsx`. A custom local path in that environment variable is currently ignored by `app/config.py`.

To use remote workbooks, create a local `.env`:

```dotenv
caminho_excel=https://your-data-host.example/dados_resumidos_gerado.xlsx
estatistica=https://your-data-host.example/statistics.xlsx
```

Replace these example URLs with accessible data sources.

Expected workbook conventions:

| Dataset | Worksheet / date field |
| --- | --- |
| Raw records | `Dados Completos`, with `DATA` and `PROGRAM_Nº` |
| All recipes — daily | `Médias Diárias`, with `DATA` |
| All recipes — weekly | `Médias Semanais`, with `SEMANA` |
| All recipes — monthly | `Médias Mensais`, with `MES` |
| All recipes — annual | `Médias Anuais`, with `ANO` |
| Individual recipe | `<recipe>`, `<recipe> - Semanal`, `<recipe> - Mensal`, `<recipe> - Anual` |

Sensor columns use `VELOCIDADE`, `CORRENTE`, `TEMPERATURA`, `PRESSAO_SOLDA`, and `PRESSAO_MARTELADOR`. The loader divides speed by 100 and current/pressures/temperature by 10; temperature is then rounded to an integer.

The separate statistics loader expects a `Sheet1` worksheet. Its default path is `data/estatisticas_por_receita.xlsx`, while the tracked statistics file is named `estatisticas_por_programa.xlsx`. Configure an appropriate remote `estatistica` URL when using that loader.

## Current development priorities

- Add a synthetic demonstration dataset and reproducible setup checks.
- Pin dependencies and document a verified Python version.
- Validate heuristic thresholds and add tests for boundary values, missing data, and zero readings.
- Align the local workbook configuration and statistics filename.
- Document how shared-password access should evolve for broader use.

These priorities describe future work; they are not claims of completed validation.
