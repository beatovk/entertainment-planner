from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi import Request
from pydantic import BaseModel
from typing import List, Dict, Optional
import sqlite3
import json
import time
import math
from datetime import datetime
from pathlib import Path
import sys
import os

# Make ingest and root modules importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ingest.db_init import init_clean_db, seed_mock_data
from packages.search.provider import LocalSearchProvider
from cache import CacheManager
from middleware import TimingMiddleware, log_operation
from settings import settings

app = FastAPI(title="Entertainment Planner API")

# Add timing middleware
app.add_middleware(TimingMiddleware)

# Ensure database exists with seed data
db_file = Path(settings.db_path)
if not db_file.exists():
    db_file.parent.mkdir(parents=True, exist_ok=True)
    init_clean_db(db_file)
    seed_mock_data(db_file)

# Initialize search provider and cache manager
search_provider = LocalSearchProvider(settings.db_path)
cache_manager = CacheManager(settings.db_path)

# Feedback model
class FeedbackRequest(BaseModel):
    route: List[int]
    useful: bool
    note: Optional[str] = None

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_place_by_id(place_id: int) -> Optional[Dict]:
    """Fetch place by ID from clean.places"""
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, summary_160, full_description, lat, lng, district, city,
                   price_level, rating, ratings_count, hours_json, phone, site,
                   gmap_url, photos_json, tags_json, vibe_json, quality_score
            FROM places WHERE id = ?
        ''', (place_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'summary_160': row[2],
                'full_description': row[3],
                'lat': row[4],
                'lng': row[5],
                'district': row[6],
                'city': row[7],
                'price_level': row[8],
                'rating': row[9],
                'ratings_count': row[10],
                'hours_json': json.loads(row[11]) if row[11] else None,
                'phone': row[12],
                'site': row[13],
                'gmap_url': row[14],
                'photos_json': json.loads(row[15]) if row[15] else None,
                'tags_json': json.loads(row[16]) if row[16] else None,
                'vibe_json': json.loads(row[17]) if row[17] else None,
                'quality_score': row[18]
            }
        return None
        
    except Exception as e:
        print(f"Error fetching place {place_id}: {e}")
        return None

def build_route(candidates: List[Dict], start_lat: float, start_lng: float, 
                min_distance: float = 300, max_distance: float = 1200) -> Dict:
    """Build 3-step route using greedy approach by geo proximity"""
    if len(candidates) < 3:
        return None
    
    # Sort candidates by distance from start point
    for candidate in candidates:
        candidate['distance_from_start'] = haversine_distance(
            start_lat, start_lng, candidate['lat'], candidate['lng']
        )
    
    candidates.sort(key=lambda x: x['distance_from_start'])
    
    # Select first place (closest to start)
    route = [candidates[0]]
    current_lat, current_lng = candidates[0]['lat'], candidates[0]['lng']
    
    # Find next 2 places within distance constraints
    for _ in range(2):
        best_next = None
        best_distance = float('inf')
        
        for candidate in candidates:
            if candidate['id'] in [p['id'] for p in route]:
                continue
                
            distance = haversine_distance(current_lat, current_lng, candidate['lat'], candidate['lng'])
            
            if min_distance <= distance <= max_distance and distance < best_distance:
                best_next = candidate
                best_distance = distance
        
        if best_next:
            route.append(best_next)
            current_lat, current_lng = best_next['lat'], best_next['lng']
        else:
            # If no place in range, pick closest one
            for candidate in candidates:
                if candidate['id'] not in [p['id'] for p in route]:
                    route.append(candidate)
                    current_lat, current_lng = candidate['lat'], candidate['lng']
                    break
    
    # Calculate total distance
    total_distance = 0
    for i in range(len(route) - 1):
        total_distance += haversine_distance(
            route[i]['lat'], route[i]['lng'],
            route[i+1]['lat'], route[i+1]['lng']
        )
    
    return {
        'steps': [place['id'] for place in route],
        'total_distance_m': round(total_distance),
        'fit_score': 0.0  # Will be calculated later
    }

def calculate_fit_score(route: Dict, candidates: List[Dict], 
                       vibe: str, intents: List[str]) -> float:
    """Calculate fit score: 0.5*match + 0.25*geo + 0.15*rating + 0.1*diversity"""
    if not route or not candidates:
        return 0.0
    
    # Get route places
    route_places = [c for c in candidates if c['id'] in route['steps']]
    
    # Match score (0.5 weight)
    match_score = 0.0
    for place in route_places:
        place_tags = place.get('tags_json', [])
        place_vibe = place.get('vibe_json', {})
        
        # Check intents match
        intent_matches = sum(1 for intent in intents if intent.lower() in 
                           [tag.lower() for tag in place_tags])
        match_score += intent_matches / len(intents)
        
        # Check vibe match
        if vibe and place_vibe.get('atmosphere') == vibe:
            match_score += 0.5
    
    match_score = min(1.0, match_score / len(route_places))
    
    # Geo score (0.25 weight) - inverse of total distance
    geo_score = 1.0 / (1.0 + route['total_distance_m'] / 1000.0)
    
    # Rating score (0.15 weight)
    rating_score = sum(place.get('rating', 0) for place in route_places) / (len(route_places) * 5.0)
    
    # Diversity score (0.1 weight) - different districts
    districts = set(place.get('district', '') for place in route_places)
    diversity_score = len(districts) / len(route_places)
    
    # Calculate weighted score
    fit_score = (0.5 * match_score + 
                 0.25 * geo_score + 
                 0.15 * rating_score + 
                 0.1 * diversity_score)
    
    return round(fit_score, 3)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    # Check database connectivity
    db_status = "up"
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM places")
        conn.close()
    except:
        db_status = "down"
    
    # Check FTS status
    fts_status = "up"
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fts_places")
        conn.close()
    except:
        fts_status = "down"
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return JSONResponse(
        content={"ok": True, "db": db_status, "fts": fts_status},
        headers={
            "X-Search": "FTS+VEC",
            "X-Debug": f"time_ms={response_time};db={db_status};rank=health"
        }
    )

@app.get("/api/places/recommend")
async def recommend_places(
    vibe: str = Query(..., description="Vibe preference"),
    intents: str = Query(..., description="Comma-separated intents"),
    lat: float = Query(..., description="Starting latitude"),
    lng: float = Query(..., description="Starting longitude")
):
    """Recommend places based on vibe, intents, and location"""
    start_time = time.time()
    
    # Build cache key
    city = "bangkok"  # Default city
    day = datetime.now().strftime("%Y-%m-%d")  # Current day
    cache_key = cache_manager.build_cache_key(city, day, vibe, intents, lat, lng)
    
    # Try to get from cache
    cached_result, cache_status, cache_store = cache_manager.get(cache_key)
    
    if cache_status in ["HIT", "MISS"]:
        # Cache hit or miss, return cached result or compute
        if cache_status == "HIT":
            # Return cached result
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return JSONResponse(
                content=cached_result,
                headers={
                    "X-Search": "FTS+VEC",
                    "X-Cache-Status": cache_status,
                    "X-Cache-Store": cache_store,
                    "X-Debug": f"time_ms={response_time};db=up;rank=recommend;cache={cache_status};store={cache_store}"
                }
            )
    
    # Cache miss, compute recommendation
    # Parse intents
    intent_list = [intent.strip() for intent in intents.split(',')]
    
    # Build search query
    search_terms = [vibe] + intent_list
    search_query = " ".join(search_terms)
    
    # Get candidates via FTS
    fts_results = search_provider.fts(search_query, 20)
    fts_candidates = [doc_id for doc_id, score in fts_results]
    
    # Get candidates via KNN
    knn_results = search_provider.knn(search_query, 20)
    knn_candidates = [doc_id for doc_id, score in knn_results]
    
    # Combine and deduplicate candidates
    all_candidates = list(set(fts_candidates + knn_candidates))
    
    # Fetch full place data
    candidates = []
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in all_candidates])
        cursor.execute(f'''
            SELECT id, name, summary_160, lat, lng, district, rating, 
                   tags_json, vibe_json, quality_score
            FROM places WHERE id IN ({placeholders})
        ''', all_candidates)
        
        for row in cursor.fetchall():
            candidates.append({
                'id': row[0],
                'name': row[1],
                'summary_160': row[2],
                'lat': row[3],
                'lng': row[4],
                'district': row[5],
                'rating': row[6],
                'tags_json': json.loads(row[7]) if row[7] else [],
                'vibe_json': json.loads(row[8]) if row[8] else {},
                'quality_score': row[9]
                })
        
        conn.close()
        
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    # Build route
    route = build_route(candidates, lat, lng)
    if not route:
        raise HTTPException(status_code=404, detail="No suitable route found")
    
    # Calculate fit score
    route['fit_score'] = calculate_fit_score(route, candidates, vibe, intent_list)
    
    # Find alternatives for step 2 (middle place)
    alternatives = {}
    if len(candidates) > 3:
        step2_alternatives = []
        current_step2 = route['steps'][1]
        
        for candidate in candidates:
            if (candidate['id'] != current_step2 and 
                candidate['id'] not in route['steps']):
                # Check if it's a good alternative (similar tags, different from step 1 and 3)
                step1_tags = next(c['tags_json'] for c in candidates if c['id'] == route['steps'][0])
                step3_tags = next(c['tags_json'] for c in candidates if c['id'] == route['steps'][2])
                
                candidate_tags = candidate['tags_json']
                
                # Calculate similarity to step 2
                similarity = len(set(candidate_tags) & set(
                    next(c['tags_json'] for c in candidates if c['id'] == current_step2)
                )) / max(len(candidate_tags), 1)
                
                if similarity > 0.3:  # At least 30% tag overlap
                    step2_alternatives.append({
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'similarity': round(similarity, 2)
                    })
        
        if step2_alternatives:
            step2_alternatives.sort(key=lambda x: x['similarity'], reverse=True)
            alternatives['step2'] = step2_alternatives[:5]
    
    # Prepare result
    result = {
        "routes": [route],
        "alternatives": alternatives
    }
    
    # Cache the result
    cache_manager.set(cache_key, result)
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return JSONResponse(
        content=result,
        headers={
            "X-Search": "FTS+VEC",
            "X-Cache-Status": "MISS",
            "X-Cache-Store": "compute",
            "X-Debug": f"time_ms={response_time};db=up;rank=recommend;cache=miss;store=compute"
        }
    )

@app.get("/api/places/{place_id}")
async def get_place(place_id: int):
    """Get place by ID"""
    start_time = time.time()
    
    place = get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return JSONResponse(
        content=place,
        headers={
            "X-Search": "FTS+VEC",
            "X-Debug": f"time_ms={response_time};db=up;rank=id_lookup"
        }
    )

@app.get("/api/cache/warm")
async def warm_cache(
    city: str = Query(..., description="City for warming cache"),
    day: str = Query(..., description="Date for warming cache (YYYY-MM-DD)"),
    combos: str = Query(..., description="Vibe:intent1,intent2,intent3|vibe2:intent4,intent5,intent6"),
    lat: Optional[float] = Query(13.7563, description="Default latitude (Bangkok center)"),
    lng: Optional[float] = Query(100.5018, description="Default longitude (Bangkok center)")
):
    """
    Warm up cache with precomputed recommendations
    
    Combos format: vibe:intent1,intent2,intent3|vibe2:intent4,intent5,intent6
    Example: lazy:tom-yum,walk,rooftop|budget:thai-spicy,park,rooftop
    
    Uses default Bangkok coordinates if lat/lng not provided
    """
    start_time = time.time()
    
    try:
        warmed_count = 0
        warmed_keys = []
        
        # Parse combos
        combo_list = combos.split('|')
        
        for combo in combo_list:
            if ':' not in combo:
                continue
                
            vibe_part, intents_part = combo.split(':', 1)
            vibe = vibe_part.strip()
            intents = intents_part.strip()
            
            # Build cache key
            cache_key = cache_manager.build_cache_key(city, day, vibe, intents, lat, lng)
            
            # Check if already cached
            cached_value, cache_status, cache_store = cache_manager.get(cache_key)
            
            if cache_status == "MISS":
                # Precompute recommendation
                try:
                    # Parse intents
                    intent_list = [intent.strip() for intent in intents.split(',')]
                    
                    # Build search query
                    search_terms = [vibe] + intent_list
                    search_query = " ".join(search_terms)
                    
                    # Get candidates via FTS and KNN (same logic as recommend endpoint)
                    fts_results = search_provider.fts(search_query, 20)
                    fts_candidates = [doc_id for doc_id, score in fts_results]
                    
                    knn_results = search_provider.knn(search_query, 20)
                    knn_candidates = [doc_id for doc_id, score in knn_results]
                    
                    all_candidates = list(set(fts_candidates + knn_candidates))
                    
                    # Fetch full place data
                    candidates = []
                    conn = sqlite3.connect(settings.db_path)
                    cursor = conn.cursor()
                    
                    if all_candidates:
                        placeholders = ','.join(['?' for _ in all_candidates])
                        cursor.execute(f'''
                            SELECT id, name, summary_160, lat, lng, district, rating, 
                                   tags_json, vibe_json, quality_score
                            FROM places WHERE id IN ({placeholders})
                        ''', all_candidates)
                        
                        for row in cursor.fetchall():
                            candidates.append({
                                'id': row[0],
                                'name': row[1],
                                'summary_160': row[2],
                                'lat': row[3],
                                'lng': row[4],
                                'district': row[5],
                                'rating': row[6],
                                'tags_json': json.loads(row[7]) if row[7] else [],
                                'vibe_json': json.loads(row[8]) if row[8] else {},
                                'quality_score': row[9]
                            })
                    
                    conn.close()
                    
                    # Build route and calculate score
                    if len(candidates) >= 3:
                        route = build_route(candidates, lat, lng)
                        if route:
                            route['fit_score'] = calculate_fit_score(route, candidates, vibe, intent_list)
                            
                            # Find alternatives
                            alternatives = {}
                            if len(candidates) > 3:
                                step2_alternatives = []
                                current_step2 = route['steps'][1]
                                
                                for candidate in candidates:
                                    if (candidate['id'] != current_step2 and 
                                        candidate['id'] not in route['steps']):
                                        candidate_tags = candidate['tags_json']
                                        similarity = len(set(candidate_tags) & set(
                                            next(c['tags_json'] for c in candidates if c['id'] == current_step2)
                                        )) / max(len(candidate_tags), 1)
                                        
                                        if similarity > 0.3:
                                            step2_alternatives.append({
                                                'id': candidate['id'],
                                                'name': candidate['name'],
                                                'similarity': round(similarity, 2)
                                            })
                                
                                if step2_alternatives:
                                    step2_alternatives.sort(key=lambda x: x['similarity'], reverse=True)
                                    alternatives['step2'] = step2_alternatives[:5]
                            
                            # Cache the result
                            result = {
                                "routes": [route],
                                "alternatives": alternatives
                            }
                            
                            cache_manager.set(cache_key, result)
                            warmed_count += 1
                            warmed_keys.append(cache_key)
                            
                except Exception as e:
                    print(f"Error warming cache for combo {combo}: {e}")
                    continue
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return JSONResponse(
            content={
                "warmed": warmed_count,
                "keys": warmed_keys,
                "city": city,
                "day": day,
                "combos_processed": len(combo_list)
            },
            headers={
                "X-Search": "FTS+VEC",
                "X-Debug": f"time_ms={response_time};db=up;rank=warmup"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback about a route"""
    start_time = time.time()
    
    try:
        # Log the feedback operation
        log_operation("feedback_submit", route_ids=feedback.route, useful=feedback.useful, has_note=bool(feedback.note))
        
        # Store feedback in database
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        
        # Create feedback table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                route_json TEXT NOT NULL,
                useful BOOLEAN NOT NULL,
                note TEXT
            )
        ''')
        
        # Insert feedback
        route_json = json.dumps(feedback.route)
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feedback (created_at, route_json, useful, note)
            VALUES (?, ?, ?, ?)
        ''', (created_at, route_json, feedback.useful, feedback.note))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return JSONResponse(
            content={
                "id": feedback_id,
                "message": "Feedback submitted successfully",
                "route": feedback.route,
                "useful": feedback.useful,
                "note": feedback.note
            },
            headers={
                "X-Search": "FTS+VEC",
                "X-Debug": f"time_ms={response_time};db=up;rank=feedback"
            }
        )
        
    except Exception as e:
        log_operation("feedback_error", error=str(e), route_ids=feedback.route)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
