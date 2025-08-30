# Entertainment Planner API

A FastAPI-based API for entertainment place recommendations with intelligent routing and scoring.

## Features

- **Health Check**: `/api/health` - Database and FTS status
- **Place Lookup**: `/api/places/{id}` - Get place details by ID
- **Smart Recommendations**: `/api/places/recommend` - 3-step route planning with scoring

## API Endpoints

### GET /api/health
Returns system health status with database and FTS connectivity.

**Response:**
```json
{
  "ok": true,
  "db": "up",
  "fts": "up"
}
```

**Headers:**
- `X-Search: "FTS+VEC"`
- `X-Debug: "time_ms=...;db=...;rank=health"`

### GET /api/places/{id}
Fetches place details by ID from the clean.places database.

**Response:** Full place object with all details.

**Headers:**
- `X-Search: "FTS+VEC"`
- `X-Debug: "time_ms=...;db=up;rank=id_lookup"`

### GET /api/places/recommend
Generates intelligent 3-step entertainment routes based on:
- Vibe preference (e.g., "lazy", "vibrant")
- Intents (comma-separated, e.g., "tom-yum,walk,rooftop")
- Starting coordinates (lat, lng)

**Query Parameters:**
- `vibe` (required): Atmosphere preference
- `intents` (required): Comma-separated activity preferences
- `lat` (required): Starting latitude
- `lng` (required): Starting longitude

**Response:**
```json
{
  "routes": [
    {
      "steps": [1, 2, 3],
      "total_distance_m": 850,
      "fit_score": 0.847
    }
  ],
  "alternatives": {
    "step2": [
      {
        "id": 5,
        "name": "Alternative Place",
        "similarity": 0.75
      }
    ]
  }
}
```

**Headers:**
- `X-Search: "FTS+VEC"`
- `X-Debug: "time_ms=...;db=up;rank=recommend"`

## Scoring Algorithm

The fit score is calculated using:
- **50% Match Score**: Intent and vibe alignment
- **25% Geo Score**: Route efficiency (inverse distance)
- **15% Rating Score**: Average place ratings
- **10% Diversity Score**: District variety

## Route Building

Routes are built using a greedy algorithm:
1. Start with closest place to user location
2. Find next place within 300-1200m range
3. Continue until 3 steps are complete
4. Calculate total distance and fit score

## Running the API

### Prerequisites
- Python 3.8+
- SQLite database with places data
- Required packages (see requirements.txt)

### Start the Server
```bash
# From project root
./scripts/run_api.sh

# Or manually
cd apps/api
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## Testing

### Run Tests
```bash
cd apps/api
pytest tests/
```

### Test API Endpoints
```bash
# From project root
./scripts/test_api.sh
```

### Manual Testing with curl

**Health Check:**
```bash
curl "http://localhost:8000/api/health"
```

**Get Place by ID:**
```bash
curl "http://localhost:8000/api/places/1"
```

**Get Recommendations (Bangkok coordinates):**
```bash
curl "http://localhost:8000/api/places/recommend?vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.7563&lng=100.5018"
```

## Database Schema

The API expects a `clean.db` SQLite database with:
- `places` table: Entertainment venue data
- `fts_places` table: Full-text search index
- `embeddings` table: Vector embeddings for similarity search

## Architecture

- **FastAPI**: Modern, fast web framework
- **SQLite**: Lightweight database
- **FTS5**: Full-text search capabilities
- **Vector Search**: KNN similarity search
- **Geographic Routing**: Haversine distance calculations
- **Intelligent Scoring**: Multi-factor recommendation algorithm
