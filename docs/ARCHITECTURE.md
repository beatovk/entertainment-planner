# Entertainment Planner Architecture

## Overview
Monorepo structure for entertainment planning application.

## Structure
- `/apps/api` - FastAPI backend service
- `/apps/ingest` - Data ingestion services
- `/apps/ui` - Frontend user interface
- `/packages/core` - Shared data models
- `/packages/search` - Search functionality
- `/docs` - Documentation
- `/scripts` - Utility scripts

## API Endpoints
- `GET /api/health` - Health check

## Database Schema

### raw.db
- **raw_places**: Stores raw data from various sources
  - Fields: id, source, source_url, name_raw, description_raw, address_raw, raw_json, fetched_at
  - Unique partial index on (source, name_raw, address_raw)

### clean.db
- **places**: Clean, processed entertainment locations
  - Fields: id, name, summary_160, full_description, lat, lng, district, city, price_level, rating, ratings_count, hours_json, phone, site, gmap_url, photos_json, tags_json, vibe_json, updated_at, quality_score
- **embeddings**: Vector embeddings for semantic search
  - Fields: doc_id, vector, dim
- **fts_places**: FTS5 virtual table for full-text search
  - Fields: name, summary_160, tags

## Data Flow
1. Ingest services collect entertainment data into raw.db
2. Data processing transforms raw data into clean.db
3. Core models define data structure
4. Search providers enable discovery via FTS5 and embeddings
5. API serves data to UI

## Enricher Design

### Overview
The enrichment system adds external data to raw place information using provider abstraction.

### Components
- **PlaceEnricher**: Main enricher class that coordinates enrichment process
- **EnrichmentProvider**: Abstract interface for different data sources
- **MapsStubProvider**: Stub implementation returning deterministic fake data

### Process Flow
1. **Extract**: Read latest N rows from raw.db/raw_places
2. **Enrich**: Call provider to get additional data (rating, coordinates, hours, etc.)
3. **Buffer**: Write enriched data to clean.db/clean_buffer
4. **Upsert**: Move from buffer to clean.db/places with deduplication

### Provider Interface
```python
def enrich(name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
    # Returns: rating, ratings_count, price_level, lat, lng, hours_json, site, phone, gmap_url
```

### Future Providers
- Google Maps API (real HTTP)
- TripAdvisor API
- Local business directories
