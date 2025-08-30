#!/usr/bin/env python3
"""
Build Search Indices CLI
Rebuilds all search indices from clean.places
"""
import argparse
from pathlib import Path
from indexer import SearchIndexer

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Build Search Indices")
    parser.add_argument("--clean-db", default="clean.db", help="Clean database path (default: clean.db)")
    parser.add_argument("--verify", action="store_true", help="Verify indices after building")
    
    args = parser.parse_args()
    
    # Ensure database exists
    if not Path(args.clean_db).exists():
        print(f"❌ Clean database {args.clean_db} not found. Run enrichment first.")
        return 1
    
    # Build indices
    indexer = SearchIndexer(args.clean_db)
    results = indexer.build_indices()
    
    # Verify if requested
    if args.verify:
        verification = indexer.verify_indices()
        print(f"\n🔍 Index Verification:")
        print(f"   Places in DB: {verification['places_count']}")
        print(f"   FTS entries: {verification['fts_count']}")
        print(f"   Embeddings: {verification['embeddings_count']}")
    
    print(f"\n✅ Index building completed!")
    print(f"   Places processed: {results['total_places']}")
    print(f"   Places indexed: {results['indexed_count']}")
    
    return 0

if __name__ == "__main__":
    exit(main())
