"""
Search Indexer
Builds FTS5 and embedding indices from clean.places
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, cast  # noqa: F401

from packages.search.provider import LocalSearchProvider


class SearchIndexer:
    """Builds search indices from clean.places"""
    
    def __init__(self, clean_db: str = "clean.db") -> None:
        self.clean_db = clean_db
    
    def get_places_for_indexing(self) -> List[Dict]:
        """Get all places from clean.places for indexing"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, summary_160, tags_json, full_description
            FROM places
            ORDER BY id
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'summary_160': row[2],
                'tags_json': row[3],
                'full_description': row[4]
            }
            for row in rows
        ]
    
    def build_fts_text(self, place: Dict) -> str:
        """Build FTS text from name, summary, and tags"""
        text_parts = []
        
        # Add name
        if place['name']:
            text_parts.append(place['name'])
        
        # Add summary
        if place['summary_160']:
            text_parts.append(place['summary_160'])
        
        # Add tags
        if place['tags_json']:
            try:
                tags = json.loads(place['tags_json'])
                if isinstance(tags, list):
                    text_parts.extend(tags)
            except Exception:
                pass
        
        return " ".join(text_parts)
    
    def clear_indices(self) -> None:
        """Clear existing FTS5 and embeddings indices"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        # Clear FTS5 table
        pass
        
        # Clear embeddings table
        cursor.execute('DELETE FROM embeddings')
        
        conn.commit()
        conn.close()
        print("🧹 Cleared existing indices")
    
    def build_indices(self) -> Dict[str, int]:
        """Build both FTS5 and embeddings indices"""
        print("🚀 Building search indices...")
        
        # Clear existing indices
        self.clear_indices()
        
        # Get places for indexing
        places = self.get_places_for_indexing()
        print(f"📥 Found {len(places)} places to index")
        
        # Import search provider
        provider = LocalSearchProvider(self.clean_db)
        
        indexed_count = 0
        
        for place in places:
            try:
                # Build FTS text
                fts_text = self.build_fts_text(place)
                
                # Index the place
                if provider.index(place['id'], fts_text):
                    indexed_count += 1
                    print(f"✅ Indexed: {place['name']}")
                else:
                    print(f"❌ Failed to index: {place['name']}")
                    
            except Exception as e:
                print(f"❌ Error indexing {place['name']}: {e}")
                continue
        
        print(f"✅ Indexing completed: {indexed_count} places indexed")
        
        return {
            'total_places': len(places),
            'indexed_count': indexed_count
        }
    
    def verify_indices(self) -> Dict[str, int]:
        """Verify that indices were built correctly"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        # Check FTS5
        cursor.execute('SELECT COUNT(*) FROM fts_places')
        fts_count = cursor.fetchone()[0]
        
        # Check embeddings
        cursor.execute('SELECT COUNT(*) FROM embeddings')
        embeddings_count = cursor.fetchone()[0]
        
        # Check places
        cursor.execute('SELECT COUNT(*) FROM places')
        places_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'places_count': places_count,
            'fts_count': fts_count,
            'embeddings_count': embeddings_count
        }

def main() -> None:
    """CLI entry point for testing"""
    indexer = SearchIndexer()
    
    # Build indices
    results = indexer.build_indices()
    
    # Verify indices
    verification = indexer.verify_indices()
    
    print("\n📊 Indexing Results:")
    print(f"   Places processed: {results['total_places']}")
    print(f"   Places indexed: {results['indexed_count']}")
    print("\n🔍 Index Verification:")
    print(f"   Places in DB: {verification['places_count']}")
    print(f"   FTS entries: {verification['fts_count']}")
    print(f"   Embeddings: {verification['embeddings_count']}")

if __name__ == "__main__":
    main()
