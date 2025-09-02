"""Pydantic schemas for knowledge base entries."""
from pydantic import BaseModel, validator
from typing import List, Optional


class KnowledgeEntry(BaseModel):
    """Schema for a single knowledge base entry."""
    id: str                           # Unique identifier: "ded_wfh_2024"
    title: str                        # Human-readable title
    content: str                      # Main explanation text (200-800 chars optimal)
    category: str                     # "deduction" | "calculation" | "concept"
    ato_url: str                     # Primary ATO source URL
    keywords: List[str]              # Search optimization keywords
    tax_year: str = "2024-25"        # Default to current tax year
    
    @validator('content')
    def validate_content_length(cls, v):
        """Ensure content is optimal length for vector search."""
        if len(v) > 2000:
            raise ValueError('Content should be under 2000 characters for optimal search performance')
        if len(v) < 50:
            raise ValueError('Content should be at least 50 characters')
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """Ensure category is one of allowed values."""
        allowed_categories = {"deduction", "calculation", "concept", "faq"}
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {allowed_categories}')
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
    min_score: float = 0.7          # Minimum similarity threshold