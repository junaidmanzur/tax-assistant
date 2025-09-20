"""Pydantic schemas for knowledge base entries."""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib


class KnowledgeEntry(BaseModel):
    """Schema for a single knowledge base entry with enhanced RAG-friendly structure."""
    id: str                          # Unique identifier
    url: str                         # Source URL
    title: str                       # Human-readable title
    section: Optional[str] = None    # H2/H3 heading context
    anchor: Optional[str] = None     # kebab-case-anchor for citation links
    content: str                     # Main content chunk (300-800 tokens optimal)
    jurisdiction: str = "AU"         # Jurisdiction code
    domain: str                      # Source domain (e.g., "ato.gov.au")
    source_type: str = "web"         # Source type
    last_updated_claimed: Optional[str] = None    # YYYY-MM-DD from page content
    last_modified_header: Optional[str] = None    # YYYY-MM-DDTHH:MM:SSZ from HTTP header
    retrieved_at: str                # YYYY-MM-DD when scraped
    effective_years: List[str] = []  # e.g., ["2025-26"]
    tags: List[str] = []             # e.g., ["individual-tax", "resident-rates"]
    hash: Optional[str] = None       # sha256 hash of clean content
    
    def __init__(self, **data):
        # Auto-generate hash if not provided
        if 'hash' not in data or data['hash'] is None:
            content = data.get('content', '')
            data['hash'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Auto-generate retrieved_at if not provided
        if 'retrieved_at' not in data:
            data['retrieved_at'] = datetime.now().strftime('%Y-%m-%d')
            
        super().__init__(**data)
    
    @validator('content')
    def validate_content_length(cls, v):
        """Ensure content is optimal length for RAG retrieval (300-800 tokens)."""
        if len(v) > 3200:  # ~800 tokens at 4 chars per token
            raise ValueError('Content should be under 3200 characters for optimal RAG performance (800 tokens)')
        if len(v) < 50:  # Minimum viable content
            raise ValueError('Content should be at least 50 characters')
        return v
    
    @validator('jurisdiction')
    def validate_jurisdiction(cls, v):
        """Ensure jurisdiction is valid."""
        allowed_jurisdictions = {"AU", "US", "UK", "CA", "NZ"}
        if v not in allowed_jurisdictions:
            raise ValueError(f'Jurisdiction must be one of: {allowed_jurisdictions}')
        return v
    
    @validator('source_type')
    def validate_source_type(cls, v):
        """Ensure source_type is valid."""
        allowed_types = {"web", "pdf", "document", "api", "manual"}
        if v not in allowed_types:
            raise ValueError(f'Source type must be one of: {allowed_types}')
        return v


class KnowledgeSearchResult(BaseModel):
    """Schema for search results with relevance score."""
    entry: KnowledgeEntry
    score: float                     # Similarity score from vector search
    
    
class KnowledgeSearchRequest(BaseModel):
    """Schema for knowledge search requests."""
    query: str
    category: Optional[str] = None   # Filter by category
    limit: int = 3                   # Number of results to return
    min_score: float = 0.5          # Minimum similarity threshold