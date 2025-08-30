#!/usr/bin/env python3
"""
Simple test script to debug extraction logic
"""

import requests
from bs4 import BeautifulSoup
import re

def test_extraction():
    url = "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("🔍 ТЕСТИРОВАНИЕ ЛОГИКИ ИЗВЛЕЧЕНИЯ")
        print("=" * 60)
        
        # Find first numbered heading
        headings = soup.find_all(['h2', 'h3'])
        numbered_headings = []
        
        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if re.match(r'^\d+\.', heading_text):
                numbered_headings.append(heading)
        
        if numbered_headings:
            heading = numbered_headings[0]
            heading_text = heading.get_text(strip=True)
            
            print(f"📋 Первый заголовок: '{heading_text}'")
            print(f"   HTML: {heading}")
            
            # Test name extraction
            name_raw = re.sub(r'^\d+\.', '', heading_text).strip()
            print(f"📝 Извлеченное название: '{name_raw}'")
            
            # Test place URL extraction
            link = heading.find('a')
            if link:
                href = link.get('href')
                print(f"🔗 Ссылка: {href}")
            else:
                print("🔗 Ссылка не найдена")
            
            # Test tile container
            tile_container = heading.parent.parent
            print(f"🏗️ Контейнер заголовка: <{tile_container.name}> class='{tile_container.get('class', [])}'")
            
            # Find the actual tile container (parent of the title container)
            actual_tile_container = tile_container.parent
            print(f"🏗️ Реальный контейнер плитки: <{actual_tile_container.name}> class='{actual_tile_container.get('class', [])}'")
            
            # Look for content in the actual tile container
            print(f"\n📄 ПОИСК КОНТЕНТА В РЕАЛЬНОМ КОНТЕЙНЕРЕ:")
            content_elements = actual_tile_container.find_all(['p', 'div', 'img', 'a'])
            print(f"   Найдено элементов: {len(content_elements)}")
            
            for i, elem in enumerate(content_elements[:15], 1):
                elem_type = elem.name
                elem_text = elem.get_text(strip=True)[:80] if elem.get_text(strip=True) else 'пусто'
                elem_class = elem.get('class', [])
                
                print(f"   {i}. <{elem_type}> class='{elem_class}': '{elem_text}...'")
                
                # Look for specific patterns
                if elem.name == 'p':
                    if 'address' in elem_text.lower():
                        print(f"      🏠 ПОТЕНЦИАЛЬНЫЙ АДРЕС!")
                    elif len(elem_text) > 50:
                        print(f"      📝 ПОТЕНЦИАЛЬНОЕ ОПИСАНИЕ!")
                
                if elem.name == 'img':
                    src = elem.get('src', '')
                    alt = elem.get('alt', '')
                    print(f"      🖼️ ИЗОБРАЖЕНИЕ: src='{src}', alt='{alt}'")
            
            # Test description extraction
            summary_container = actual_tile_container.find('div', class_='_summaryContainer_osmln_364')
            if summary_container:
                print(f"\n📄 Найден контейнер описания: {summary_container}")
                
                paragraphs = summary_container.find_all('p')
                print(f"   Параграфов: {len(paragraphs)}")
                
                for i, p in enumerate(paragraphs, 1):
                    text = p.get_text(strip=True)
                    print(f"   {i}. '{text[:100]}...'")
                    
                    if text.lower().startswith('address'):
                        print(f"      🏠 ЭТО АДРЕС!")
                    elif len(text) > 30:
                        print(f"      📝 ЭТО ОПИСАНИЕ!")
            else:
                print("\n❌ Контейнер описания не найден")
            
            # Test categories extraction
            tags_container = actual_tile_container.find('div', class_='_tileTags_osmln_50')
            if tags_container:
                print(f"\n🏷️ Найден контейнер тегов: {tags_container}")
                tags_text = tags_container.get_text(strip=True)
                print(f"   Текст тегов: '{tags_text}'")
            else:
                print("\n❌ Контейнер тегов не найден")
            
            # Test image extraction
            image_container = actual_tile_container.find('div', class_='_imageContainer_osmln_46')
            if image_container:
                print(f"\n🖼️ Найден контейнер изображений: {image_container}")
                
                images = image_container.find_all('img')
                print(f"   Изображений: {len(images)}")
                
                for i, img in enumerate(images, 1):
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    print(f"   {i}. src: {src}")
                    print(f"      alt: {alt}")
            else:
                print("\n❌ Контейнер изображений не найден")
                
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_extraction()
