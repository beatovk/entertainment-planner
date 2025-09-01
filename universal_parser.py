#!/usr/bin/env python3
"""
Универсальный парсер для поиска мест в статьях
Поддерживает различные форматы и количество мест
"""

import json
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


class UniversalPlaceParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def parse_article(self, url: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Парсит статью и извлекает все найденные места
        """
        try:
            print(f"🔍 Парсинг статьи: {url}")
            
            # Получаем HTML
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Пробуем разные стратегии парсинга
            places = []
            
            # Стратегия 1: Поиск по карточкам (div с классом card)
            places.extend(self._parse_card_based(soup, limit))
            
            # Стратегия 2: Поиск по заголовкам (h2, h3)
            if not places:
                places.extend(self._parse_heading_based(soup, limit))
            
            # Стратегия 3: Поиск по спискам (ul, ol)
            if not places:
                places.extend(self._parse_list_based(soup, limit))
            
            # Стратегия 4: Поиск по параграфам с названиями
            if not places:
                places.extend(self._parse_paragraph_based(soup, limit))
            
            # Стратегия 5: Поиск по ссылкам на места
            if not places:
                places.extend(self._parse_link_based(soup, limit))
            
            # Ограничиваем количество результатов
            if limit and len(places) > limit:
                places = places[:limit]
            
            print(f"✅ Найдено мест: {len(places)}")
            return places
            
        except Exception as e:
            print(f"❌ Ошибка при парсинге: {e}")
            return []
    
    def _parse_card_based(self, soup: BeautifulSoup, limit: Optional[int] = None) -> List[Dict]:
        """Парсинг по карточкам (div с классом card)"""
        places = []
        
        # Ищем карточки по классу
        cards = soup.find_all('div', class_='card')
        if not cards:
            # Пробуем другие варианты карточек
            cards = soup.find_all('div', class_=re.compile(r'card|item|place|venue|restaurant|cafe|bar'))
        
        for card in cards:
            place = self._extract_place_from_card(card)
            if place:
                places.append(place)
                if limit and len(places) >= limit:
                    break
        
        return places
    
    def _parse_heading_based(self, soup: BeautifulSoup, limit: Optional[int] = None) -> List[Dict]:
        """Парсинг по заголовкам"""
        places = []
        
        # Ищем заголовки h2, h3, h4
        headings = soup.find_all(['h2', 'h3', 'h4'])
        
        for heading in headings:
            text = heading.get_text(strip=True)
            if self._is_place_heading(text):
                place = self._extract_place_from_heading(heading)
                if place:
                    places.append(place)
                    if limit and len(places) >= limit:
                        break
        
        return places
    
    def _parse_list_based(self, soup: BeautifulSoup, limit: Optional[int] = None) -> List[Dict]:
        """Парсинг по спискам"""
        places = []
        
        # Ищем списки
        lists = soup.find_all(['ul', 'ol'])
        
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                place = self._extract_place_from_list_item(item)
                if place:
                    places.append(place)
                    if limit and len(places) >= limit:
                        break
            if limit and len(places) >= limit:
                break
        
        return places
    
    def _parse_paragraph_based(self, soup: BeautifulSoup, limit: Optional[int] = None) -> List[Dict]:
        """Парсинг по параграфам с названиями мест"""
        places = []
        
        # Ищем параграфы
        paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if self._contains_place_name(text):
                place = self._extract_place_from_paragraph(p)
                if place:
                    places.append(place)
                    if limit and len(places) >= limit:
                        break
        
        return places
    
    def _parse_link_based(self, soup: BeautifulSoup, limit: Optional[int] = None) -> List[Dict]:
        """Парсинг по ссылкам на места"""
        places = []
        
        # Ищем ссылки
        links = soup.find_all('a', href=True)
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if self._is_place_link(text, href):
                place = self._extract_place_from_link(link)
                if place:
                    places.append(place)
                    if limit and len(places) >= limit:
                        break
        
        return places
    
    def _extract_place_from_card(self, card) -> Optional[Dict]:
        """Извлекает информацию о месте из карточки"""
        try:
            # Ищем заголовок
            title_elem = card.find(['h2', 'h3', 'h4', 'h5'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Ищем описание
            desc_elem = card.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Ищем изображение
            img_elem = card.find('img')
            image_url = img_elem.get('src', '') if img_elem else ""
            
            # Ищем мета-информацию
            rating = self._extract_rating(card)
            price = self._extract_price(card)
            category = self._extract_category(card)
            
            if title:
                return {
                    'title': title,
                    'description': description,
                    'image_url': image_url,
                    'rating': rating,
                    'price': price,
                    'category': category,
                    'source': 'card'
                }
        except Exception as e:
            print(f"Ошибка при извлечении из карточки: {e}")
        
        return None
    
    def _extract_place_from_heading(self, heading) -> Optional[Dict]:
        """Извлекает информацию о месте из заголовка"""
        try:
            title = heading.get_text(strip=True)
            
            # Ищем следующий элемент с описанием
            next_elem = heading.find_next_sibling()
            description = ""
            if next_elem and next_elem.name == 'p':
                description = next_elem.get_text(strip=True)
            
            # Ищем изображение рядом
            img_elem = heading.find_next('img')
            image_url = img_elem.get('src', '') if img_elem else ""
            
            if title:
                return {
                    'title': title,
                    'description': description,
                    'image_url': image_url,
                    'rating': None,
                    'price': None,
                    'category': None,
                    'source': 'heading'
                }
        except Exception as e:
            print(f"Ошибка при извлечении из заголовка: {e}")
        
        return None
    
    def _extract_place_from_list_item(self, item) -> Optional[Dict]:
        """Извлекает информацию о месте из элемента списка"""
        try:
            text = item.get_text(strip=True)
            
            # Ищем ссылку
            link = item.find('a')
            if link:
                title = link.get_text(strip=True)
            else:
                title = text
            
            # Ищем изображение
            img_elem = item.find('img')
            image_url = img_elem.get('src', '') if img_elem else ""
            
            if title:
                return {
                    'title': title,
                    'description': text,
                    'image_url': image_url,
                    'rating': None,
                    'price': None,
                    'category': None,
                    'source': 'list_item'
                }
        except Exception as e:
            print(f"Ошибка при извлечении из списка: {e}")
        
        return None
    
    def _extract_place_from_paragraph(self, p) -> Optional[Dict]:
        """Извлекает информацию о месте из параграфа"""
        try:
            text = p.get_text(strip=True)
            
            # Ищем название места (обычно в начале параграфа)
            lines = text.split('.')
            if lines:
                title = lines[0].strip()
                description = '. '.join(lines[1:]).strip() if len(lines) > 1 else ""
                
                if title:
                    return {
                        'title': title,
                        'description': description,
                        'image_url': "",
                        'rating': None,
                        'price': None,
                        'category': None,
                        'source': 'paragraph'
                    }
        except Exception as e:
            print(f"Ошибка при извлечении из параграфа: {e}")
        
        return None
    
    def _extract_place_from_link(self, link) -> Optional[Dict]:
        """Извлекает информацию о месте из ссылки"""
        try:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if title and self._is_place_name(title):
                return {
                    'title': title,
                    'description': f"Ссылка: {href}",
                    'image_url': "",
                    'rating': None,
                    'price': None,
                    'category': None,
                    'source': 'link'
                }
        except Exception as e:
            print(f"Ошибка при извлечении из ссылки: {e}")
        
        return None
    
    def _is_place_heading(self, text: str) -> bool:
        """Проверяет, является ли заголовок названием места"""
        place_indicators = [
            'restaurant', 'cafe', 'bar', 'pub', 'club', 'spa', 'hotel', 'museum',
            'gallery', 'park', 'market', 'shop', 'store', 'mall', 'cinema', 'theater',
            'restaurant', 'café', 'bistro', 'diner', 'eatery', 'grill', 'steakhouse'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in place_indicators)
    
    def _contains_place_name(self, text: str) -> bool:
        """Проверяет, содержит ли текст название места"""
        # Простая эвристика: текст содержит заглавные буквы и достаточно длинный
        return len(text) > 10 and any(c.isupper() for c in text)
    
    def _is_place_link(self, text: str, href: str) -> bool:
        """Проверяет, является ли ссылка на место"""
        if not text or len(text) < 3:
            return False
        
        # Проверяем, что текст не похож на служебную ссылку
        service_words = ['home', 'about', 'contact', 'privacy', 'terms', 'login', 'signup']
        if text.lower() in service_words:
            return False
        
        return True
    
    def _is_place_name(self, text: str) -> bool:
        """Проверяет, является ли текст названием места"""
        if not text or len(text) < 3:
            return False
        
        # Проверяем на служебные слова
        service_words = ['home', 'about', 'contact', 'privacy', 'terms', 'login', 'signup', 'menu']
        if text.lower() in service_words:
            return False
        
        return True
    
    def _extract_rating(self, element) -> Optional[float]:
        """Извлекает рейтинг из элемента"""
        try:
            # Ищем по классу rating
            rating_elem = element.find(class_=re.compile(r'rating|score|stars'))
            if rating_elem:
                text = rating_elem.get_text(strip=True)
                # Ищем число
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    return float(match.group(1))
            
            # Ищем по тексту
            text = element.get_text()
            match = re.search(r'(\d+\.?\d*)\s*stars?', text, re.IGNORECASE)
            if match:
                return float(match.group(1))
                
        except Exception:
            pass
        
        return None
    
    def _extract_price(self, element) -> Optional[str]:
        """Извлекает цену из элемента"""
        try:
            # Ищем по классу price
            price_elem = element.find(class_=re.compile(r'price|cost'))
            if price_elem:
                return price_elem.get_text(strip=True)
            
            # Ищем по тексту
            text = element.get_text()
            match = re.search(r'(\$+|\€+|\£+)', text)
            if match:
                return match.group(1)
                
        except Exception:
            pass
        
        return None
    
    def _extract_category(self, element) -> Optional[str]:
        """Извлекает категорию из элемента"""
        try:
            # Ищем по классу category
            cat_elem = element.find(class_=re.compile(r'category|type|genre'))
            if cat_elem:
                return cat_elem.get_text(strip=True)
            
            # Ищем по тексту
            text = element.get_text()
            categories = ['restaurant', 'cafe', 'bar', 'spa', 'hotel', 'museum', 'gallery']
            for cat in categories:
                if cat in text.lower():
                    return cat.title()
                
        except Exception:
            pass
        
        return None
    
    def save_to_json(self, places: List[Dict], filename: str):
        """Сохраняет места в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(places, f, ensure_ascii=False, indent=2)
            print(f"💾 Сохранено в {filename}")
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")

def main():
    parser = UniversalPlaceParser()
    
    # URL для тестирования
    test_url = "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025"
    
    print("🚀 Универсальный парсер мест")
    print("=" * 50)
    
    # Парсим статью
    places = parser.parse_article(test_url, limit=10)
    
    if places:
        print(f"\n📋 Найдено мест: {len(places)}")
        print("-" * 50)
        
        for i, place in enumerate(places, 1):
            print(f"{i}. {place['title']}")
            if place['description']:
                print(f"   Описание: {place['description'][:100]}...")
            if place['image_url']:
                print(f"   Изображение: {place['image_url']}")
            if place['rating']:
                print(f"   Рейтинг: {place['rating']}")
            if place['price']:
                print(f"   Цена: {place['price']}")
            if place['category']:
                print(f"   Категория: {place['category']}")
            print(f"   Источник: {place['source']}")
            print()
        
        # Сохраняем в JSON
        parser.save_to_json(places, 'parsed_places.json')
        
    else:
        print("\n❌ Места не найдены")

if __name__ == "__main__":
    main()
