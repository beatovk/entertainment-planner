import json
import sqlite3
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.cache import CacheManager  # for type hinting (optional)
from services.search import build_route, calculate_fit_score, get_place_by_id
from middleware import log_operation
from settings import settings

router = APIRouter()


class FeedbackRequest(BaseModel):
    route: List[int]
    useful: bool
    note: Optional[str] = None


@router.get("/api/health")
async def health_check():
    start_time = time.time()
    db_status = "up"
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM places")
        conn.close()
    except Exception:
        db_status = "down"

    fts_status = "up"
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fts_places")
        conn.close()
    except Exception:
        fts_status = "down"

    response_time = round((time.time() - start_time) * 1000, 2)
    return JSONResponse(
        content={"ok": True, "db": db_status, "fts": fts_status},
        headers={
            "X-Search": "FTS+VEC",
            "X-Debug": f"time_ms={response_time};db={db_status};rank=health",
        },
    )


@router.get("/api/places/recommend")
async def recommend_places(
    request: Request,
    vibe: str = Query(..., description="Vibe preference"),
    intents: str = Query(..., description="Comma-separated intents"),
    lat: float = Query(..., description="Starting latitude"),
    lng: float = Query(..., description="Starting longitude"),
):
    start_time = time.time()
    cache_manager: CacheManager = request.app.state.cache_manager
    search_provider = request.app.state.search_provider

    city = "bangkok"
    day = datetime.now().strftime("%Y-%m-%d")
    cache_key = cache_manager.build_cache_key(city, day, vibe, intents, lat, lng)

    cached_result, cache_status, cache_store = cache_manager.get(cache_key)
    if cache_status == "HIT":
        response_time = round((time.time() - start_time) * 1000, 2)
        return JSONResponse(
            content=cached_result,
            headers={
                "X-Search": "FTS+VEC",
                "X-Cache-Status": cache_status,
                "X-Cache-Store": cache_store,
                "X-Debug": f"time_ms={response_time};db=up;rank=recommend;cache={cache_status};store={cache_store}",
            },
        )

    intent_list = [intent.strip() for intent in intents.split(",")]
    search_terms = [vibe] + intent_list
    search_query = " ".join(search_terms)

    fts_results = search_provider.fts(search_query, 20)
    fts_candidates = [doc_id for doc_id, _ in fts_results]
    knn_results = search_provider.knn(search_query, 20)
    knn_candidates = [doc_id for doc_id, _ in knn_results]
    all_candidates = list(set(fts_candidates + knn_candidates))

    candidates = []
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        if all_candidates:
            placeholders = ",".join(["?" for _ in all_candidates])
            cursor.execute(
                f"""
                SELECT id, name, summary_160, lat, lng, district, rating,
                       tags_json, vibe_json, quality_score
                FROM places WHERE id IN ({placeholders})
                """,
                all_candidates,
            )
            for row in cursor.fetchall():
                candidates.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "summary_160": row[2],
                        "lat": row[3],
                        "lng": row[4],
                        "district": row[5],
                        "rating": row[6],
                        "tags_json": json.loads(row[7]) if row[7] else [],
                        "vibe_json": json.loads(row[8]) if row[8] else {},
                        "quality_score": row[9],
                    }
                )
        conn.close()
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    route = build_route(candidates, lat, lng)
    if not route:
        raise HTTPException(status_code=404, detail="No suitable route found")

    route["fit_score"] = calculate_fit_score(route, candidates, vibe, intent_list)
    alternatives = {}
    if len(candidates) > 3:
        step2_alternatives = []
        current_step2 = route["steps"][1]
        for candidate in candidates:
            if candidate["id"] != current_step2 and candidate["id"] not in route["steps"]:
                step1_tags = next(
                    c["tags_json"] for c in candidates if c["id"] == route["steps"][0]
                )
                step3_tags = next(
                    c["tags_json"] for c in candidates if c["id"] == route["steps"][2]
                )
                candidate_tags = candidate["tags_json"]
                similarity = len(
                    set(candidate_tags)
                    & set(next(c["tags_json"] for c in candidates if c["id"] == current_step2))
                ) / max(len(candidate_tags), 1)
                if similarity > 0.3:
                    step2_alternatives.append(
                        {
                            "id": candidate["id"],
                            "name": candidate["name"],
                            "similarity": round(similarity, 2),
                        }
                    )
        if step2_alternatives:
            step2_alternatives.sort(key=lambda x: x["similarity"], reverse=True)
            alternatives["step2"] = step2_alternatives[:5]

    result = {"routes": [route], "alternatives": alternatives}
    cache_manager.set(cache_key, result)

    response_time = round((time.time() - start_time) * 1000, 2)
    return JSONResponse(
        content=result,
        headers={
            "X-Search": "FTS+VEC",
            "X-Cache-Status": "MISS",
            "X-Cache-Store": "compute",
            "X-Debug": f"time_ms={response_time};db=up;rank=recommend;cache=miss;store=compute",
        },
    )


@router.get("/api/places/{place_id}")
async def get_place(place_id: int):
    start_time = time.time()
    place = get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    response_time = round((time.time() - start_time) * 1000, 2)
    return JSONResponse(
        content=place,
        headers={
            "X-Search": "FTS+VEC",
            "X-Debug": f"time_ms={response_time};db=up;rank=id_lookup",
        },
    )


@router.get("/api/cache/warm")
async def warm_cache(
    request: Request,
    city: str = Query(..., description="City for warming cache"),
    day: str = Query(..., description="Date for warming cache (YYYY-MM-DD)"),
    combos: str = Query(..., description="Vibe:intent1,intent2,intent3|vibe2:intent4,intent5,intent6"),
    lat: Optional[float] = Query(13.7563, description="Default latitude (Bangkok center)"),
    lng: Optional[float] = Query(100.5018, description="Default longitude (Bangkok center)"),
):
    start_time = time.time()
    cache_manager: CacheManager = request.app.state.cache_manager
    search_provider = request.app.state.search_provider

    try:
        warmed_count = 0
        warmed_keys = []
        combo_list = combos.split("|")
        for combo in combo_list:
            if ":" not in combo:
                continue
            vibe_part, intents_part = combo.split(":", 1)
            vibe = vibe_part.strip()
            intents = intents_part.strip()
            cache_key = cache_manager.build_cache_key(city, day, vibe, intents, lat, lng)
            cached_value, cache_status, _ = cache_manager.get(cache_key)
            if cache_status == "MISS":
                try:
                    intent_list = [intent.strip() for intent in intents.split(",")]
                    search_terms = [vibe] + intent_list
                    search_query = " ".join(search_terms)
                    fts_results = search_provider.fts(search_query, 20)
                    fts_candidates = [doc_id for doc_id, _ in fts_results]
                    knn_results = search_provider.knn(search_query, 20)
                    knn_candidates = [doc_id for doc_id, _ in knn_results]
                    all_candidates = list(set(fts_candidates + knn_candidates))

                    candidates = []
                    conn = sqlite3.connect(settings.db_path)
                    cursor = conn.cursor()
                    if all_candidates:
                        placeholders = ",".join(["?" for _ in all_candidates])
                        cursor.execute(
                            f"""
                            SELECT id, name, summary_160, lat, lng, district, rating,
                                   tags_json, vibe_json, quality_score
                            FROM places WHERE id IN ({placeholders})
                            """,
                            all_candidates,
                        )
                        for row in cursor.fetchall():
                            candidates.append(
                                {
                                    "id": row[0],
                                    "name": row[1],
                                    "summary_160": row[2],
                                    "lat": row[3],
                                    "lng": row[4],
                                    "district": row[5],
                                    "rating": row[6],
                                    "tags_json": json.loads(row[7]) if row[7] else [],
                                    "vibe_json": json.loads(row[8]) if row[8] else {},
                                    "quality_score": row[9],
                                }
                            )
                    conn.close()

                    if len(candidates) >= 3:
                        route = build_route(candidates, lat, lng)
                        if route:
                            route["fit_score"] = calculate_fit_score(
                                route, candidates, vibe, intent_list
                            )
                            alternatives = {}
                            if len(candidates) > 3:
                                step2_alternatives = []
                                current_step2 = route["steps"][1]
                                for candidate in candidates:
                                    if (
                                        candidate["id"] != current_step2
                                        and candidate["id"] not in route["steps"]
                                    ):
                                        candidate_tags = candidate["tags_json"]
                                        similarity = len(
                                            set(candidate_tags)
                                            & set(
                                                next(
                                                    c["tags_json"]
                                                    for c in candidates
                                                    if c["id"] == current_step2
                                                )
                                            )
                                        ) / max(len(candidate_tags), 1)
                                        if similarity > 0.3:
                                            step2_alternatives.append(
                                                {
                                                    "id": candidate["id"],
                                                    "name": candidate["name"],
                                                    "similarity": round(similarity, 2),
                                                }
                                            )
                                if step2_alternatives:
                                    step2_alternatives.sort(
                                        key=lambda x: x["similarity"], reverse=True
                                    )
                                    alternatives["step2"] = step2_alternatives[:5]

                            result = {"routes": [route], "alternatives": alternatives}
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
                "combos_processed": len(combo_list),
            },
            headers={
                "X-Search": "FTS+VEC",
                "X-Debug": f"time_ms={response_time};db=up;rank=warmup",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")


@router.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    start_time = time.time()
    try:
        log_operation(
            "feedback_submit",
            route_ids=feedback.route,
            useful=feedback.useful,
            has_note=bool(feedback.note),
        )
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                route_json TEXT NOT NULL,
                useful BOOLEAN NOT NULL,
                note TEXT
            )
            '''
        )
        route_json = json.dumps(feedback.route)
        created_at = datetime.now().isoformat()
        cursor.execute(
            '''
            INSERT INTO feedback (created_at, route_json, useful, note)
            VALUES (?, ?, ?, ?)
            ''',
            (created_at, route_json, feedback.useful, feedback.note),
        )
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
                "note": feedback.note,
            },
            headers={
                "X-Search": "FTS+VEC",
                "X-Debug": f"time_ms={response_time};db=up;rank=feedback",
            },
        )
    except Exception as e:
        log_operation(
            "feedback_error",
            error=str(e),
            route_ids=feedback.route,
        )
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")
