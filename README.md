# Entertainment Planner MVP

A monorepo project for building entertainment recommendation systems with AI-powered search and route planning.

## Project Structure

```
/Users/user/my-project/
├── apps/
│   ├── api/           # FastAPI backend with recommendation endpoints
│   ├── ingest/        # Data ingestion pipeline (parsers, enrichment, normalization)
│   └── ui/            # React frontend for route planning
├── packages/
│   ├── core/          # Shared data models and ontology
│   └── search/        # Search provider with FTS5 and k-NN
├── docs/              # Project documentation
└── scripts/           # Utility and test scripts
```

## Test Suite

The project includes a comprehensive test suite covering all layers:

### Layer Tests
- **Ingest Layer**: `apps/ingest/tests/test_timeout_parser.py` - Snapshot testing for 3 rows
- **Search Layer**: `packages/search/tests/test_search_provider.py` - Deterministic ordering validation  
- **API Layer**: `apps/api/tests/test_recommend.py` - 3-step route validation

### Running Tests

```bash
# Run all tests (recommended)
bash scripts/run_tests.sh

# Individual layer tests
cd apps/ingest/tests && python3 test_timeout_parser.py
cd packages/search/tests && python3 test_search_provider.py  
cd apps/api/tests && python3 test_recommend.py

# Using pytest (if compatible)
python3 -m pytest -q
```

### Test Configuration

The `pytest.ini` file configures test paths and settings for the monorepo structure.

## Quick Start

### 1. Setup Environment
```bash
# Install Python dependencies
python3 -m pip install -r requirements.txt

# Initialize database
python3 apps/ingest/db_init.py
```

### 2. Run Data Pipeline
```bash
# Parse TimeOut Bangkok data
python3 apps/ingest/parsers/timeout_bkk.py --limit 5

# Enrich with external APIs
python3 apps/ingest/enrich/run_enrich.py --limit 5 --city bangkok

# Normalize data
python3 apps/ingest/normalize/normalizer.py --limit 10

# Build search indices
python3 apps/ingest/index/build_index.py
```

### 3. Start Services
```bash
# Start API server
cd apps/api && python3 main.py

# Start UI (in another terminal)
cd apps/ui && npm start
```

### 4. Run Tests
```bash
# Run complete test suite
bash scripts/run_tests.sh
```

## API Endpoints

- `GET /api/health` - Health check with DB and FTS status
- `GET /api/places/{id}` - Get place details by ID
- `GET /api/places/recommend` - Get route recommendations
- `POST /api/feedback` - Submit route feedback
- `GET /api/cache/warm` - Warm up recommendation cache

## Features

- **Two-layer Caching**: In-memory + SQLite persistence
- **Structured Logging**: JSON-formatted logs with timing
- **FTS5 Search**: Full-text search with SQLite
- **k-NN Search**: Vector similarity search
- **Route Planning**: 3-step route generation with scoring
- **Feedback System**: User feedback collection and storage

## Development

### Adding Tests
- Follow the existing pattern: one test file per layer
- Use descriptive test names and clear assertions
- Include both positive and negative test cases
- Test for deterministic behavior where applicable

### Test Requirements
- **Ingest**: Snapshot testing for data consistency
- **Search**: Deterministic ordering validation
- **API**: Endpoint functionality and response structure

## Troubleshooting

### Pytest Compatibility Issues
If `pytest -q` fails due to version conflicts, use the custom test runner:
```bash
bash scripts/run_tests.sh
```

### Database Issues
Ensure the database is properly initialized:
```bash
python3 apps/ingest/db_init.py
```

### Import Errors
Check that you're running tests from the correct directory or use the test runner script.
