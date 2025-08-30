#!/usr/bin/env python3
"""
Debug script to analyze TimeOut Bangkok HTML structure
"""
import requests
from bs4 import BeautifulSoup
import json

def analyze_timeout_structure():
    """Analyze the HTML structure of TimeOut Bangkok page"""
    url = "https://www.timeout.com/bangkok/restaurants/bangkoks-best-new-cafes-of-2025"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        print(f"🌐 Fetching: {url}")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("🔍 Analyzing HTML structure...")
        
        # Look for different types of content containers
        print("\n1️⃣ Looking for numbered list items:")
        numbered_items = soup.find_all(['li', 'div'], string=lambda text: text and re.match(r'^\d+\.', text.strip()))
        print(f"   Found {len(numbered_items)} numbered items")
        
        if numbered_items:
            print("   First few items:")
            for i, item in enumerate(numbered_items[:3]):
                print(f"     {i+1}. {item.get_text(strip=True)[:100]}")
        
        print("\n2️⃣ Looking for headings:")
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        print(f"   Found {len(headings)} headings")
        
        if headings:
            print("   First few headings:")
            for i, heading in enumerate(headings[:5]):
                print(f"     {i+1}. {heading.name}: {heading.get_text(strip=True)[:100]}")
        
        print("\n3️⃣ Looking for article sections:")
        article_sections = soup.find_all(['article', 'section', 'div'], class_=lambda x: x and ('article' in x.lower() or 'content' in x.lower()))
        print(f"   Found {len(article_sections)} potential article sections")
        
        print("\n4️⃣ Looking for place-specific content:")
        # Look for content that might contain place information
        place_containers = soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['place', 'venue', 'cafe', 'restaurant']))
        print(f"   Found {len(place_containers)} potential place containers")
        
        print("\n5️⃣ Analyzing first numbered item structure:")
        if numbered_items:
            first_item = numbered_items[0]
            print(f"   Item tag: {first_item.name}")
            print(f"   Item classes: {first_item.get('class', [])}")
            print(f"   Item text: {first_item.get_text(strip=True)[:200]}")
            
            # Look at siblings and children
            print(f"   Children count: {len(first_item.find_all())}")
            print(f"   Next sibling: {first_item.find_next_sibling().name if first_item.find_next_sibling() else 'None'}")
            
            # Look for paragraphs in the same container
            paragraphs = first_item.find_all('p')
            print(f"   Paragraphs in item: {len(paragraphs)}")
            for i, p in enumerate(paragraphs):
                print(f"     {i+1}. {p.get_text(strip=True)[:100]}")
            
            # Look for paragraphs in parent container
            parent = first_item.parent
            if parent:
                parent_paragraphs = parent.find_all('p')
                print(f"   Paragraphs in parent: {len(parent_paragraphs)}")
                for i, p in enumerate(parent_paragraphs[:3]):
                    print(f"     {i+1}. {p.get_text(strip=True)[:100]}")
        
        print("\n6️⃣ Looking for address patterns:")
        # Search for common address patterns in the text
        full_text = soup.get_text()
        address_patterns = [
            r'Address[:\s]+([^\.]+)',
            r'Located at[:\s]+([^\.]+)',
            r'([^\.]+(?:Road|Street|Soi|Alley)[^\.]*)',
            r'([^\.]+(?:Sukhumvit|Silom|Thonglor|Ekkamai|Sathorn)[^\.]*)'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"   Pattern '{pattern}': {len(matches)} matches")
                for match in matches[:3]:
                    print(f"     - {match.strip()}")
        
        print("\n7️⃣ Looking for image patterns:")
        images = soup.find_all('img')
        print(f"   Found {len(images)} images")
        
        if images:
            print("   First few images:")
            for i, img in enumerate(images[:5]):
                src = img.get('src') or img.get('data-src') or 'No src'
                alt = img.get('alt', 'No alt')[:50]
                print(f"     {i+1}. src: {src[:100]}")
                print(f"        alt: {alt}")
        
        # Save HTML for manual inspection
        with open('timeout_debug.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"\n💾 Saved HTML to timeout_debug.html for manual inspection")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import re
    analyze_timeout_structure()
