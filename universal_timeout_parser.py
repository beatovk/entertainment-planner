#!/usr/bin/env python3
"""
Universal TimeOut parser that can handle different types of articles
and extract all places from various TimeOut URLs.
"""

import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class UniversalTimeOutParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def parse_article(self, url: str) -> List[Dict]:
        """Parse any TimeOut article and extract places"""
        try:
            print(f"\n🔍 Парсинг статьи: {url}")
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Determine article type and extract places accordingly
            places = []
            
            # Method 1: Look for numbered headings (like the cafes article)
            numbered_places = self._extract_numbered_places(soup, url)
            if numbered_places:
                print(f"📝 Найдено пронумерованных мест: {len(numbered_places)}")
                places.extend(numbered_places)
            
            # Method 2: Look for unnumbered place headings
            unnumbered_places = self._extract_unnumbered_places(soup, url)
            if unnumbered_places:
                print(f"📝 Найдено ненумерованных мест: {len(unnumbered_places)}")
                places.extend(unnumbered_places)
            
            # Method 3: Look for place names in article content
            content_places = self._extract_content_places(soup, url)
            if content_places:
                print(f"📝 Найдено мест в контенте: {len(content_places)}")
                places.extend(content_places)
            
            # Remove duplicates based on name and address
            unique_places = self._remove_duplicates(places)
            print(f"🎯 Всего уникальных мест: {len(unique_places)}")
            
            return unique_places
            
        except Exception as e:
            print(f"❌ Ошибка парсинга статьи {url}: {e}")
            return []

    def _extract_numbered_places(self, soup: BeautifulSoup, article_url: str) -> List[Dict]:
        """Extract places with numbered headings (1., 2., 3., etc.)"""
        places = []
        
        # Find all headings that might contain numbered places
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            
            # Check for numbered patterns
            if re.match(r'^\d+[\.\)]', heading_text):
                place = self._extract_place_from_heading(heading, heading_text, article_url, soup)
                if place:
                    places.append(place)
        
        return places

    def _extract_unnumbered_places(self, soup: BeautifulSoup, article_url: str) -> List[Dict]:
        """Extract places without numbered headings"""
        places = []
        
        # Look for headings that might be place names
        headings = soup.find_all(['h2', 'h3', 'h4'])
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            
            # Skip if it's clearly not a place name
            if (len(heading_text) < 3 or 
                heading_text.lower() in ['about', 'introduction', 'conclusion', 'related articles'] or
                re.match(r'^[A-Z\s]+$', heading_text) and len(heading_text) < 10):
                continue
            
            # Check if it looks like a place name
            if self._looks_like_place_name(heading_text):
                place = self._extract_place_from_heading(heading, heading_text, article_url, soup)
                if place:
                    places.append(place)
        
        return places

    def _extract_content_places(self, soup: BeautifulSoup, article_url: str) -> List[Dict]:
        """Extract places mentioned in article content"""
        places = []
        
        # Look for paragraphs that mention place names
        paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            
            # Look for patterns like "at [Place Name]" or "from [Place Name]"
            place_matches = re.findall(r'(?:at|from|in|near)\s+([A-Z][A-Za-z\s&\-\(\)]+)', text)
            
            for match in place_matches:
                if self._looks_like_place_name(match):
                    place = {
                        'name_raw': match.strip(),
                        'place_url': None,
                        'description_raw': text[:200] + "..." if len(text) > 200 else text,
                        'address_raw': "",
                        'image_url': "",
                        'categories': [],
                        'district': None,
                        'article_url': article_url,
                        'extraction_method': 'content_mention'
                    }
                    places.append(place)
        
        return places

    def _looks_like_place_name(self, text: str) -> bool:
        """Check if text looks like a place name"""
        # Must be at least 3 characters
        if len(text) < 3:
            return False
        
        # Must start with capital letter
        if not text[0].isupper():
            return False
        
        # Must contain letters (not just numbers/symbols)
        if not re.search(r'[A-Za-z]', text):
            return False
        
        # Skip common non-place words
        skip_words = ['about', 'introduction', 'conclusion', 'related', 'articles', 'news', 'review']
        if text.lower() in skip_words:
            return False
        
        return True

    def _extract_place_from_heading(self, heading, heading_text: str, article_url: str, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract place information from a heading"""
        try:
            # Clean the name
            name_raw = re.sub(r'^\d+[\.\)]\s*', '', heading_text).strip()
            
            # Find place URL
            place_url = self._find_place_url(heading, article_url)
            
            # Find content container
            content_container = self._find_content_container(heading)
            
            # Extract description and address
            description_raw = self._extract_description_from_container(content_container)
            address_raw = self._extract_address_from_container(content_container)
            
            # Extract image
            image_url = self._extract_image_from_container(content_container)
            
            # Extract categories and district
            categories, district = self._extract_categories_and_district(content_container)
            
            place = {
                'name_raw': name_raw,
                'place_url': place_url,
                'description_raw': description_raw,
                'address_raw': address_raw,
                'image_url': image_url,
                'categories': categories,
                'district': district,
                'article_url': article_url,
                'extraction_method': 'heading'
            }
            
            return place
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения места '{heading_text}': {e}")
            return None

    def _find_content_container(self, heading) -> BeautifulSoup:
        """Find the container with content for this heading"""
        # Try to find the parent container
        current = heading
        for _ in range(5):  # Look up to 5 levels up
            current = current.parent
            if not current:
                break
            
            # Check if this container has substantial content
            text_content = current.get_text(strip=True)
            if len(text_content) > 100:  # Has substantial content
                return current
        
        # If no substantial container found, return the heading's parent
        return heading.parent

    def _extract_description_from_container(self, container) -> str:
        """Extract description from content container"""
        try:
            # Look for paragraphs
            paragraphs = container.find_all('p')
            description_parts = []
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                # Skip address paragraphs and very short text
                if (not text.lower().startswith('address') and 
                    not text.lower().startswith('location') and
                    len(text) > 30):
                    description_parts.append(text)
            
            return '\n\n'.join(description_parts) if description_parts else ""
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения описания: {e}")
            return ""

    def _extract_address_from_container(self, container) -> str:
        """Extract address from content container"""
        try:
            # Look for address patterns
            paragraphs = container.find_all('p')
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if (text.lower().startswith('address') or 
                    text.lower().startswith('location') or
                    'road' in text.lower() or
                    'soi' in text.lower() or
                    'sukhumvit' in text.lower()):
                    
                    # Clean up the address
                    address = re.sub(r'^(address|location):\s*', '', text, flags=re.IGNORECASE)
                    address = re.sub(r'\n+', ', ', address)
                    address = re.sub(r'\s+', ' ', address).strip()
                    return address
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения адреса: {e}")
            return ""

    def _extract_image_from_container(self, container) -> str:
        """Extract image URL from content container"""
        try:
            # Look for images
            images = container.find_all('img')
            
            for img in images:
                src = img.get('src', '')
                if 'media.timeout.com' in src:
                    return src
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения изображения: {e}")
            return ""

    def _extract_categories_and_district(self, container) -> Tuple[List[str], Optional[str]]:
        """Extract categories and district from content container"""
        try:
            categories = []
            district = None
            
            # Look for tags or categories
            tag_elements = container.find_all(['span', 'div', 'a'], class_=re.compile(r'badge|tag|category|district'))
            
            for tag in tag_elements:
                text = tag.get_text(strip=True)
                if text:
                    # Simple heuristic for district vs category
                    if any(word in text.lower() for word in ['sukhumvit', 'bang', 'thonglor', 'ekkamai', 'sathorn', 'yaowarat', 'phaya', 'ratcha', 'asoke', 'ari']):
                        district = text
                    else:
                        categories.append(text)
            
            return categories, district
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения категорий: {e}")
            return [], None

    def _find_place_url(self, heading, article_url: str) -> Optional[str]:
        """Find place URL from heading"""
        try:
            # Look for links in the heading
            link = heading.find('a')
            if link and link.get('href'):
                href = link.get('href')
                if not href.startswith('http'):
                    return urljoin(article_url, href)
                return href
            
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска URL: {e}")
            return None

    def _remove_duplicates(self, places: List[Dict]) -> List[Dict]:
        """Remove duplicate places based on name and address"""
        seen = set()
        unique_places = []
        
        for place in places:
            # Create a key based on name and address
            key = (place['name_raw'].lower(), place.get('address_raw', '').lower())
            
            if key not in seen:
                seen.add(key)
                unique_places.append(place)
        
        return unique_places

class UniversalTimeOutIntegration:
    def __init__(self, db_path: str = 'raw.db'):
        self.db_path = db_path
        self.parser = UniversalTimeOutParser()
        self.init_database()

    def init_database(self):
        """Initialize database table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    name_raw TEXT NOT NULL,
                    description_raw TEXT,
                    address_raw TEXT,
                    raw_json TEXT,
                    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create unique index for deduplication
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_places_unique
                ON raw_places(source, name_raw, address_raw)
                WHERE source IS NOT NULL AND name_raw IS NOT NULL AND address_raw IS NOT NULL
            ''')
            
            conn.commit()
            conn.close()
            print("✅ База данных инициализирована")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    def save_places(self, places: List[Dict], source: str) -> bool:
        """Save places to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for place in places:
                try:
                    # Prepare raw_json
                    raw_json = {
                        "article_url": place.get('article_url'),
                        "place_url": place.get('place_url'),
                        "image_url": place.get('image_url'),
                        "categories": place.get('categories', []),
                        "district": place.get('district'),
                        "extraction_method": place.get('extraction_method', 'unknown')
                    }
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO raw_places 
                        (source, source_url, name_raw, description_raw, address_raw, raw_json, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        source,
                        place.get('place_url'),
                        place['name_raw'],
                        place.get('description_raw', ''),
                        place.get('address_raw', ''),
                        json.dumps(raw_json),
                        datetime.now().isoformat()
                    ))
                    
                    saved_count += 1
                    
                except sqlite3.IntegrityError:
                    print(f"⚠️ Дубликат: {place['name_raw']}")
                    continue
                except Exception as e:
                    print(f"⚠️ Ошибка сохранения {place['name_raw']}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            print(f"✅ Сохранено {saved_count} мест в БД")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в БД: {e}")
            return False

    def parse_and_save_article(self, url: str, source: str) -> bool:
        """Parse article and save places to database"""
        print(f"\n🚀 Обработка статьи: {url}")
        
        # Parse the article
        places = self.parser.parse_article(url)
        
        if not places:
            print(f"❌ Места не найдены в статье: {url}")
            return False
        
        # Save to database
        success = self.save_places(places, source)
        
        if success:
            print(f"🎉 Успешно обработано {len(places)} мест из статьи")
            return True
        else:
            print(f"❌ Ошибка сохранения мест из статьи")
            return False

def main():
    """Main function to parse all articles"""
    # List of URLs to process
    urls = [
        "https://www.timeout.com/bangkok/restaurants/bangkoks-top-10-spots-for-health-conscious-dining",
        "https://www.timeout.com/bangkok/restaurants/best-breakfast-restaurants-in-bangkok",
        "https://www.timeout.com/bangkok/restaurants/bangkoks-best-garden-cafes",
        "https://www.timeout.com/bangkok/restaurants/best-juice-bars-around-bangkok-to-beat-the-heat",
        "https://www.timeout.com/bangkok/shopping/bookstores-cafe-coffee",
        "https://www.timeout.com/bangkok/news/thailand-leads-asias-50-best-restaurants-2025-032625",
        "https://www.timeout.com/bangkok/news/haoma-sustainable-indian-dining-thats-mighty-fine-042325",
        "https://www.timeout.com/bangkok/news/review-what-to-expect-from-the-shake-shack-x-potong-collab-051525",
        "https://www.timeout.com/bangkok/bakery-shops",
        "https://www.timeout.com/bangkok/restaurants/best-bakeries-to-find-perfect-sourdough-bread",
        "https://www.timeout.com/bangkok/restaurants/best-donut-shops-in-bangkok",
        "https://www.timeout.com/bangkok/restaurants/best-restaurants-and-cafes-asoke",
        "https://www.timeout.com/bangkok/restaurants/best-places-to-eat-iconsiam",
        "https://www.timeout.com/bangkok/restaurants/best-restaurants-ari",
        "https://www.timeout.com/bangkok/restaurants/best-restaurants-charoenkrung",
        "https://www.timeout.com/bangkok/best-restaurants-and-cafes-in-soi-sukhumvit-31"
    ]
    
    print("🚀 УНИВЕРСАЛЬНЫЙ ПАРСЕР TIMEOUT")
    print("=" * 60)
    print(f"📝 Всего статей для обработки: {len(urls)}")
    
    integration = UniversalTimeOutIntegration()
    
    total_places = 0
    successful_articles = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*50}")
        print(f"📰 СТАТЬЯ {i}/{len(urls)}")
        print(f"{'='*50}")
        
        # Extract source name from URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        source = f"timeout_{path_parts[-1]}" if path_parts else "timeout_unknown"
        
        success = integration.parse_and_save_article(url, source)
        if success:
            successful_articles += 1
        
        # Count places for this article
        places = integration.parser.parse_article(url)
        total_places += len(places)
        
        print(f"📊 Статистика по статье: {len(places)} мест")
    
    print(f"\n🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
    print(f"📊 Всего статей обработано: {successful_articles}/{len(urls)}")
    print(f"🎯 Всего мест найдено: {total_places}")
    
    # Show final database stats
    conn = sqlite3.connect('raw.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM raw_places WHERE source LIKE 'timeout_%'")
    total_in_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT source, COUNT(*) FROM raw_places WHERE source LIKE 'timeout_%' GROUP BY source")
    sources_stats = cursor.fetchall()
    
    conn.close()
    
    print(f"💾 Всего мест в базе данных: {total_in_db}")
    print(f"\n📊 Статистика по источникам:")
    for source, count in sources_stats:
        print(f"   {source}: {count} мест")

if __name__ == "__main__":
    main()
