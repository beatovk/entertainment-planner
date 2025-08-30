"""
Tests for SearchProvider implementation
"""
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from provider import LocalSearchProvider

def test_deterministic_ordering():
    """Test that kNN search returns deterministic ordering for mock data"""
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize provider
        provider = LocalSearchProvider(temp_db.name)
        
        # Create tables
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE VIRTUAL TABLE fts_places USING FTS5 (
                name, summary_160, tags
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE embeddings (
                doc_id INTEGER PRIMARY KEY,
                vector BLOB,
                dim INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Index mock documents
        mock_docs = [
            (1, "Tom Yum Goong Master - Authentic Thai tom yum soup with fresh prawns"),
            (2, "Lumpini Park - Central Bangkok green oasis with walking paths"),
            (3, "Sky Bar Bangkok - Luxury rooftop bar with panoramic city views"),
            (4, "Street Food Markets - Explore Bangkok's vibrant street food scene"),
            (5, "Traditional Thai Massage - Experience authentic Thai massage treatments")
        ]
        
        for doc_id, text in mock_docs:
            provider.index(doc_id, text)
        
        # Test kNN search
        query = "tom yum"
        results = provider.knn(query, 5)
        
        # Verify results
        assert len(results) > 0, "kNN should return results"
        
        # Check that tom yum document is in top results
        doc_ids = [doc_id for doc_id, score in results]
        assert 1 in doc_ids[:3], "Tom yum document should be in top 3 results"
        
        # Verify deterministic ordering (same query should give same results)
        results2 = provider.knn(query, 5)
        assert results == results2, "kNN should be deterministic"
        
        print("✅ Test passed: kNN returns deterministic ordering")
        
        # Test FTS search
        fts_results = provider.fts("tom yum", 5)
        assert len(fts_results) > 0, "FTS search works"
        
        print("✅ Test passed: FTS search works")
        
    finally:
        # Cleanup
        os.unlink(temp_db.name)

if __name__ == "__main__":
    test_deterministic_ordering()
