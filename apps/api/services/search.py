import math
import sqlite3
import json
from typing import List, Dict, Optional

from settings import settings


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_place_by_id(place_id: int) -> Optional[Dict]:
    """Fetch place by ID from database"""
    try:
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, name, summary_160, full_description, lat, lng, district, city,
                   price_level, rating, ratings_count, hours_json, phone, site,
                   gmap_url, photos_json, tags_json, vibe_json, quality_score
            FROM places WHERE id = ?
            ''',
            (place_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "name": row[1],
                "summary_160": row[2],
                "full_description": row[3],
                "lat": row[4],
                "lng": row[5],
                "district": row[6],
                "city": row[7],
                "price_level": row[8],
                "rating": row[9],
                "ratings_count": row[10],
                "hours_json": json.loads(row[11]) if row[11] else None,
                "phone": row[12],
                "site": row[13],
                "gmap_url": row[14],
                "photos_json": json.loads(row[15]) if row[15] else None,
                "tags_json": json.loads(row[16]) if row[16] else None,
                "vibe_json": json.loads(row[17]) if row[17] else None,
                "quality_score": row[18],
            }
        return None
    except Exception as e:
        print(f"Error fetching place {place_id}: {e}")
        return None


def build_route(
    candidates: List[Dict],
    start_lat: float,
    start_lng: float,
    min_distance: float = 300,
    max_distance: float = 1200,
) -> Optional[Dict]:
    """Build 3-step route using greedy approach by geo proximity"""
    if len(candidates) < 3:
        return None

    for candidate in candidates:
        candidate["distance_from_start"] = haversine_distance(
            start_lat, start_lng, candidate["lat"], candidate["lng"]
        )

    candidates.sort(key=lambda x: x["distance_from_start"])
    route = [candidates[0]]
    current_lat, current_lng = candidates[0]["lat"], candidates[0]["lng"]

    for _ in range(2):
        best_next = None
        best_distance = float("inf")
        for candidate in candidates:
            if candidate["id"] in [p["id"] for p in route]:
                continue
            distance = haversine_distance(
                current_lat, current_lng, candidate["lat"], candidate["lng"]
            )
            if min_distance <= distance <= max_distance and distance < best_distance:
                best_next = candidate
                best_distance = distance
        if best_next:
            route.append(best_next)
            current_lat, current_lng = best_next["lat"], best_next["lng"]
        else:
            for candidate in candidates:
                if candidate["id"] not in [p["id"] for p in route]:
                    route.append(candidate)
                    current_lat, current_lng = candidate["lat"], candidate["lng"]
                    break

    total_distance = 0
    for i in range(len(route) - 1):
        total_distance += haversine_distance(
            route[i]["lat"], route[i]["lng"], route[i + 1]["lat"], route[i + 1]["lng"]
        )

    return {
        "steps": [place["id"] for place in route],
        "total_distance_m": round(total_distance),
        "fit_score": 0.0,
    }


def calculate_fit_score(
    route: Dict,
    candidates: List[Dict],
    vibe: str,
    intents: List[str],
) -> float:
    """Calculate fit score for the route"""
    if not route or not candidates:
        return 0.0

    route_places = [c for c in candidates if c["id"] in route["steps"]]

    match_score = 0.0
    for place in route_places:
        place_tags = place.get("tags_json", [])
        place_vibe = place.get("vibe_json", {})
        intent_matches = sum(
            1 for intent in intents if intent.lower() in [tag.lower() for tag in place_tags]
        )
        match_score += intent_matches / len(intents)
        if vibe and place_vibe.get("atmosphere") == vibe:
            match_score += 0.5
    match_score = min(1.0, match_score / len(route_places))

    geo_score = 1.0 / (1.0 + route["total_distance_m"] / 1000.0)
    rating_score = sum(place.get("rating", 0) for place in route_places) / (
        len(route_places) * 5.0
    )
    districts = set(place.get("district", "") for place in route_places)
    diversity_score = len(districts) / len(route_places)

    fit_score = (
        0.5 * match_score
        + 0.25 * geo_score
        + 0.15 * rating_score
        + 0.1 * diversity_score
    )
    return round(fit_score, 3)
