import sqlite3
import pytest


def test_connection_closed_on_exception(tmp_path):
    db_path = tmp_path / "test.db"

    def trigger():
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        trigger()

    # Connection should be closed automatically allowing a new connection
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
