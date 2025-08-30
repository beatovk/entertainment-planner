import sqlite3
import json
from datetime import datetime
from pathlib import Path

def init_raw_db():
    """Initialize raw.db with raw_places table"""
    conn = sqlite3.connect('raw.db')
    cursor = conn.cursor()
    
    # Create raw_places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_url TEXT,
            name_raw TEXT NOT NULL,
            description_raw TEXT,
            address_raw TEXT,
            raw_json TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create unique partial index
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_places_unique 
        ON raw_places(source, name_raw, address_raw) 
        WHERE source IS NOT NULL AND name_raw IS NOT NULL AND address_raw IS NOT NULL
    ''')
    
    conn.commit()
    conn.close()
    print("✅ raw.db initialized with raw_places table")

def init_clean_db():
    """Initialize clean.db with places, embeddings, and FTS5 tables"""
    conn = sqlite3.connect('clean.db')
    cursor = conn.cursor()
    
    # Create places table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
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
    
    # Create embeddings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            doc_id INTEGER PRIMARY KEY,
            vector BLOB,
            dim INTEGER
        )
    ''')
    
    # Create FTS5 table
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_places USING FTS5(
            name, 
            summary_160, 
            tags, 
            content=''
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ clean.db initialized with places, embeddings, and FTS5 tables")

def seed_mock_data():
    """Seed clean.db with 3 mock Bangkok places"""
    conn = sqlite3.connect('clean.db')
    cursor = conn.cursor()
    
    mock_places = [
        {
            'name': 'Tom Yum Goong Master',
            'summary_160': 'Authentic Thai tom yum soup with fresh prawns and aromatic herbs',
            'full_description': 'Famous for their signature tom yum soup, this restaurant serves traditional Thai cuisine in a cozy setting. Known for using fresh local ingredients and authentic recipes passed down through generations.',
            'lat': 13.7563,
            'lng': 100.5018,
            'district': 'Sukhumvit',
            'city': 'Bangkok',
            'price_level': 2,
            'rating': 4.6,
            'ratings_count': 1247,
            'hours_json': json.dumps({'monday': '11:00-22:00', 'tuesday': '11:00-22:00', 'wednesday': '11:00-22:00', 'thursday': '11:00-22:00', 'friday': '11:00-22:00', 'saturday': '11:00-22:00', 'sunday': '11:00-22:00'}),
            'phone': '+66 2 123 4567',
            'site': 'https://tomyum-master.com',
            'gmap_url': 'https://maps.google.com/?q=Tom+Yum+Master',
            'photos_json': json.dumps(['photo1.jpg', 'photo2.jpg', 'photo3.jpg']),
            'tags_json': json.dumps(['thai', 'soup', 'authentic', 'local']),
            'vibe_json': json.dumps({'atmosphere': 'cozy', 'crowd': 'mixed', 'music': 'traditional'}),
            'quality_score': 0.92
        },
        {
            'name': 'Lumpini Park',
            'summary_160': 'Central Bangkok green oasis with walking paths, lake, and outdoor activities',
            'full_description': 'Bangkok\'s largest and most famous public park, offering a peaceful escape from the bustling city. Features walking and jogging paths, a large lake for paddle boating, outdoor exercise equipment, and plenty of shade from ancient trees.',
            'lat': 13.7325,
            'lng': 100.5444,
            'district': 'Pathum Wan',
            'city': 'Bangkok',
            'price_level': 0,
            'rating': 4.4,
            'ratings_count': 8923,
            'hours_json': json.dumps({'monday': '04:30-22:00', 'tuesday': '04:30-22:00', 'wednesday': '04:30-22:00', 'thursday': '04:30-22:00', 'friday': '04:30-22:00', 'saturday': '04:30-22:00', 'sunday': '04:30-22:00'}),
            'phone': '+66 2 252 7006',
            'site': 'https://www.bangkok.go.th/lumpini',
            'gmap_url': 'https://maps.google.com/?q=Lumpini+Park',
            'photos_json': json.dumps(['park1.jpg', 'park2.jpg', 'lake.jpg']),
            'tags_json': json.dumps(['park', 'outdoor', 'nature', 'exercise', 'free']),
            'vibe_json': json.dumps({'atmosphere': 'peaceful', 'crowd': 'families', 'music': 'nature'}),
            'quality_score': 0.88
        },
        {
            'name': 'Sky Bar Bangkok',
            'summary_160': 'Luxury rooftop bar with panoramic city views and craft cocktails',
            'full_description': 'Perched on the 63rd floor, this exclusive rooftop bar offers breathtaking 360-degree views of Bangkok\'s skyline. Serves premium cocktails, fine wines, and gourmet snacks in an elegant, sophisticated atmosphere perfect for special occasions.',
            'lat': 13.7246,
            'lng': 100.4930,
            'district': 'Silom',
            'city': 'Bangkok',
            'price_level': 4,
            'rating': 4.7,
            'ratings_count': 2156,
            'hours_json': json.dumps({'monday': '18:00-01:00', 'tuesday': '18:00-01:00', 'wednesday': '18:00-01:00', 'thursday': '18:00-01:00', 'friday': '18:00-01:00', 'saturday': '18:00-01:00', 'sunday': '18:00-01:00'}),
            'phone': '+66 2 624 9999',
            'site': 'https://skybar-bangkok.com',
            'gmap_url': 'https://maps.google.com/?q=Sky+Bar+Bangkok',
            'photos_json': json.dumps(['view1.jpg', 'view2.jpg', 'cocktail.jpg']),
            'tags_json': json.dumps(['rooftop', 'luxury', 'cocktails', 'views', 'romantic']),
            'vibe_json': json.dumps({'atmosphere': 'sophisticated', 'crowd': 'upscale', 'music': 'ambient'}),
            'quality_score': 0.95
        }
    ]
    
    for place in mock_places:
        cursor.execute('''
            INSERT INTO places (
                name, summary_160, full_description, lat, lng, district, city,
                price_level, rating, ratings_count, hours_json, phone, site,
                gmap_url, photos_json, tags_json, vibe_json, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            place['name'], place['summary_160'], place['full_description'],
            place['lat'], place['lng'], place['district'], place['city'],
            place['price_level'], place['rating'], place['ratings_count'],
            place['hours_json'], place['phone'], place['site'],
            place['gmap_url'], place['photos_json'], place['tags_json'],
            place['vibe_json'], place['quality_score']
        ))
    
    # Update FTS5 table
    pass
    cursor.execute('''
        INSERT INTO fts_places (name, summary_160, tags)
        SELECT name, summary_160, tags_json FROM places
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Mock data seeded into clean.db")

def print_row_counts():
    """Print row counts for verification"""
    # Raw DB counts
    conn = sqlite3.connect('raw.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM raw_places')
    raw_count = cursor.fetchone()[0]
    conn.close()
    
    # Clean DB counts
    conn = sqlite3.connect('clean.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM places')
    places_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM embeddings')
    embeddings_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM fts_places')
    fts_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📊 Database Row Counts:")
    print(f"raw.db - raw_places: {raw_count}")
    print(f"clean.db - places: {places_count}")
    print(f"clean.db - embeddings: {embeddings_count}")
    print(f"clean.db - fts_places: {fts_count}")

def main():
    """Main initialization function"""
    print("🚀 Initializing Entertainment Planner Databases...")
    
    # Create databases directory if it doesn't exist
    Path('.').mkdir(exist_ok=True)
    
    # Initialize databases
    init_raw_db()
    init_clean_db()
    
    # Seed mock data
    seed_mock_data()
    
    # Print verification counts
    print_row_counts()
    
    print("\n✅ Database initialization complete!")

if __name__ == "__main__":
    main()
