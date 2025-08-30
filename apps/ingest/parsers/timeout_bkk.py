#!/usr/bin/env python3
"""
TimeOut Bangkok Parser
Extracts entertainment places from TimeOut Bangkok and inserts into raw.db
"""
import argparse
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
import time

class TimeOutBkkParser:
    """Parser for TimeOut Bangkok entertainment listings"""
    
    def __init__(self, db_path: str = "raw.db"):
        self.db_path = db_path
        self.source = "timeout"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def fetch_real_data(self, url: str, limit: int = 10) -> List[Dict]:
        """Fetch real data from TimeOut Bangkok URL"""
        try:
            print(f"🌐 Fetching data from: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse the cafes article structure
            places = []
            
            # Look for h3 headings with numbers (1.Place Name, 2.Place Name, etc.)
            # Based on debug analysis, TimeOut uses h3 for numbered places
            list_items = soup.find_all('h3', string=re.compile(r'^\d+\.'))
            
            if not list_items:
                # Alternative: look for any headings with numbers
                list_items = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'^\d+\.'))
            
            print(f"🔍 Found {len(list_items)} potential places")
            
            for i, item in enumerate(list_items[:limit]):
                try:
                    place_data = self._extract_place_data(item, soup)
                    if place_data:
                        places.append(place_data)
                        print(f"  ✅ Extracted: {place_data['name_raw']}")
                    
                    # Be respectful with requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ❌ Error extracting place {i+1}: {e}")
                    continue
            
            return places
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []
    
    def _extract_place_data(self, item, soup) -> Optional[Dict]:
        """Extract place data from a heading item"""
        try:
            # Get the text content
            text_content = item.get_text(strip=True)
            
            # Extract place name (remove the number prefix)
            name_match = re.search(r'^\d+\.\s*(.+)', text_content)
            if name_match:
                name_raw = name_match.group(1)
            else:
                name_raw = text_content
            
            # Look for description and address in the following content
            description_raw = ""
            address_raw = ""
            
            # Strategy: Look for content after this heading until the next heading
            current_element = item
            content_text = ""
            
            # Collect text from next siblings until we hit another heading
            while current_element.find_next_sibling():
                next_element = current_element.find_next_sibling()
                
                # Stop if we hit another heading
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                # Collect text content
                if next_element.name == 'p':
                    content_text += " " + next_element.get_text(strip=True)
                elif next_element.get_text(strip=True):
                    content_text += " " + next_element.get_text(strip=True)
                
                current_element = next_element
            
            # Extract description (first meaningful paragraph)
            paragraphs = content_text.split('.')
            for para in paragraphs:
                para = para.strip()
                if len(para) > 30 and not para.startswith('Address'):  # Meaningful description
                    description_raw = para
                    break
            
            # Extract address using patterns found in debug
            address_patterns = [
                r'Address[:\s]+([^\.]+)',
                r'([^\.]+(?:Road|Street|Soi|Alley)[^\.]*)',
                r'([^\.]+(?:Sukhumvit|Silom|Thonglor|Ekkamai|Sathorn)[^\.]*)'
            ]
            
            for pattern in address_patterns:
                address_match = re.search(pattern, content_text, re.IGNORECASE)
                if address_match:
                    address_raw = address_match.group(1).strip()
                    break
            
            # Extract image URL if available
            image_url = ""
            
            # Look for images in the same section
            current_element = item
            while current_element.find_next_sibling():
                next_element = current_element.find_next_sibling()
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                
                img_element = next_element.find('img')
                if img_element:
                    image_url = img_element.get('src') or img_element.get('data-src')
                    if image_url and not image_url.endswith('loading_icon.gif'):
                        break
                
                current_element = next_element
            
            # Look for additional metadata
            raw_json = {
                "title": name_raw,
                "category": "cafes",
                "source_type": "article",
                "image_url": image_url,
                "extracted_at": datetime.now().isoformat()
            }
            
            # Try to extract rating if available
            rating_match = re.search(r'(\d+\.?\d*)', text_content)
            if rating_match:
                try:
                    raw_json["rating"] = float(rating_match.group(1))
                except ValueError:
                    pass
            
            # Try to extract price range
            price_patterns = [r'\$+', r'Free', r'Budget', r'Mid-range', r'Luxury']
            for pattern in price_patterns:
                if re.search(pattern, content_text, re.IGNORECASE):
                    raw_json["price_range"] = pattern
                    break
            
            # Extract tags from text content
            tags = []
            tag_keywords = [
                'coffee', 'cafe', 'brunch', 'pastry', 'dessert', 'wine', 'bar',
                'rooftop', 'outdoor', 'minimalist', 'design', 'art', 'music',
                'pet-friendly', 'work-friendly', 'instagram', 'photography'
            ]
            
            text_lower = (text_content + " " + description_raw + " " + content_text).lower()
            for keyword in tag_keywords:
                if keyword in text_lower:
                    tags.append(keyword)
            
            if tags:
                raw_json["tags"] = tags
            
            return {
                "name_raw": name_raw,
                "description_raw": description_raw,
                "address_raw": address_raw,
                "source_url": "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025",
                "raw_json": raw_json
            }
            
        except Exception as e:
            print(f"    Error in _extract_place_data: {e}")
            return None
    
    def fetch_mock_data(self, limit: int = 10) -> List[Dict]:
        """Fetch mock TimeOut Bangkok data (simulates real HTTP requests)"""
        mock_data = [
            {
                "name_raw": "Bangkok's Best Rooftop Bars",
                "description_raw": "Discover the city's most spectacular rooftop venues with stunning skyline views and craft cocktails. From luxury hotel bars to hidden gems, experience Bangkok from above.",
                "address_raw": "Various locations across Bangkok",
                "source_url": "https://www.timeout.com/bangkok/bars-and-pubs/best-rooftop-bars",
                "raw_json": {
                    "title": "Bangkok's Best Rooftop Bars",
                    "category": "bars-and-pubs",
                    "rating": 4.8,
                    "price_range": "$$$",
                    "tags": ["rooftop", "cocktails", "views", "luxury"]
                }
            },
            {
                "name_raw": "Traditional Thai Massage Spas",
                "description_raw": "Experience authentic Thai massage and wellness treatments in serene spa environments. Traditional techniques passed down through generations for ultimate relaxation.",
                "address_raw": "Sukhumvit, Silom, and Old Town areas",
                "source_url": "https://www.timeout.com/bangkok/health-and-beauty/best-thai-massage",
                "raw_json": {
                "rating": 4.6,
                "price_range": "$$",
                "tags": ["massage", "wellness", "traditional", "relaxation"]
                }
            },
            {
                "name_raw": "Street Food Markets Tour",
                "description_raw": "Explore Bangkok's vibrant street food scene with guided tours through famous markets. Sample authentic Thai dishes from local vendors and learn about culinary traditions.",
                "address_raw": "Chinatown, Chatuchak Weekend Market, Sukhumvit Soi 38",
                "source_url": "https://www.timeout.com/bangkok/food-and-drink/street-food-markets",
                "raw_json": {
                    "title": "Street Food Markets Tour",
                    "category": "food-and-drink",
                    "rating": 4.9,
                    "price_range": "$",
                    "tags": ["street-food", "markets", "local", "authentic", "tours"]
                }
            },
            {
                "name_raw": "Lumpini Park Morning Activities",
                "description_raw": "Join locals for morning tai chi, jogging, and outdoor exercise in Bangkok's largest public park. Peaceful green space perfect for fitness and relaxation.",
                "address_raw": "Rama IV Road, Pathum Wan, Bangkok 10330",
                "source_url": "https://www.timeout.com/bangkok/things-to-do/lumpini-park-activities",
                "raw_json": {
                    "title": "Lumpini Park Morning Activities",
                    "category": "things-to-do",
                    "rating": 4.4,
                    "price_range": "Free",
                    "tags": ["park", "outdoor", "fitness", "nature", "free"]
                }
            },
            {
                "name_raw": "Silom Nightlife District",
                "description_raw": "Vibrant nightlife area with bars, clubs, and entertainment venues. Popular with both locals and tourists for evening entertainment and socializing.",
                "address_raw": "Silom Road, Bang Rak, Bangkok",
                "source_url": "https://www.timeout.com/bangkok/nightlife/silom-district",
                "raw_json": {
                    "title": "Silom Nightlife District",
                    "category": "nightlife",
                    "rating": 4.3,
                    "price_range": "$$",
                    "tags": ["nightlife", "bars", "clubs", "entertainment", "social"]
                }
            }
        ]
        
        return mock_data[:limit]
    
    def insert_raw_places(self, data: List[Dict]) -> int:
        """Insert raw places data into raw.db with deduplication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for item in data:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO raw_places 
                    (source, source_url, name_raw, description_raw, address_raw, raw_json, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.source,
                    item['source_url'],
                    item['name_raw'],
                    item['description_raw'],
                    item['address_raw'],
                    json.dumps(item['raw_json']),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    inserted_count += 1
                    
            except Exception as e:
                print(f"Error inserting {item['name_raw']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count
    
    def run(self, limit: int = 10, url: str = None, use_real: bool = False) -> int:
        """Main parser execution"""
        print(f"🚀 TimeOut Bangkok Parser - fetching {limit} items...")
        
        if use_real and url:
            print(f"🌐 Using real URL: {url}")
            data = self.fetch_real_data(url, limit)
        else:
            print("🧪 Using mock data")
            data = self.fetch_mock_data(limit)
        
        print(f"📥 Fetched {len(data)} items")
        
        # Insert into database
        inserted = self.insert_raw_places(data)
        print(f"💾 Inserted {inserted} new items into raw.db")
        
        return inserted

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="TimeOut Bangkok Parser")
    parser.add_argument("--limit", type=int, default=10, help="Number of items to fetch (default: 10)")
    parser.add_argument("--db", default="raw.db", help="Database path (default: raw.db)")
    parser.add_argument("--url", help="URL to parse (for real data)")
    parser.add_argument("--real", action="store_true", help="Use real web scraping instead of mock data")
    
    args = parser.parse_args()
    
    # Ensure database exists
    if not Path(args.db).exists():
        print(f"❌ Database {args.db} not found. Run db_init.py first.")
        return 1
    
    # Run parser
    parser_instance = TimeOutBkkParser(args.db)
    inserted = parser_instance.run(args.limit, args.url, args.real)
    
    print(f"✅ Parser completed. {inserted} items inserted.")
    return 0

if __name__ == "__main__":
    exit(main())
