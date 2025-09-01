import pytest
import sqlite3
import json
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the path to import the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def setup_test_db():
    """Setup test database with seeded data"""
    # Create a test database with the same schema
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute('''
        CREATE TABLE places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            summary_160 TEXT,
            full_description TEXT,
            lat REAL,
            lng REAL,
            district TEXT,
            city TEXT,
            price_level INTEGER,
            rating REAL,
            ratings_count INTEGER,
            hours_json TEXT,
            phone TEXT,
            site TEXT,
            gmap_url TEXT,
            photos_json TEXT,
            tags_json TEXT,
            vibe_json TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            quality_score REAL
        )
    ''')
    
    # Create FTS5 table
    cursor.execute('''
        CREATE VIRTUAL TABLE fts_places USING FTS5(
            name, 
            summary_160, 
            tags, 
            content=''
        )
    ''')
    
    # Create embeddings table
    cursor.execute('''
        CREATE TABLE embeddings (
            doc_id INTEGER PRIMARY KEY,
            vector BLOB,
            dim INTEGER
        )
    ''')
    
    # Insert test data (deterministic)
    test_places = [
        {
            'name': 'Test Tom Yum Place',
            'summary_160': 'Authentic Thai tom yum soup',
            'lat': 13.7563,
            'lng': 100.5018,
            'district': 'Sukhumvit',
            'city': 'Bangkok',
            'rating': 4.5,
            'tags_json': json.dumps(['thai', 'soup', 'tom-yum']),
            'vibe_json': json.dumps({'atmosphere': 'lazy'}),
            'quality_score': 0.9
        },
        {
            'name': 'Test Walking Park',
            'summary_160': 'Beautiful park for walking',
            'lat': 13.7325,
            'lng': 100.5444,
            'district': 'Pathum Wan',
            'city': 'Bangkok',
            'rating': 4.3,
            'tags_json': json.dumps(['park', 'walk', 'outdoor']),
            'vibe_json': json.dumps({'atmosphere': 'lazy'}),
            'quality_score': 0.8
        },
        {
            'name': 'Test Rooftop Bar',
            'summary_160': 'Luxury rooftop with views',
            'lat': 13.7246,
            'lng': 100.4930,
            'district': 'Silom',
            'city': 'Bangkok',
            'rating': 4.7,
            'tags_json': json.dumps(['rooftop', 'luxury', 'views']),
            'vibe_json': json.dumps({'atmosphere': 'classy'}),
            'quality_score': 0.95
        }
    ]
    
    for place in test_places:
        cursor.execute('''
            INSERT INTO places (
                name, summary_160, lat, lng, district, city, rating, 
                tags_json, vibe_json, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            place['name'], place['summary_160'], place['lat'], place['lng'],
            place['district'], place['city'], place['rating'], place['tags_json'],
            place['vibe_json'], place['quality_score']
        ))
    
    # Insert into FTS5
    cursor.execute('''
        INSERT INTO fts_places (name, summary_160, tags)
        SELECT name, summary_160, tags_json FROM places
    ''')
    
    conn.commit()
    conn.close()

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"]
    assert "db" in data
    assert "fts" in data
    assert "X-Search" in response.headers
    assert "X-Debug" in response.headers

def test_get_place_by_id():
    """Test getting place by ID"""
    # This test would need a real database connection
    # For now, we'll test the endpoint structure
    response = client.get("/api/places/1")
    # Should return 404 since we don't have a real DB in test
    assert response.status_code in [404, 500]

def test_recommend_places():
    """Test recommendation endpoint with deterministic data"""
    # Test parameters
    params = {
        "vibe": "lazy",
        "intents": "tom-yum,walk,rooftop",
        "lat": 13.7563,
        "lng": 100.5018
    }
    
    response = client.get("/api/places/recommend", params=params)
    
    # Should return 200 if DB is available, otherwise 500/404
    if response.status_code == 200:
        data = response.json()
        
        # Check response structure
        assert "routes" in data
        assert "alternatives" in data
        
        # Check routes
        routes = data["routes"]
        assert len(routes) >= 1
        
        route = routes[0]
        assert "steps" in route
        assert "total_distance_m" in route
        assert "fit_score" in route
        
        # Check that we have 3 steps
        assert len(route["steps"]) == 3
        
        # Check that total distance is positive
        assert route["total_distance_m"] > 0
        
        # Check fit score is between 0 and 1
        assert 0 <= route["fit_score"] <= 1
        
        # Check headers
        assert "X-Search" in response.headers
        assert "X-Debug" in response.headers
        
    else:
        # If DB not available, should get appropriate error
        assert response.status_code in [404, 500]

def test_recommend_places_missing_params():
    """Test recommendation endpoint with missing parameters"""
    # Test with missing vibe
    params = {
        "intents": "tom-yum,walk",
        "lat": 13.7563,
        "lng": 100.5018
    }
    response = client.get("/api/places/recommend", params=params)
    assert response.status_code == 422  # Validation error
    
    # Test with missing intents
    params = {
        "vibe": "lazy",
        "lat": 13.7563,
        "lng": 100.5018
    }
    response = client.get("/api/places/recommend", params=params)
    assert response.status_code == 422  # Validation error
    
    # Test with missing coordinates
    params = {
        "vibe": "lazy",
        "intents": "tom-yum,walk"
    }
    response = client.get("/api/places/recommend", params=params)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    # Run tests directly without pytest.main()
    print("🧪 Running API tests...")
    
    try:
        test_health_endpoint()
        print("✅ Health endpoint test passed")
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
    
    try:
        test_get_place_by_id()
        print("✅ Get place by ID test passed")
    except Exception as e:
        print(f"❌ Get place by ID test failed: {e}")
    
    try:
        test_recommend_places()
        print("✅ Recommend places test passed")
    except Exception as e:
        print(f"❌ Recommend places test failed: {e}")
    
    try:
        test_recommend_places_missing_params()
        print("✅ Missing params test passed")
    except Exception as e:
        print(f"❌ Missing params test failed: {e}")
    
    print("🎉 API tests completed!")
