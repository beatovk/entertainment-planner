from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import sqlite3
import json

from settings import settings

class SearchProvider(ABC):
    """Abstract interface for search providers"""
    
    @abstractmethod
    def index(self, doc_id: int, text: str) -> bool:
        """Index a document with given ID and text"""
        pass
    
    @abstractmethod
    def knn(self, query_text: str, top_k: int) -> List[Tuple[int, float]]:
        """Find top-k most similar documents using k-NN"""
        pass
    
    @abstractmethod
    def fts(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Full-text search using FTS5"""
        pass

class LocalSearchProvider(SearchProvider):
    """Local search provider using FTS5 + deterministic embeddings"""

    def __init__(self, db_path: str = settings.db_path):
        self.db_path = db_path
        self.embedding_dim = 64  # Fixed dimension for deterministic vectors
    
    def _compute_embedding(self, text: str) -> bytes:
        """Compute deterministic embedding using char n-gram hashing trick"""
        import hashlib
        
        # Simple char n-gram approach (n=3)
        n = 3
        ngrams = []
        text_lower = text.lower()
        
        for i in range(len(text_lower) - n + 1):
            ngrams.append(text_lower[i:i+n])
        
        # Hash n-grams to fixed-size vector
        vector = [0.0] * self.embedding_dim
        
        for ngram in ngrams:
            # Hash ngram to vector index
            hash_val = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
            idx = hash_val % self.embedding_dim
            vector[idx] += 1.0
        
        # Normalize vector
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x/norm for x in vector]
        
        # Convert to bytes
        import struct
        return struct.pack(f'{self.embedding_dim}f', *vector)
    
    def _cosine_similarity(self, vec1_bytes: bytes, vec2_bytes: bytes) -> float:
        """Compute cosine similarity between two vectors"""
        import struct
        
        vec1 = struct.unpack(f'{self.embedding_dim}f', vec1_bytes)
        vec2 = struct.unpack(f'{self.embedding_dim}f', vec2_bytes)
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return dot_product  # Vectors are already normalized
    
    def index(self, doc_id: int, text: str) -> bool:
        """Index a document with FTS5 and embeddings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert into FTS5
            cursor.execute('''
                INSERT OR REPLACE INTO fts_places (name, summary_160, tags)
                VALUES (?, ?, ?)
            ''', (text, text, text))
            
            # Compute and store embedding
            embedding = self._compute_embedding(text)
            cursor.execute('''
                INSERT OR REPLACE INTO embeddings (doc_id, vector, dim)
                VALUES (?, ?, ?)
            ''', (doc_id, embedding, self.embedding_dim))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error indexing doc {doc_id}: {e}")
            return False
    
    def knn(self, query_text: str, top_k: int) -> List[Tuple[int, float]]:
        """Find top-k most similar documents using k-NN on embeddings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get query embedding
            query_embedding = self._compute_embedding(query_text)
            
            # Get all document embeddings
            cursor.execute('SELECT doc_id, vector FROM embeddings')
            embeddings = cursor.fetchall()
            
            # Compute similarities
            similarities = []
            for doc_id, vec_bytes in embeddings:
                similarity = self._cosine_similarity(query_embedding, vec_bytes)
                similarities.append((doc_id, similarity))
            
            # Sort by similarity (descending) and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            conn.close()
            
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error in kNN search: {e}")
            return []
    
    def fts(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Full-text search using FTS5"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rowid, rank FROM fts_places 
                WHERE fts_places MATCH ? 
                ORDER BY rank
                LIMIT ?
            ''', (query, top_k))
            
            results = cursor.fetchall()
            conn.close()
            
            # Convert rank to similarity score (lower rank = higher score)
            return [(doc_id, 1.0 / (rank + 1)) for doc_id, rank in results]
            
        except Exception as e:
            print(f"Error in FTS search: {e}")
            return []
