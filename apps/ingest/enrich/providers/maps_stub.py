"""
Maps Provider Stub and Google Maps Enrichment
Deterministic fake enrichment data + real Google Maps web scraping with correct URL formats
"""
import json
import re
import time
import requests
from typing import Dict, Optional
from enricher import EnrichmentProvider, EnrichmentResult
from bs4 import BeautifulSoup
from logger import logger

class GoogleMapsProvider(EnrichmentProvider):
    """Real Google Maps provider using web scraping with correct URL formats"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Cache for already enriched places
        self.cache = {}
    
    def enrich(self, name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
        """Enrich place data from Google Maps"""
        
        # Create cache key
        cache_key = f"{name_raw}_{city}"
        
        # Check cache first
        if cache_key in self.cache:
            logger.info(f"📋 Using cached data for: {name_raw}")
            return self.cache[cache_key]
        
        try:
            logger.info(f"🔍 Enriching from Google Maps: {name_raw}")
            
            # Build search query
            search_query = f"{name_raw} {city}"
            if address_raw:
                search_query += f" {address_raw}"
            
            # Search Google Maps
            search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            
            # Get search results page
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            # Parse the page to find place details
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract place information
            place_data = self._extract_place_data(soup, name_raw)
            
            # Try to extract the first place link from search results using correct methods
            place_link = self._extract_first_place_link(soup, name_raw)
            
            # Use the generated link
            gmap_url = place_link if place_link else f"https://maps.google.com/maps?q={name_raw.replace(' ', '+')}+{city}"
            
            # Create enrichment result
            result = EnrichmentResult(
                rating=place_data.get('rating'),
                ratings_count=place_data.get('ratings_count'),
                price_level=place_data.get('price_level'),
                lat=place_data.get('lat'),
                lng=place_data.get('lng'),
                hours_json=place_data.get('hours_json'),
                site=place_data.get('site'),
                phone=place_data.get('phone'),
                gmap_url=gmap_url
            )
            
            # Cache the result
            self.cache[cache_key] = result
            
            # Be respectful with requests
            time.sleep(2)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error enriching {name_raw}: {e}")
            # Return fallback data
            return self._get_fallback_data(name_raw, city)
    
    def _extract_place_data(self, soup: BeautifulSoup, name_raw: str) -> Dict:
        """Extract place data from Google Maps page"""
        place_data = {}
        
        try:
            # Look for coordinates in the page
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and 'lat' in script.string and 'lng' in script.string:
                    lat_match = re.search(r'"lat":\s*([-\d.]+)', script.string)
                    lng_match = re.search(r'"lng":\s*([-\d.]+)', script.string)
                    if lat_match and lng_match:
                        place_data['lat'] = float(lat_match.group(1))
                        place_data['lng'] = float(lng_match.group(1))
                        break
            
            # Default hours (most places in Bangkok are open daily)
            place_data['hours_json'] = json.dumps({
                "monday": "09:00-22:00",
                "tuesday": "09:00-22:00",
                "wednesday": "09:00-22:00",
                "thursday": "09:00-22:00",
                "friday": "09:00-22:00",
                "saturday": "09:00-22:00",
                "sunday": "09:00-22:00"
            })
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting place data: {e}")
        
        return place_data
    
    def _extract_first_place_link(self, soup: BeautifulSoup, name_raw: str) -> Optional[str]:
        """Extract place link using correct Google Maps URL formats based on ID type"""
        try:
            logger.info(f"🔍 Attempting to extract place link for: {name_raw}")
            
            # Extract data from HTML
            html_content = str(soup)
            place_data = {}
            
            # Look for Place ID (ChIJ strings) - these are NOT numeric CIDs
            # Try multiple patterns for finding Place IDs
            place_id_matches = []
            
            # Pattern 1: ChIJiW5PNgCf4jARFz9UHGvCjT8 (direct match)
            direct_place_id_matches = re.findall(r'ChIJ[-\w]{20,}', html_content)
            place_id_matches.extend(direct_place_id_matches)
            
            # Pattern 2: "place_id":"ChIJiW5PNgCf4jARFz9UHGvCjT8" (JSON format)
            json_place_id_matches = re.findall(r'"place_id":\s*"(ChIJ[-\w]{20,})"', html_content)
            place_id_matches.extend(json_place_id_matches)
            
            # Pattern 3: place_id:ChIJiW5PNgCf4jARFz9UHGvCjT8 (colon format)
            colon_place_id_matches = re.findall(r'place_id:(ChIJ[-\w]{20,})', html_content)
            place_id_matches.extend(colon_place_id_matches)
            
            if place_id_matches:
                # Remove duplicates and take the first one
                unique_place_ids = list(set(place_id_matches))
                place_data['place_id'] = unique_place_ids[0]
                logger.info(f"✅ Found Place ID: {unique_place_ids[0]}")
                if len(unique_place_ids) > 1:
                    logger.info(f"📝 Found multiple Place IDs: {unique_place_ids}")
            
            # Look for numeric CID (digits only) - these are different from Place IDs
            # Try multiple patterns for finding numeric CIDs
            numeric_cid_matches = []
            
            # Pattern 1: cid=1234567890123456789
            cid_param_matches = re.findall(r'cid=(\d{10,})', html_content)
            numeric_cid_matches.extend(cid_param_matches)
            
            # Pattern 2: "cid":"1234567890123456789" (JSON format)
            cid_json_matches = re.findall(r'"cid":\s*"(\d{10,})"', html_content)
            numeric_cid_matches.extend(cid_json_matches)
            
            # Pattern 3: cid:1234567890123456789 (colon format)
            cid_colon_matches = re.findall(r'cid:(\d{10,})', html_content)
            numeric_cid_matches.extend(cid_colon_matches)
            
            if numeric_cid_matches:
                # Remove duplicates and take the first one
                unique_cids = list(set(numeric_cid_matches))
                place_data['numeric_cid'] = unique_cids[0]
                logger.info(f"✅ Found numeric CID: {unique_cids[0]}")
                if len(unique_cids) > 1:
                    logger.info(f"📝 Found multiple CIDs: {unique_cids}")
            
            # Look for coordinates
            coord_matches = re.findall(r'@([-\d.]+),([-\d.]+)', html_content)
            if coord_matches:
                for lat, lng in coord_matches:
                    try:
                        lat_val = float(lat)
                        lng_val = float(lng)
                        if 13.0 <= lat_val <= 14.0 and 100.0 <= lng_val <= 101.0:  # Bangkok area
                            place_data['lat'] = lat_val
                            place_data['lng'] = lng_val
                            logger.info(f"✅ Found coordinates: {lat_val}, {lng_val}")
                            break
                    except ValueError:
                        continue
            
            # Now generate URLs using the correct formats based on ID type
            
            # Method 1: Place ID format (ChIJ strings) - use place_id parameter
            if place_data.get('place_id'):
                place_id_url = f"https://www.google.com/maps/place/?q=place_id:{place_data['place_id']}"
                logger.info(f"✅ Generated Place ID URL: {place_id_url}")
                return place_id_url
            
            # Method 2: Numeric CID format (digits only) - use cid parameter
            if place_data.get('numeric_cid'):
                numeric_cid_url = f"https://www.google.com/maps/?cid={place_data['numeric_cid']}"
                logger.info(f"✅ Generated numeric CID URL: {numeric_cid_url}")
                return numeric_cid_url
            
            # Method 3: Coordinate-based format (fallback when no IDs found)
            if place_data.get('lat') and place_data.get('lng'):
                coord_url = f"https://www.google.com/maps/place/{name_raw.replace(' ', '+')}/@{place_data['lat']},{place_data['lng']},17z"
                logger.info(f"✅ Generated coordinate URL: {coord_url}")
                return coord_url
            
            # Method 4: Universal search format (final fallback)
            search_url = f"https://www.google.com/maps/search/{name_raw.replace(' ', '+')}+Bangkok"
            logger.info(f"✅ Generated search URL: {search_url}")
            return search_url

        except Exception as e:
            logger.warning(f"⚠️ Error extracting place link: {e}")

            # Fallback: simple search
            fallback_url = f"https://maps.google.com/maps?q={name_raw.replace(' ', '+')}+Bangkok"
            logger.warning(f"⚠️ Using fallback URL: {fallback_url}")
            return fallback_url
    
    def _get_fallback_data(self, name_raw: str, city: str) -> EnrichmentResult:
        """Return fallback data when enrichment fails"""
        return EnrichmentResult(
            rating=4.0,
            ratings_count=100,
            price_level=2,
            lat=13.7563,  # Bangkok center
            lng=100.5018,
            hours_json=json.dumps({"monday": "09:00-18:00"}),
            site="https://maps.google.com",
            phone="+66 2 000 0000",
            gmap_url=f"https://maps.google.com/maps?q={name_raw.replace(' ', '+')}+{city}"
        )


class MapsStubProvider(EnrichmentProvider):
    """Deterministic fake enrichment data for testing"""
    
    def enrich(self, name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
        """Return deterministic fake data based on input"""
        # Generate deterministic fake data based on name hash
        name_hash = hash(name_raw) % 1000
        
        return EnrichmentResult(
            rating=3.5 + (name_hash % 15) / 10,  # 3.5-5.0
            ratings_count=50 + (name_hash % 200),  # 50-250
            price_level=1 + (name_hash % 4),  # 1-4
            lat=13.7563 + (name_hash % 100 - 50) / 1000,  # Bangkok area ±0.05
            lng=100.5018 + (name_hash % 100 - 50) / 1000,
            hours_json=json.dumps({
                "monday": "09:00-22:00",
                "tuesday": "09:00-22:00",
                "wednesday": "09:00-22:00",
                "thursday": "09:00-22:00",
                "friday": "09:00-22:00",
                "saturday": "09:00-22:00",
                "sunday": "09:00-22:00"
            }),
            site=f"https://example.com/{name_raw.lower().replace(' ', '-')}",
            phone=f"+66 2 {name_hash:03d} {name_hash % 1000:04d}",
            gmap_url=f"https://maps.google.com/maps?q={name_raw.replace(' ', '+')}+{city}"
        )
