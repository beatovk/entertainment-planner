"""
Place Enricher Interface
Enriches raw place data with additional information from external providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class EnrichmentResult:
    """Result of place enrichment"""
    rating: Optional[float] = None
    ratings_count: Optional[int] = None
    price_level: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    hours_json: Optional[str] = None
    site: Optional[str] = None
    phone: Optional[str] = None
    gmap_url: Optional[str] = None

class EnrichmentProvider(ABC):
    """Abstract interface for enrichment providers"""
    
    @abstractmethod
    def enrich(self, name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
        """Enrich place data with external information"""
        pass

class PlaceEnricher:
    """Main enricher that uses provider implementations"""
    
    def __init__(self, provider: EnrichmentProvider):
        self.provider = provider
    
    def enrich(self, name_raw: str, address_raw: str, city: str) -> EnrichmentResult:
        """Enrich place data using the configured provider"""
        return self.provider.enrich(name_raw, address_raw, city)
