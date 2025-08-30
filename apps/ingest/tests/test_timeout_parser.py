"""
Snapshot tests for TimeOut Bangkok parser
"""
import sqlite3
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parsers directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'parsers'))

from timeout_bkk import TimeOutBkkParser

def test_timeout_parser_inserts_3_rows():
    """Test that parser inserts exactly 3 rows into raw_places"""
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize parser with temp DB
        parser = TimeOutBkkParser(temp_db.name)
        
        # Create raw_places table
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE raw_places (
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
        conn.commit()
        conn.close()
        
        # Run parser with limit 3
        inserted = parser.run(3)
        
        # Verify exactly 3 rows inserted
        assert inserted == 3, f"Expected 3 rows, got {inserted}"
        
        # Verify database has 3 rows
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM raw_places')
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 3, f"Expected 3 rows in DB, got {count}"
        
        print("✅ Test passed: Parser inserted exactly 3 rows")
        
    finally:
        # Cleanup
        os.unlink(temp_db.name)

if __name__ == "__main__":
    test_timeout_parser_inserts_3_rows()
