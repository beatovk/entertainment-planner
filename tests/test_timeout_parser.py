import sqlite3
from apps.ingest.parsers.timeout_bkk import TimeOutBkkParser


def test_timeout_parser_inserts_3_rows(tmp_path):
    """Parser should insert exactly 3 rows into raw_places."""
    db_path = tmp_path / "raw.db"
    parser = TimeOutBkkParser(str(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
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
        """
    )
    conn.commit()
    conn.close()

    inserted = parser.run(3)
    assert inserted == 3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM raw_places")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3
