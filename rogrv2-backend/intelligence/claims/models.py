from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class ClaimTier(str, Enum):
    primary = "primary"
    secondary = "secondary"
    tertiary = "tertiary"

class ExtractedClaim(BaseModel):
    id: str = Field(default_factory=lambda: "c_" + "".join(__import__("secrets").choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(8)))
    text: str
    tier: ClaimTier
    priority: int = 0
    entities: Optional[List[str]] = None
    scope: Optional[Dict] = None