import sqlite3
from packages.search.provider import LocalSearchProvider


def test_knn_returns_deterministic_order(tmp_path):
    """kNN search should return deterministic ordering."""
    db_path = tmp_path / "search.db"
    provider = LocalSearchProvider(str(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE VIRTUAL TABLE fts_places USING FTS5 (
            name, summary_160, tags
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE embeddings (
            doc_id INTEGER PRIMARY KEY,
            vector BLOB,
            dim INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

    mock_docs = [
        (1, "Tom Yum Goong Master - Authentic Thai tom yum soup with fresh prawns"),
        (2, "Lumpini Park - Central Bangkok green oasis with walking paths"),
        (3, "Sky Bar Bangkok - Luxury rooftop bar with panoramic city views"),
        (4, "Street Food Markets - Explore Bangkok's vibrant street food scene"),
        (5, "Traditional Thai Massage - Experience authentic Thai massage treatments"),
    ]

    for doc_id, text in mock_docs:
        provider.index(doc_id, text)

    query = "tom yum"
    results = provider.knn(query, 5)
    assert len(results) > 0
    doc_ids = [doc_id for doc_id, _ in results]
    assert 1 in doc_ids[:3]
    assert results == provider.knn(query, 5)

    fts_results = provider.fts("tom yum", 5)
    assert len(fts_results) > 0
