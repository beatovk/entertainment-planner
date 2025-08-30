# Entertainment Planner API - Observability Features

## Overview

The API now includes comprehensive observability features including structured logging, timing middleware, and feedback collection.

## Features Implemented

### 1. Timing Middleware (`/apps/api/middleware.py`)

**Purpose**: Automatically logs timing and metadata for all API requests

**Features**:
- **Structured JSON Logging**: All logs are in JSON format for easy parsing
- **Request Timing**: Measures response time in milliseconds
- **Operation Tracking**: Logs operation name, HTTP method, and path
- **Header Enhancement**: Automatically adds timing info to X-Debug headers

**Log Format**:
```json
{
  "op": "places/recommend",
  "ms": 45.23,
  "status": 200,
  "db": "up",
  "cache": "HIT:memory",
  "method": "GET",
  "path": "/api/places/recommend",
  "query": "vibe=lazy&intents=tom-yum,walk,rooftop&lat=13.73&lng=100.52"
}
```

### 2. Enhanced Response Headers

All API endpoints now include comprehensive debug headers:

**X-Debug Header Format**:
```
time_ms=45.23;db=up;rank=recommend;cache=HIT;store=memory
```

**Components**:
- `time_ms`: Response time in milliseconds
- `db`: Database status (up/down)
- `rank`: Operation type
- `cache`: Cache status (HIT/MISS)
- `store`: Cache storage layer (memory/sqlite/compute)

### 3. Feedback System (`POST /api/feedback`)

**Purpose**: Collect user feedback about route recommendations

**Endpoint**: `POST /api/feedback`

**Request Body**:
```json
{
  "route": [1, 2, 3],
  "useful": true,
  "note": "Great route for lazy day!"
}
```

**Response**:
```json
{
  "id": 1,
  "message": "Feedback submitted successfully",
  "route": [1, 2, 3],
  "useful": true,
  "note": "Great route for lazy day!"
}
```

**Database Schema**:
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    route_json TEXT NOT NULL,
    useful BOOLEAN NOT NULL,
    note TEXT
);
```

## Usage Examples

### Testing the API

1. **Run Smoke Test**:
   ```bash
   ./scripts/smoke.sh
   ```

2. **Test Feedback System**:
   ```bash
   ./scripts/test_feedback.sh
   ```

3. **Run Feedback Examples**:
   ```bash
   ./scripts/feedback_examples.sh
   ```

### Database Queries

**View All Feedback**:
```bash
sqlite3 clean.db 'SELECT * FROM feedback;'
```

**Feedback Summary**:
```bash
sqlite3 clean.db 'SELECT useful, COUNT(*) as count FROM feedback GROUP BY useful;'
```

**Recent Feedback**:
```bash
sqlite3 clean.db 'SELECT id, created_at, route_json, useful, note FROM feedback ORDER BY created_at DESC LIMIT 5;'
```

**Search by Content**:
```bash
sqlite3 clean.db "SELECT * FROM feedback WHERE note LIKE '%lazy%';"
```

**Routes with Most Feedback**:
```bash
sqlite3 clean.db 'SELECT route_json, COUNT(*) as feedback_count FROM feedback GROUP BY route_json ORDER BY feedback_count DESC;'
```

### Curl Examples

**Submit Positive Feedback**:
```bash
curl -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [1,2,3], "useful": true, "note": "Great route!"}'
```

**Submit Negative Feedback**:
```bash
curl -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [4,5,6], "useful": false, "note": "Too expensive"}'
```

**Submit Feedback Without Note**:
```bash
curl -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{"route": [7,8,9], "useful": true}'
```

## Monitoring and Analysis

### Console Logs

All API requests are logged to the console in structured JSON format. Monitor these logs to:
- Track API performance
- Identify slow endpoints
- Monitor cache hit rates
- Track database status

### Response Headers

Use the X-Debug headers to:
- Monitor response times
- Track cache performance
- Verify database connectivity
- Debug performance issues

### Feedback Analytics

Use the feedback data to:
- Identify popular routes
- Improve recommendation algorithms
- Track user satisfaction
- Gather improvement suggestions

## Implementation Details

### Middleware Integration

The timing middleware is automatically applied to all endpoints:
```python
app.add_middleware(TimingMiddleware)
```

### Structured Logging

All operations use the `log_operation` helper:
```python
log_operation("feedback_submit", route_ids=feedback.route, useful=feedback.useful)
```

### Error Handling

Comprehensive error handling with logging:
```python
except Exception as e:
    log_operation("feedback_error", error=str(e), route_ids=feedback.route)
    raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
```

## Benefits

1. **Performance Monitoring**: Real-time visibility into API response times
2. **User Feedback**: Direct insights into route quality and user satisfaction
3. **Structured Logging**: Easy parsing and analysis of API logs
4. **Cache Analytics**: Monitor cache performance and hit rates
5. **Database Monitoring**: Track database connectivity and performance
6. **Debugging**: Comprehensive headers for troubleshooting

## Future Enhancements

- **Metrics Dashboard**: Real-time monitoring dashboard
- **Alerting**: Automated alerts for performance issues
- **Feedback Analytics**: Advanced feedback analysis and reporting
- **Performance Trends**: Historical performance analysis
- **Integration**: Connect with external monitoring tools
