#!/usr/bin/env python3
"""
Place Normalizer
Cleans text, generates summaries, proposes tags/vibes via ontology, computes quality scores
"""
import argparse
import sqlite3
import json
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class NormalizationResult:
    """Result of place normalization"""
    summary_160: str
    tags: List[str]
    vibe: Dict[str, str]
    quality_score: float

class PlaceNormalizer:
    """Normalizes place data using ontology rules"""
    
    def __init__(self, ontology_path: str = "packages/core/ontology.yaml"):
        self.ontology = self.load_ontology(ontology_path)
        self.pending_tags = set()
    
    def load_ontology(self, path: str) -> Dict:
        """Load ontology from YAML file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Ontology file {path} not found, using defaults")
            return {
                'vibes': ['lazy', 'cozy', 'scenic', 'vibrant', 'classy', 'budget', 'premium', 'date', 'solo'],
                'categories': ['food', 'coffee', 'bar', 'rooftop', 'park', 'gallery', 'live-music', 'night-market', 'cinema', 'workshop'],
                'cuisines': ['thai-spicy', 'tom-yum', 'seafood', 'vegan']
            }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s\-.,!?]', '', cleaned)
        return cleaned
    
    def generate_summary_160(self, description: str) -> str:
        """Generate 160-character summary from description"""
        if not description:
            return "No description available"
        
        cleaned = self.clean_text(description)
        
        # Truncate to 160 characters, preserving word boundaries
        if len(cleaned) <= 160:
            return cleaned
        
        # Find last complete word within 160 chars
        truncated = cleaned[:160]
        last_space = truncated.rfind(' ')
        
        if last_space > 140:  # Keep at least 20 chars from end
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def extract_tags(self, name: str, description: str, raw_json: str) -> List[str]:
        """Extract tags using keyword rules and ontology"""
        tags = set()
        
        # Parse raw JSON for additional context
        raw_data = {}
        try:
            if raw_json:
                raw_data = json.loads(raw_json)
        except:
            pass
        
        # Combine all text for analysis
        text = f"{name} {description} {json.dumps(raw_data)}".lower()
        
        # Category detection
        if any(word in text for word in ['restaurant', 'food', 'eat', 'dining']):
            tags.add('food')
        if any(word in text for word in ['coffee', 'tea', 'cafe']):
            tags.add('coffee')
        if any(word in text for word in ['bar', 'pub', 'lounge', 'cocktail']):
            tags.add('bar')
        if any(word in text for word in ['rooftop', 'roof-top', 'sky']):
            tags.add('rooftop')
        if any(word in text for word in ['park', 'garden', 'outdoor']):
            tags.add('park')
        if any(word in text for word in ['gallery', 'museum', 'art']):
            tags.add('gallery')
        if any(word in text for word in ['music', 'live', 'concert', 'performance']):
            tags.add('live-music')
        if any(word in text for word in ['market', 'bazaar', 'street-food']):
            tags.add('night-market')
        if any(word in text for word in ['cinema', 'movie', 'film', 'theater']):
            tags.add('cinema')
        if any(word in text for word in ['workshop', 'class', 'activity', 'creative']):
            tags.add('workshop')
        
        # Cuisine detection
        if any(word in text for word in ['thai', 'spicy', 'hot']):
            tags.add('thai-spicy')
        if any(word in text for word in ['tom yum', 'tom-yum', 'soup']):
            tags.add('tom-yum')
        if any(word in text for word in ['seafood', 'fish', 'shrimp', 'prawn']):
            tags.add('seafood')
        if any(word in text for word in ['vegan', 'vegetarian', 'plant-based']):
            tags.add('vegan')
        
        # Validate tags against ontology
        valid_tags = []
        for tag in tags:
            if tag in self.ontology['categories'] or tag in self.ontology['cuisines']:
                valid_tags.append(tag)
            else:
                self.pending_tags.add(tag)
        
        return valid_tags
    
    def propose_vibe(self, name: str, description: str, tags: List[str], price_level: int) -> Dict[str, str]:
        """Propose vibe based on context and price level"""
        vibe = {
            'atmosphere': 'mixed',
            'crowd': 'mixed',
            'music': 'various'
        }
        
        text = f"{name} {description}".lower()
        
        # Atmosphere based on keywords
        if any(word in text for word in ['cozy', 'intimate', 'warm']):
            vibe['atmosphere'] = 'cozy'
        elif any(word in text for word in ['scenic', 'view', 'beautiful']):
            vibe['atmosphere'] = 'scenic'
        elif any(word in text for word in ['vibrant', 'lively', 'energetic']):
            vibe['atmosphere'] = 'vibrant'
        elif any(word in text for word in ['classy', 'elegant', 'sophisticated']):
            vibe['atmosphere'] = 'classy'
        elif any(word in text for word in ['lazy', 'relaxed', 'peaceful']):
            vibe['atmosphere'] = 'lazy'
        
        # Crowd based on context
        if any(word in text for word in ['romantic', 'couple', 'date']):
            vibe['crowd'] = 'couples'
        elif any(word in text for word in ['family', 'children', 'kids']):
            vibe['atmosphere'] = 'families'
        elif any(word in text for word in ['solo', 'individual', 'single']):
            vibe['crowd'] = 'solo'
        elif any(word in text for word in ['party', 'group', 'social']):
            vibe['crowd'] = 'groups'
        
        # Music based on venue type
        if 'bar' in tags or 'live-music' in tags:
            vibe['music'] = 'live'
        elif 'rooftop' in tags:
            vibe['music'] = 'ambient'
        elif 'park' in tags:
            vibe['music'] = 'nature'
        elif 'gallery' in tags:
            vibe['music'] = 'quiet'
        
        return vibe
    
    def compute_quality_score(self, description: str, rating: float, ratings_count: int, 
                             updated_at: str) -> float:
        """Compute quality score based on coverage, ratings, and freshness"""
        
        # Coverage score (0-1): how complete the description is
        coverage_score = min(1.0, len(description or "") / 100.0)
        
        # Ratings score (0-1): normalized rating and count
        ratings_score = min(1.0, (rating or 0) / 5.0) * min(1.0, (ratings_count or 0) / 1000.0)
        
        # Freshness score (0-1): how recent the data is
        try:
            if updated_at:
                update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_old = (datetime.now() - update_date).days
                freshness_score = max(0.0, 1.0 - (days_old / 365.0))
            else:
                freshness_score = 0.5
        except:
            freshness_score = 0.5
        
        # Weighted combination
        w1, w2, w3 = 0.4, 0.4, 0.2  # coverage, ratings, freshness
        quality_score = w1 * coverage_score + w2 * ratings_score + w3 * freshness_score
        
        return round(quality_score, 3)
    
    def normalize_place(self, place_data: Dict) -> NormalizationResult:
        """Normalize a single place"""
        
        # Generate summary
        summary_160 = self.generate_summary_160(place_data.get('full_description', ''))
        
        # Extract tags
        tags = self.extract_tags(
            place_data.get('name', ''),
            place_data.get('full_description', ''),
            place_data.get('', '{}')
        )
        
        # Propose vibe
        vibe = self.propose_vibe(
            place_data.get('name', ''),
            place_data.get('full_description', ''),
            tags,
            place_data.get('price_level', 2)
        )
        
        # Compute quality score
        quality_score = self.compute_quality_score(
            place_data.get('full_description', ''),
            place_data.get('rating', 0),
            place_data.get('ratings_count', 0),
            place_data.get('updated_at', '')
        )
        
        return NormalizationResult(
            summary_160=summary_160,
            tags=tags,
            vibe=vibe,
            quality_score=quality_score
        )

class NormalizationRunner:
    """Runs the normalization process"""
    
    def __init__(self, clean_db: str = "clean.db"):
        self.clean_db = clean_db
        self.normalizer = PlaceNormalizer()
    
    def get_places_to_normalize(self, limit: int) -> List[Dict]:
        """Get places that need normalization"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, full_description, tags_json, vibe_json, quality_score,
                   rating, ratings_count, price_level, updated_at
            FROM places
            WHERE summary_160 IS NULL OR tags_json IS NULL OR vibe_json IS NULL OR quality_score IS NULL
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'full_description': row[2],
                'tags_json': row[3],
                'vibe_json': row[4],
                'quality_score': row[5],
                'rating': row[6],
                'ratings_count': row[7],
                'price_level': row[8],
                'updated_at': row[9],
            }
            for row in rows
        ]
    
    def update_place(self, place_id: int, normalization: NormalizationResult):
        """Update place with normalized data"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE places SET
                summary_160 = ?,
                tags_json = ?,
                vibe_json = ?,
                quality_score = ?
            WHERE id = ?
        ''', (
            normalization.summary_160,
            json.dumps(normalization.tags),
            json.dumps(normalization.vibe),
            normalization.quality_score,
            place_id
        ))
        
        conn.commit()
        conn.close()
    
    def create_pending_tags_table(self):
        """Create pending_tags table for unknown tags"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE NOT NULL,
                context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def run(self, limit: int) -> Dict[str, int]:
        """Main normalization process"""
        print(f"🚀 Starting normalization process for {limit} places...")
        
        # Create pending_tags table
        self.create_pending_tags_table()
        
        # Get places to normalize
        places = self.get_places_to_normalize(limit)
        print(f"📥 Found {len(places)} places to normalize")
        
        normalized_count = 0
        
        for place in places:
            try:
                # Normalize the place
                normalization = self.normalizer.normalize_place(place)
                
                # Update the place
                self.update_place(place['id'], normalization)
                
                normalized_count += 1
                print(f"✅ Normalized: {place['name']} (quality: {normalization.quality_score})")
                
            except Exception as e:
                print(f"❌ Error normalizing {place['name']}: {e}")
                continue
        
        # Report pending tags
        if self.normalizer.pending_tags:
            print(f"⚠️  Pending tags found: {', '.join(self.normalizer.pending_tags)}")
        
        return {
            'total_places': len(places),
            'normalized_count': normalized_count,
            'pending_tags_count': len(self.normalizer.pending_tags)
        }

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Place Normalizer")
    parser.add_argument("--limit", type=int, default=10, help="Number of places to normalize (default: 10)")
    parser.add_argument("--clean-db", default="clean.db", help="Clean database path (default: clean.db)")
    
    args = parser.parse_args()
    
    # Ensure database exists
    if not Path(args.clean_db).exists():
        print(f"❌ Clean database {args.clean_db} not found. Run enrichment first.")
        return 1
    
    # Run normalization
    runner = NormalizationRunner(args.clean_db)
    results = runner.run(args.limit)
    
    print(f"\n✅ Normalization completed!")
    print(f"   Total places processed: {results['total_places']}")
    print(f"   Places normalized: {results['normalized_count']}")
    print(f"   Pending tags: {results['pending_tags_count']}")
    
    return 0

if __name__ == "__main__":
    exit(main())
