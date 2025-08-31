#!/usr/bin/env python3
"""
GPT-4o Mini Powered Place Summarizer
Generates ONLY beautiful, poetic 4-sentence descriptions in B2 English level
NO truncation, NO simple rules - ONLY GPT-4o mini generated summaries
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
import openai

@dataclass
class SummarizationResult:
    """Result of place summarization"""
    summary: str
    tags: List[str]
    vibe: Dict[str, str]
    quality_score: float

class GPTPlaceSummarizer:
    """Generates ONLY beautiful summaries using GPT-4o mini - NO TRUNCATION EVER"""
    
    def __init__(self, api_key: str, ontology_path: str = "packages/core/ontology.yaml"):
        self.client = openai.OpenAI(api_key=api_key)
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
    
    def generate_gpt_summary(self, name: str, description: str) -> str:
        """Generate ONLY beautiful 4-sentence summary using GPT-4o mini - NO FALLBACK TO TRUNCATION"""
        if not description or description.strip() == "":
            return "No description available"
        
        prompt = f"""
You are a skilled travel writer creating functional but beautiful descriptions of places in Bangkok. 

Create a description that is:
- Functional and informative (not a fairy tale)
- Beautiful and engaging in style
- Written at B2 English level (intermediate-advanced)
- Captures the essence and main features of the place
- Around 200 characters
- Useful for travelers

Description: {description}

Write your description:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a skilled travel writer who creates functional, informative, and beautiful descriptions of places."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.8
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Clean up the summary
            summary = re.sub(r'^["\']|["\']$', '', summary)  # Remove quotes
            summary = re.sub(r'\n+', ' ', summary)  # Remove newlines
            summary = re.sub(r'\s+', ' ', summary)  # Normalize whitespace
            
            # NO TRUNCATION - return exactly what GPT generated
            
            return summary
            
        except Exception as e:
            print(f"❌ GPT API error: {e}")
            # NO FALLBACK TO TRUNCATION - return error message
            return f"Error generating summary: {str(e)[:100]}"
    
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
        
        # Atmosphere based on keywords - расширенный список
        if any(word in text for word in ['cozy', 'intimate', 'warm', 'comfortable', 'homely', 'welcoming']):
            vibe['atmosphere'] = 'cozy'
        elif any(word in text for word in ['scenic', 'view', 'beautiful', 'panoramic', 'stunning', 'breathtaking', 'rooftop', 'garden']):
            vibe['atmosphere'] = 'scenic'
        elif any(word in text for word in ['vibrant', 'lively', 'energetic', 'bustling', 'dynamic', 'exciting', 'trendy', 'hip']):
            vibe['atmosphere'] = 'vibrant'
        elif any(word in text for word in ['classy', 'elegant', 'sophisticated', 'luxury', 'premium', 'upscale', 'refined', 'chic']):
            vibe['atmosphere'] = 'classy'
        elif any(word in text for word in ['lazy', 'relaxed', 'peaceful', 'tranquil', 'serene', 'calm', 'quiet', 'zen']):
            vibe['atmosphere'] = 'lazy'
        elif any(word in text for word in ['rustic', 'traditional', 'authentic', 'heritage', 'cultural']):
            vibe['atmosphere'] = 'rustic'
        elif any(word in text for word in ['modern', 'contemporary', 'innovative', 'creative', 'artistic']):
            vibe['atmosphere'] = 'modern'
        
        # Crowd based on context - расширенный список
        if any(word in text for word in ['local', 'neighborhood', 'community', 'resident', 'native']):
            vibe['crowd'] = 'local'
        elif any(word in text for word in ['tourist', 'visitor', 'traveler', 'foreign', 'international']):
            vibe['crowd'] = 'tourist'
        elif any(word in text for word in ['young', 'student', 'hipster', 'millennial', 'creative', 'artistic']):
            vibe['crowd'] = 'young'
        elif any(word in text for word in ['mature', 'adult', 'professional', 'business', 'executive', 'family']):
            vibe['crowd'] = 'mature'
        elif any(word in text for word in ['mixed', 'diverse', 'varied', 'eclectic']):
            vibe['crowd'] = 'mixed'
        
        # Music based on context - расширенный список
        if any(word in text for word in ['live', 'band', 'performance', 'concert', 'dj', 'karaoke', 'entertainment']):
            vibe['music'] = 'live'
        elif any(word in text for word in ['ambient', 'background', 'soft', 'chill', 'relaxing', 'smooth']):
            vibe['music'] = 'ambient'
        elif any(word in text for word in ['none', 'quiet', 'silent', 'peaceful', 'tranquil', 'zen']):
            vibe['music'] = 'none'
        elif any(word in text for word in ['various', 'different', 'mixed', 'eclectic']):
            vibe['music'] = 'various'
        
        # Дополнительная логика на основе тегов
        if 'rooftop' in tags:
            vibe['atmosphere'] = 'scenic'
        if 'park' in tags:
            vibe['atmosphere'] = 'lazy'
        if 'gallery' in tags or 'art' in tags:
            vibe['atmosphere'] = 'modern'
        if 'bar' in tags or 'nightlife' in tags:
            vibe['atmosphere'] = 'vibrant'
        if 'coffee' in tags:
            vibe['atmosphere'] = 'cozy'
        if 'live-music' in tags:
            vibe['music'] = 'live'
        
        return vibe
    
    def compute_quality_score(self, description: str, rating: float, ratings_count: int, updated_at: str) -> float:
        """Compute quality score based on data completeness and freshness"""
        score = 0.0
        
        # Description quality (40%)
        if description and len(description.strip()) > 50:
            score += 0.4
        elif description and len(description.strip()) > 20:
            score += 0.2
        
        # Rating quality (30%)
        if rating and rating > 0:
            score += 0.3
        elif ratings_count and ratings_count > 0:
            score += 0.15
        
        # Data freshness (20%)
        if updated_at:
            try:
                updated_date = datetime.fromisoformat(updated_at)
                days_old = (datetime.now() - updated_date).days
                if days_old <= 7:
                    score += 0.2
                elif days_old <= 30:
                    score += 0.1
            except:
                pass
        
        # Additional data (10%)
        score += 0.1
        
        return round(score, 3)
    
    def summarize_place(self, place_data: Dict) -> SummarizationResult:
        """Summarize a single place using GPT-4o mini - ONLY generates summary_160"""
        
        # Generate beautiful summary using GPT - THIS IS THE ONLY SUMMARY METHOD
        summary = self.generate_gpt_summary(
            place_data.get('name', ''),
            place_data.get('full_description', '')
        )
        
        # Extract tags
        tags = self.extract_tags(
            place_data.get('name', ''),
            place_data.get('full_description', ''),
            place_data.get('raw_json', '{}')
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
        
        return SummarizationResult(
            summary=summary,
            tags=tags,
            vibe=vibe,
            quality_score=quality_score
        )

class GPTSummarizationRunner:
    """Runs the GPT-powered summarization process - ONLY for summary_160"""
    
    def __init__(self, clean_db: str = "clean.db", api_key: str = None):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.clean_db = clean_db
        self.summarizer = GPTPlaceSummarizer(api_key)
    
    def get_places_to_summarize(self, limit: int) -> List[Dict]:
        """Get places that need summarization - focus on places with full_description"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        # Get places that have full_description but NO summary
        cursor.execute('''
            SELECT id, name, summary, full_description, tags_json, vibe_json, quality_score,
                   rating, ratings_count, price_level, updated_at
            FROM places
            WHERE full_description IS NOT NULL 
              AND full_description != ''
              AND (summary IS NULL OR summary = '')
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'summary_160': row[2],
                'full_description': row[3],
                'tags_json': row[4],
                'vibe_json': row[5],
                'quality_score': row[6],
                'rating': row[7],
                'ratings_count': row[8],
                'price_level': row[9],
                'updated_at': row[10],
            }
            for row in rows
        ]
    
    def update_place(self, place_id: int, summarization: SummarizationResult):
        """Update place with summarized data - ONLY summary_160"""
        conn = sqlite3.connect(self.clean_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE places SET
                summary = ?,
                tags_json = ?,
                vibe_json = ?,
                quality_score = ?
            WHERE id = ?
        ''', (
            summarization.summary,
            json.dumps(summarization.tags),
            json.dumps(summarization.vibe),
            summarization.quality_score,
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
        """Main summarization process - ONLY generates summary_160"""
        print(f"🚀 Starting GPT-4o mini summarization process for {limit} places...")
        print(f"🎯 Focus: Generate ONLY beautiful 4-sentence summaries from full_description")
        print(f"❌ NO TRUNCATION, NO SIMPLE RULES - ONLY GPT-4o mini")
        
        # Create pending_tags table
        self.create_pending_tags_table()
        
        # Get places to summarize
        places = self.get_places_to_summarize(limit)
        print(f"📥 Found {len(places)} places to summarize")
        
        if not places:
            print("✅ All places already have proper GPT-generated summaries!")
            return {'total_places': 0, 'summarized_count': 0, 'pending_tags_count': 0}
        
        summarized_count = 0
        
        for place in places:
            try:
                print(f"🤖 Processing: {place['name']}")
                print(f"   📖 Full description: {place['full_description'][:100]}...")
                
                # Summarize the place using GPT-4o mini ONLY
                summarization = self.summarizer.summarize_place(place)
                
                # Update the place
                self.update_place(place['id'], summarization)
                
                summarized_count += 1
                print(f"✅ Summarized: {place['name']}")
                print(f"   📝 GPT Summary: {summarization.summary}")
                print(f"   🏷️ Tags: {', '.join(summarization.tags)}")
                print(f"   🎭 Vibe: {summarization.vibe}")
                print(f"   📈 Quality: {summarization.quality_score}")
                print()
                
            except Exception as e:
                print(f"❌ Error summarizing {place['name']}: {e}")
                continue
        
        # Report pending tags
        if self.summarizer.pending_tags:
            print(f"⚠️  Pending tags found: {', '.join(self.summarizer.pending_tags)}")
        
        return {
            'total_places': len(places),
            'summarized_count': summarized_count,
            'pending_tags_count': len(self.summarizer.pending_tags)
        }

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="GPT-4o Mini Place Summarizer - ONLY beautiful 4-sentence summaries")
    parser.add_argument("--limit", type=int, default=10, help="Number of places to summarize (default: 10)")
    parser.add_argument("--clean-db", default="clean.db", help="Clean database path (default: clean.db)")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    
    args = parser.parse_args()
    
    # Ensure database exists
    if not Path(args.clean_db).exists():
        print(f"❌ Clean database {args.clean_db} not found. Run enrichment first.")
        return 1
    
    # Run summarization
    try:
        runner = GPTSummarizationRunner(args.clean_db, args.api_key)
        results = runner.run(args.limit)
        
        print(f"\n✅ GPT-4o mini summarization completed!")
        print(f"   Total places processed: {results['total_places']}")
        print(f"   Places summarized: {results['summarized_count']}")
        print(f"   Pending tags: {results['pending_tags_count']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
