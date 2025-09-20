from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.connection import execute_query, execute_insert, execute_update, json_to_str, str_to_json

@dataclass
class TrustfeedEntry:
    """Model for trustfeed entries."""
    claim_summary: str
    trust_score: Optional[float] = None
    grade: Optional[str] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    claims_analyzed: int = 0
    scan_mode: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    full_capsule_data: Optional[Dict[str, Any]] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustfeedEntry':
        """Create TrustfeedEntry from dictionary."""
        # Convert JSON strings back to Python objects
        if 'tags' in data and isinstance(data['tags'], str):
            data['tags'] = str_to_json(data['tags'])
        if 'categories' in data and isinstance(data['categories'], str):
            data['categories'] = str_to_json(data['categories'])
        if 'full_capsule_data' in data and isinstance(data['full_capsule_data'], str):
            data['full_capsule_data'] = str_to_json(data['full_capsule_data'])

        # Convert created_at string to datetime if present
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert TrustfeedEntry to dictionary."""
        data = asdict(self)
        # Convert datetime to string for JSON serialization
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        return data

    def save(self) -> int:
        """Save the entry to the database and return the ID."""
        if self.id is None:
            # Insert new entry
            query = """
                INSERT INTO trustfeed_entries (
                    claim_summary, trust_score, grade, source_url, source_domain,
                    claims_analyzed, scan_mode, tags, categories, full_capsule_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.claim_summary,
                self.trust_score,
                self.grade,
                self.source_url,
                self.source_domain,
                self.claims_analyzed,
                self.scan_mode,
                json_to_str(self.tags),
                json_to_str(self.categories),
                json_to_str(self.full_capsule_data)
            )
            self.id = execute_insert(query, params)
            return self.id
        else:
            # Update existing entry
            query = """
                UPDATE trustfeed_entries SET
                    claim_summary = ?, trust_score = ?, grade = ?, source_url = ?,
                    source_domain = ?, claims_analyzed = ?, scan_mode = ?,
                    tags = ?, categories = ?, full_capsule_data = ?
                WHERE id = ?
            """
            params = (
                self.claim_summary,
                self.trust_score,
                self.grade,
                self.source_url,
                self.source_domain,
                self.claims_analyzed,
                self.scan_mode,
                json_to_str(self.tags),
                json_to_str(self.categories),
                json_to_str(self.full_capsule_data),
                self.id
            )
            execute_update(query, params)
            return self.id

    @classmethod
    def get_by_id(cls, entry_id: int) -> Optional['TrustfeedEntry']:
        """Get a trustfeed entry by ID."""
        query = "SELECT * FROM trustfeed_entries WHERE id = ?"
        results = execute_query(query, (entry_id,))
        if results:
            return cls.from_dict(results[0])
        return None

    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List['TrustfeedEntry']:
        """Get all trustfeed entries with pagination."""
        query = """
            SELECT * FROM trustfeed_entries
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        results = execute_query(query, (limit, offset))
        return [cls.from_dict(row) for row in results]

    @classmethod
    def get_by_source_domain(cls, domain: str, limit: int = 50) -> List['TrustfeedEntry']:
        """Get entries by source domain."""
        query = """
            SELECT * FROM trustfeed_entries
            WHERE source_domain = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = execute_query(query, (domain, limit))
        return [cls.from_dict(row) for row in results]

    @classmethod
    def get_by_trust_score_range(cls, min_score: float, max_score: float, limit: int = 50) -> List['TrustfeedEntry']:
        """Get entries within a trust score range."""
        query = """
            SELECT * FROM trustfeed_entries
            WHERE trust_score BETWEEN ? AND ?
            ORDER BY trust_score DESC, created_at DESC
            LIMIT ?
        """
        results = execute_query(query, (min_score, max_score, limit))
        return [cls.from_dict(row) for row in results]

    @classmethod
    def search_by_claim(cls, search_term: str, limit: int = 50) -> List['TrustfeedEntry']:
        """Search entries by claim summary."""
        query = """
            SELECT * FROM trustfeed_entries
            WHERE claim_summary LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        results = execute_query(query, (f"%{search_term}%", limit))
        return [cls.from_dict(row) for row in results]