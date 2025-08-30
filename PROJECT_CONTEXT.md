# Entertainment Planner - Project Context for Context7

## Project Overview
**entertainment-planner** is a multi-agent system designed for collecting, processing, and recommending entertainment venues and places. The system successfully parses TimeOut articles and maintains a comprehensive database of places in Bangkok.

## Current Implementation Status
✅ **COMPLETED**: Universal TimeOut parser with 321 places extracted
✅ **COMPLETED**: Database integration (raw.db) with 283 unique places
✅ **COMPLETED**: Monorepo structure with apps/, packages/, docs/
✅ **COMPLETED**: API layer for recommendations
✅ **COMPLETED**: Search provider implementation
✅ **COMPLETED**: React UI application

## Key Components

### 1. TimeOut Parser (`universal_timeout_parser.py`)
- **Purpose**: Extracts place information from TimeOut articles
- **Capabilities**: 
  - Handles 16 different article types
  - Extracts names, descriptions, addresses, images
  - Supports numbered and unnumbered place lists
  - News articles and reviews parsing
- **Output**: 321 places with rich metadata

### 2. Database (`raw.db`)
- **Schema**: raw_places table
- **Fields**: name_raw, description_raw, address_raw, raw_json, source
- **Content**: 283 unique places from TimeOut articles
- **Sources**: 16 different TimeOut article types

### 3. Monorepo Structure
```
entertainment-planner/
├── apps/
│   ├── api/          # FastAPI recommendation API
│   ├── ingest/       # Data ingestion pipeline
│   └── ui/           # React TypeScript UI
├── packages/
│   ├── core/         # Data models and ontology
│   └── search/       # Search provider
├── docs/             # Architecture documentation
└── scripts/          # Utility scripts
```

## Data Sources Processed
1. **bangkoks-top-10-spots-for-health-conscious-dining** (23 places)
2. **best-breakfast-restaurants-in-bangkok** (15 places)
3. **bangkoks-best-garden-cafes** (15 places)
4. **best-juice-bars-around-bangkok** (9 places)
5. **bookstores-cafe-coffee** (24 places)
6. **thailand-leads-asias-50-best-restaurants** (12 places)
7. **haoma-sustainable-indian-dining** (8 places)
8. **shake-shack-x-potong-collab** (5 places)
9. **bakery-shops** (18 places)
10. **best-bakeries-sourdough** (10 places)
11. **best-donut-shops** (13 places)
12. **best-restaurants-asoke** (17 places)
13. **best-places-iconsiam** (14 places)
14. **best-restaurants-ari** (35 places)
15. **best-restaurants-charoenkrung** (49 places)
16. **best-restaurants-sukhumvit-31** (16 places)

## Current Capabilities
- **Data Extraction**: 100% success rate for descriptions and images
- **Address Extraction**: 26% success rate (where available in articles)
- **Image URLs**: 100% success rate from media.timeout.com
- **Category Detection**: Automatic district and category identification
- **Deduplication**: Smart duplicate removal based on name and address

## Next Development Phases
1. **Enrichment Pipeline**: Integrate with external APIs for additional data
2. **Search Enhancement**: Implement advanced search and filtering
3. **Recommendation Engine**: Build ML-based recommendation system
4. **User Interface**: Enhance UI with place discovery features
5. **Data Validation**: Implement quality checks and data cleaning

## Technical Stack
- **Backend**: Python, FastAPI, SQLite
- **Frontend**: React, TypeScript, Tailwind CSS
- **Data Processing**: BeautifulSoup4, requests, regex
- **Testing**: pytest, snapshot testing
- **Architecture**: Monorepo with clear separation of concerns

## Usage Context
When referencing this project in AI conversations:
- **Project Name**: entertainment-planner
- **Current Focus**: TimeOut data extraction and place database
- **Key Achievement**: Successfully parsed 321 places from 16 articles
- **Architecture**: Multi-agent system with clear component separation
- **Status**: Core functionality complete, ready for enhancement phase

## Context7 Integration
This project context file is designed to be used with Context7 MCP server to provide AI assistants with comprehensive understanding of the entertainment-planner project, its current status, capabilities, and architecture.
