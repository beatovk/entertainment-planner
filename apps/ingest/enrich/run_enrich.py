#!/usr/bin/env python3
"""
Place Enrichment Runner
Reads from raw.db, enriches data, and writes to clean.db
"""
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from enricher import PlaceEnricher
from providers.maps_stub import GoogleMapsProvider, MapsStubProvider

from logger import logger


class EnrichmentRunner:
    """Runs the enrichment process"""
    
    def __init__(self, raw_db: str = "raw.db", clean_db: str = "clean.db", use_google_maps: bool = True):
        self.raw_db = raw_db
        self.clean_db = clean_db
        
        # Choose provider based on preference
        if use_google_maps:
            logger.info("🔍 Using Google Maps provider for real-time enrichment")
            self.enricher = PlaceEnricher(GoogleMapsProvider())
        else:
            logger.info("📋 Using stub provider for testing")
            self.enricher = PlaceEnricher(MapsStubProvider())
    
    def get_latest_raw_places(self, limit: int) -> List[Dict]:
        """Get latest N rows from raw_places with quality filtering"""
        conn = sqlite3.connect(self.raw_db)
        cursor = conn.cursor()
        
        # Get places with good names (not too long, not generic)
        cursor.execute('''
            SELECT id, source, source_url, name_raw, description_raw, address_raw, raw_json, fetched_at
            FROM raw_places
            WHERE LENGTH(name_raw) BETWEEN 3 AND 100  -- Reasonable name length
            AND name_raw NOT LIKE '%about%'  -- Skip generic descriptions
            AND name_raw NOT LIKE '%news%'
            AND name_raw NOT LIKE '%review%'
            AND name_raw NOT LIKE '%Ethiopia%'
            AND name_raw NOT LIKE '%Japan%'
            AND name_raw NOT LIKE '%Spain%'
            ORDER BY id ASC  -- Get first entries (usually better quality)
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'source': row[1],
                'source_url': row[2],
                'name_raw': row[3],
                'description_raw': row[4],
                'address_raw': row[5],
                'raw_json': row[6],
                'fetched_at': row[7]
            }
            for row in rows
        ]
    
    def create_clean_buffer_table(self):
        """Create clean_buffer table if it doesn't exist"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clean_buffer (
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
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def enrich_and_insert(self, raw_places: List[Dict], city: str) -> int:
        """Enrich places and insert into clean_buffer"""
        self.create_clean_buffer_table()
        
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for raw_place in raw_places:
            try:
                # Enrich the place
                enrichment = self.enricher.enrich(
                    raw_place['name_raw'],
                    raw_place['address_raw'],
                    city
                )
                
                # Parse raw JSON for additional data
                raw_data = json.loads(raw_place['raw_json']) if raw_place['raw_json'] else {}
                
                # Extract tags and vibe from raw data
                tags = raw_data.get('tags', [])
                vibe = {
                    'atmosphere': 'mixed',
                    'crowd': 'mixed',
                    'music': 'various'
                }
                
                # Insert into clean_buffer
                cursor.execute('''
                    INSERT INTO clean_buffer (
                        name, summary_160, full_description, lat, lng, district, city,
                        price_level, rating, ratings_count, hours_json, phone, site,
                        gmap_url, photos_json, tags_json, vibe_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    raw_place['name_raw'],
                    raw_place['description_raw'][:160] if raw_place['description_raw'] else None,
                    raw_place['description_raw'],
                    enrichment.lat,
                    enrichment.lng,
                    None,  # district - could be extracted from address later
                    city,
                    enrichment.price_level,
                    enrichment.rating,
                    enrichment.ratings_count,
                    enrichment.hours_json,
                    enrichment.phone,
                    enrichment.site,
                    enrichment.gmap_url,
                    json.dumps([]),  # photos_json - empty for now
                    json.dumps(tags),
                    json.dumps(vibe),
                    datetime.now().isoformat()
                ))
                
                inserted_count += 1
                
            except Exception as e:
                logger.error(f"Error enriching {raw_place['name_raw']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count
    
    def upsert_to_places(self) -> int:
        """Upsert from clean_buffer to places table"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        # Get count before upsert
        cursor.execute('SELECT COUNT(*) FROM places')
        count_before = cursor.fetchone()[0]
        
        # Upsert from buffer to places (using name as unique key)
        cursor.execute('''
            INSERT OR REPLACE INTO places (
                name, summary_160, full_description, lat, lng, district, city,
                price_level, rating, ratings_count, hours_json, phone, site,
                gmap_url, photos_json, tags_json, vibe_json, updated_at, quality_score
            )
            SELECT 
                name, summary_160, full_description, lat, lng, district, city,
                price_level, rating, ratings_count, hours_json, phone, site,
                gmap_url, photos_json, tags_json, vibe_json, updated_at, 0.8
            FROM clean_buffer
            WHERE name IS NOT NULL AND name != ''
        ''')
        
        # Get count after upsert
        cursor.execute('SELECT COUNT(*) FROM places')
        count_after = cursor.fetchone()[0]
        
        # Clear buffer
        cursor.execute('DELETE FROM clean_buffer')
        
        conn.commit()
        conn.close()
        
        return count_after - count_before
    
    def run(self, limit: int, city: str) -> Dict[str, int]:
        """Main enrichment process"""
        logger.info(f"🚀 Starting enrichment process for {limit} places in {city}...")
        
        # Get latest raw places
        raw_places = self.get_latest_raw_places(limit)
        logger.info(f"📥 Found {len(raw_places)} raw places to enrich")
        
        # Enrich and insert into buffer
        enriched_count = self.enrich_and_insert(raw_places, city)
        logger.info(f"💾 Enriched and inserted {enriched_count} places into clean_buffer")
        
        # Upsert to places table
        upserted_count = self.upsert_to_places()
        logger.info(f"🔄 Upserted {upserted_count} places to clean.places")
        
        return {
            'raw_count': len(raw_places),
            'enriched_count': enriched_count,
            'upserted_count': upserted_count
        }

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Place Enrichment Runner")
    parser.add_argument("--limit", type=int, default=10, help="Number of places to enrich (default: 10)")
    parser.add_argument("--city", default="bangkok", help="City for enrichment (default: bangkok)")
    parser.add_argument("--raw-db", default="raw.db", help="Raw database path (default: raw.db)")
    parser.add_argument("--clean-db", default="clean.db", help="Clean database path (default: clean.db)")
    
    args = parser.parse_args()
    
    # Ensure databases exist
    if not Path(args.raw_db).exists():
        logger.error(f"❌ Raw database {args.raw_db} not found. Run timeout parser first.")
        return 1
    
    if not Path(args.clean_db).exists():
        logger.error(f"❌ Clean database {args.clean_db} not found. Run db_init.py first.")
        return 1
    
    # Determine provider based on arguments
    use_google_maps = True  # Default to Google Maps
    
    # Run enrichment
    runner = EnrichmentRunner(args.raw_db, args.clean_db, use_google_maps)
    results = runner.run(args.limit, args.city)
    
    logger.info("\n✅ Enrichment completed!")
    logger.info(f"   Raw places processed: {results['raw_count']}")
    logger.info(f"   Places enriched: {results['enriched_count']}")
    logger.info(f"   Places upserted: {results['upserted_count']}")
    
    return 0

if __name__ == "__main__":
    exit(main())
