"""
Maps Provider Stub
Deterministic fake enrichment data for known mock names
"""
import json
from typing import Dict, Optional
from enricher import EnrichmentProvider, EnrichmentResult

class MapsStubProvider(EnrichmentProvider):
    """Stub provider that returns deterministic fake data"""
    
    def __init__(self):
        # Mock data for known places
        self.mock_data = {
            "Bangkok's Best Rooftop Bars": {
                "rating": 4.8,
                "ratings_count": 1247,
                "price_level": 4,
                "lat": 13.7563,
                "lng": 100.5018,
                "hours_json": json.dumps({
                    "monday": "18:00-02:00",
                    "tuesday": "18:00-02:00",
                    "wednesday": "18:00-02:00",
                    "thursday": "18:00-02:00",
                    "friday": "18:00-02:00",
                    "saturday": "18:00-02:00",
                    "sunday": "18:00-02:00"
                }),
                "site": "https://www.timeout.com/bangkok/bars-and-pubs/best-rooftop-bars",
                "phone": "+66 2 123 4567",
                "gmap_url": "https://maps.google.com/?q=Bangkok+Rooftop+Bars"
            },
            "Traditional Thai Massage Spas": {
                "rating": 4.6,
                "ratings_count": 892,
                "price_level": 2,
                "lat": 13.7325,
                "lng": 100.5444,
                "hours_json": json.dumps({
                    "monday": "09:00-21:00",
                    "tuesday": "09:00-21:00",
                    "wednesday": "09:00-21:00",
                    "thursday": "09:00-21:00",
                    "friday": "09:00-21:00",
                    "saturday": "09:00-21:00",
                    "sunday": "09:00-21:00"
                }),
                "site": "https://www.timeout.com/bangkok/health-and-beauty/best-thai-massage",
                "phone": "+66 2 234 5678",
                "gmap_url": "https://maps.google.com/?q=Thai+Massage+Bangkok"
            },
            "Street Food Markets Tour": {
                "rating": 4.9,
                "ratings_count": 2156,
                "price_level": 1,
                "lat": 13.7246,
                "lng": 100.4930,
                "hours_json": json.dumps({
                    "monday": "06:00-22:00",
                    "tuesday": "06:00-22:00",
                    "wednesday": "06:00-22:00",
                    "thursday": "06:00-22:00",
                    "friday": "06:00-22:00",
                    "saturday": "06:00-22:00",
                    "sunday": "06:00-22:00"
                }),
                "site": "https://www.timeout.com/bangkok/food-and-drink/street-food-markets",
                "phone": "+66 2 345 6789",
                "gmap_url": "https://maps.google.com/?q=Bangkok+Street+Food"
            },
            "Lumpini Park Morning Activities": {
                "rating": 4.4,
                "ratings_count": 8923,
                "price_level": 0,
                "lat": 13.7325,
                "lng": 100.5444,
                "hours_json": json.dumps({
                    "monday": "04:30-22:00",
                    "tuesday": "04:30-22:00",
                    "wednesday": "04:30-22:00",
                    "thursday": "04:30-22:00",
                    "friday": "04:30-22:00",
                    "saturday": "04:30-22:00",
                    "sunday": "04:30-22:00"
                }),
                "site": "https://www.timeout.com/bangkok/things-to-do/lumpini-park-activities",
                "phone": "+66 2 252 7006",
                "gmap_url": "https://maps.google.com/?q=Lumpini+Park"
            },
            "Silom Nightlife District": {
                "rating": 4.3,
                "ratings_count": 1567,
                "price_level": 3,
                "lat": 13.7246,
                "lng": 100.4930,
                "hours_json": json.dumps({
                    "monday": "19:00-03:00",
                    "tuesday": "19:00-03:00",
                    "wednesday": "19:00-03:00",
                    "thursday": "19:00-03:00",
                    "friday": "19:00-03:00",
                    "saturday": "19:00-03:00",
                    "sunday": "19:00-03:00"
                }),
                "site": "https://www.timeout.com/bangkok/nightlife/silom-district",
                "phone": "+66 2 456 7890",
                "gmap_url": "https://maps.google.com/?q=Silom+Nightlife"
            }
        }
    
    def enrich(self, name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
        """Return deterministic fake data for known places"""
        
        # Try to find exact match first
        if name_raw in self.mock_data:
            data = self.mock_data[name_raw]
            return EnrichmentResult(
                rating=data["rating"],
                ratings_count=data["ratings_count"],
                price_level=data["price_level"],
                lat=data["lat"],
                lng=data["lng"],
                hours_json=data["hours_json"],
                site=data["site"],
                phone=data["phone"],
                gmap_url=data["gmap_url"]
            )
        
        # Fallback for unknown places
        return EnrichmentResult(
            rating=4.0,
            ratings_count=100,
            price_level=2,
            lat=13.7563,
            lng=100.5018,
            hours_json=json.dumps({"monday": "09:00-18:00"}),
            site="https://example.com",
            phone="+66 2 000 0000",
            gmap_url="https://maps.google.com/?q=Bangkok"
        )
