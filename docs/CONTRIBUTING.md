# Contributing

Thank you for helping improve the Entertainment Planner project! This guide outlines how to work with the repository.

## Development Workflow
1. **Setup**
   - Install dependencies with `python3 -m pip install -r requirements.txt`.
   - Optionally copy `.env.example` to `.env` and adjust values for your local environment.
2. **Run the data pipeline**
   - Parse: `python3 apps/ingest/parsers/timeout_bkk.py --limit 5`
   - Enrich: `python3 apps/ingest/enrich/run_enrich.py --limit 5 --city bangkok`
   - Normalize: `python3 apps/ingest/normalize/normalizer.py --limit 10`
   - Index: `python3 apps/ingest/index/build_index.py`
3. **Start services**
   - API: `cd apps/api && python3 main.py`
   - UI: `cd apps/ui && npm start`

## Scripts
Key helper scripts live in the `scripts/` directory:

| Script | Purpose |
|-------|---------|
| `init_db.sh` | Initialize the SQLite database |
| `run_api.sh` | Start the FastAPI server |
| `start_ui.sh` | Launch the React development server |
| `run_tests.sh` | Execute the test suite across layers |

Run any script with `bash scripts/<script>.sh`.

## Coding Standards
- Follow [PEP 8](https://peps.python.org/pep-0008/) and include type hints where possible.
- Write tests for new functionality and run `bash scripts/run_tests.sh` before committing.
- Keep commits focused and include descriptive messages.

Happy hacking!
