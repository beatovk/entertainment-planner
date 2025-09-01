import os
import sys
import tempfile
import uuid

# Add project root and api directory to path to import services
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "apps", "api"))

from services.cache import CacheManager


def test_cache_set_and_get():
    db_path = os.path.join(tempfile.gettempdir(), f"cache_{uuid.uuid4().hex}.db")
    manager = CacheManager(db_path)
    key = manager.build_cache_key("city", "2024-01-01", "vibe", "b,a", 1.234, 2.345)
    manager.set(key, {"foo": "bar"})
    value, status, store = manager.get(key)
    assert status == "HIT"
    assert value == {"foo": "bar"}
    assert store in {"memory", "sqlite"}


def test_build_cache_key_normalizes_intents():
    manager = CacheManager(os.path.join(tempfile.gettempdir(), f"cache_{uuid.uuid4().hex}.db"))
    key1 = manager.build_cache_key("city", "day", "vibe", "b,a", 1, 1)
    key2 = manager.build_cache_key("city", "day", "vibe", "a,b", 1, 1)
    assert key1 == key2
