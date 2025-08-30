from dataclasses import dataclass
from typing import Optional

@dataclass
class EntertainmentItem:
    """Placeholder for entertainment item model"""
    id: str
    title: str
    description: Optional[str] = None
