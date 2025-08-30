import json
import sqlite3
import time
import os
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

class MemoryTTLCache:
    """In-memory TTL cache using dictionary"""
    
    def __init__(self, default_ttl_days: int = 7):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl_days = default_ttl_days
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache if not expired"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry['expire_ts']:
            # Expired, remove from cache
            del self.cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl_days: Optional[int] = None) -> None:
        """Set value in memory cache with TTL"""
        ttl = ttl_days or self.default_ttl_days
        expire_ts = time.time() + (ttl * 24 * 3600)  # Convert days to seconds
        
        self.cache[key] = {
            'value': value,
            'expire_ts': expire_ts
        }
    
    def clear(self) -> None:
        """Clear all cached items"""
        self.cache.clear()

class SQLiteCache:
    """SQLite-based persistent cache"""
    
    def __init__(self, db_path: str = "clean.db"):
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """Ensure cache_entries table exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    stored_at TEXT NOT NULL,
                    ttl_seconds INTEGER NOT NULL
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_expiry 
                ON cache_entries(stored_at, ttl_seconds)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Warning: Could not create cache table: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache if not expired"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value_json, stored_at, ttl_seconds 
                FROM cache_entries 
                WHERE key = ?
            ''', (key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            value_json, stored_at_str, ttl_seconds = row
            
            # Check if expired
            stored_at = datetime.fromisoformat(stored_at_str)
            expire_time = stored_at + timedelta(seconds=ttl_seconds)
            
            if datetime.now() > expire_time:
                # Expired, remove from cache
                self._remove_expired(key)
                return None
            
            # Parse and return value
            return json.loads(value_json)
            
        except Exception as e:
            print(f"Warning: SQLite cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_days: int = 7) -> bool:
        """Set value in SQLite cache with TTL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            ttl_seconds = ttl_days * 24 * 3600
            stored_at = datetime.now().isoformat()
            value_json = json.dumps(value, ensure_ascii=False)
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries (key, value_json, stored_at, ttl_seconds)
                VALUES (?, ?, ?, ?)
            ''', (key, value_json, stored_at, ttl_seconds))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Warning: SQLite cache set error: {e}")
            return False
    
    def _remove_expired(self, key: str) -> None:
        """Remove expired entry from cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not remove expired cache entry: {e}")
    
    def cleanup_expired(self) -> int:
        """Clean up all expired entries, return count removed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find expired entries
            now = datetime.now().isoformat()
            cursor.execute('''
                SELECT key FROM cache_entries 
                WHERE datetime(stored_at) + (ttl_seconds || ' seconds') < datetime(?)
            ''', (now,))
            
            expired_keys = [row[0] for row in cursor.fetchall()]
            
            if expired_keys:
                placeholders = ','.join(['?' for _ in expired_keys])
                cursor.execute(f'DELETE FROM cache_entries WHERE key IN ({placeholders})', expired_keys)
                conn.commit()
            
            conn.close()
            return len(expired_keys)
            
        except Exception as e:
            print(f"Warning: Cache cleanup error: {e}")
            return 0

class CacheManager:
    """Two-layer cache manager with memory and SQLite"""
    
    def __init__(self, db_path: str = "clean.db"):
        self.memory_cache = MemoryTTLCache()
        self.sqlite_cache = SQLiteCache(db_path)
        self.default_ttl_days = int(os.getenv('WP_CACHE_TTL_DAYS', '7'))
    
    def get(self, key: str) -> Tuple[Optional[Any], str, str]:
        """
        Get value from cache layers
        Returns: (value, cache_status, cache_store)
        """
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value, "HIT", "memory"
        
        # Try SQLite cache
        value = self.sqlite_cache.get(key)
        if value is not None:
            # Store in memory for faster subsequent access
            self.memory_cache.set(key, value, self.default_ttl_days)
            return value, "HIT", "sqlite"
        
        # Cache miss
        return None, "MISS", "compute"
    
    def set(self, key: str, value: Any, ttl_days: Optional[int] = None) -> None:
        """Set value in both cache layers"""
        ttl = ttl_days or self.default_ttl_days
        
        # Store in memory
        self.memory_cache.set(key, value, ttl)
        
        # Store in SQLite (async-like, don't block)
        try:
            self.sqlite_cache.set(key, value, ttl)
        except Exception as e:
            print(f"Warning: Could not persist to SQLite cache: {e}")
    
    def build_cache_key(self, city: str, day: str, vibe: str, intents: str, 
                       lat: float, lng: float) -> str:
        """
        Build cache key with coordinate bucketing to avoid key explosion
        Bucket coordinates by ~0.01 degrees (~1km at equator)
        """
        lat_bucket = round(lat, 2)
        lng_bucket = round(lng, 2)
        
        # Normalize intents (sort to ensure consistent keys)
        intent_list = sorted([intent.strip() for intent in intents.split(',')])
        normalized_intents = ','.join(intent_list)
        
        return f"v2:{city}:{day}:{vibe}:{normalized_intents}:{lat_bucket}:{lng_bucket}"
    
    def clear_all(self) -> None:
        """Clear all caches"""
        self.memory_cache.clear()
        # Note: SQLite cleanup is handled by TTL expiration
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_count = len(self.memory_cache.cache)
        sqlite_count = 0
        
        try:
            conn = sqlite3.connect(self.sqlite_cache.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            sqlite_count = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass
        
        return {
            'memory_entries': memory_count,
            'sqlite_entries': sqlite_count,
            'default_ttl_days': self.default_ttl_days
        }
