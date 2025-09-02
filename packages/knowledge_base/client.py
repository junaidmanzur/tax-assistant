"""Qdrant client wrapper for knowledge base operations."""
import os
import uuid
from typing import List, Optional
from dotenv import load_dotenv, find_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
from openai import OpenAI

from knowledge_base.schemas import KnowledgeEntry, KnowledgeSearchResult, KnowledgeSearchRequest

# Load .env file from project root
load_dotenv(find_dotenv())


class KnowledgeBaseClient:
    """Client for interacting with the knowledge base stored in Qdrant."""
    
    def __init__(self, 
                 qdrant_url: str = "http://localhost:6333",
                 collection_name: str = "tax_knowledge",
                 openai_api_key: Optional[str] = None):
        """Initialize the knowledge base client.
        
        Args:
            qdrant_url: URL of the Qdrant instance
            collection_name: Name of the collection to store knowledge entries
            openai_api_key: OpenAI API key for embeddings
        """
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.openai_client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        try:
            self.qdrant_client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimension
                    distance=Distance.COSINE
                )
            )
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Add a knowledge entry to the vector database."""
        # Create embedding from title + content + keywords for better search
        search_text = f"{entry.title}. {entry.content}. Keywords: {', '.join(entry.keywords)}"
        embedding = self._get_embedding(search_text)
        
        # Generate UUID for Qdrant point ID, but store original ID in payload
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry.id))
        
        # Create point for Qdrant
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "id": entry.id,  # Store original string ID in payload
                "title": entry.title,
                "content": entry.content,
                "category": entry.category,
                "ato_url": entry.ato_url,
                "keywords": entry.keywords,
                "tax_year": entry.tax_year
            }
        )
        
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    def add_entries_batch(self, entries: List[KnowledgeEntry]) -> None:
        """Add multiple knowledge entries in batch."""
        points = []
        for entry in entries:
            search_text = f"{entry.title}. {entry.content}. Keywords: {', '.join(entry.keywords)}"
            embedding = self._get_embedding(search_text)
            
            # Generate UUID for Qdrant point ID, but store original ID in payload
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry.id))
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "id": entry.id,  # Store original string ID in payload
                    "title": entry.title,
                    "content": entry.content,
                    "category": entry.category,
                    "ato_url": entry.ato_url,
                    "keywords": entry.keywords,
                    "tax_year": entry.tax_year
                }
            )
            points.append(point)
        
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search(self, request: KnowledgeSearchRequest) -> List[KnowledgeSearchResult]:
        """Search for knowledge entries."""
        query_embedding = self._get_embedding(request.query)
        
        # Build filter if category is specified
        query_filter = None
        if request.category:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=request.category)
                    )
                ]
            )
        
        # Search in Qdrant
        search_results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=request.limit,
            score_threshold=request.min_score
        )
        
        # Convert to KnowledgeSearchResult objects
        results = []
        for hit in search_results.points:
            entry = KnowledgeEntry(
                id=hit.payload["id"],  # Use original ID from payload
                title=hit.payload["title"],
                content=hit.payload["content"],
                category=hit.payload["category"],
                ato_url=hit.payload["ato_url"],
                keywords=hit.payload["keywords"],
                tax_year=hit.payload["tax_year"]
            )
            results.append(KnowledgeSearchResult(entry=entry, score=hit.score))
        
        return results
    
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific entry by ID."""
        try:
            # Convert string ID to UUID for lookup
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry_id))
            result = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            if result:
                hit = result[0]
                return KnowledgeEntry(
                    id=hit.payload["id"],  # Use original ID from payload
                    title=hit.payload["title"],
                    content=hit.payload["content"],
                    category=hit.payload["category"],
                    ato_url=hit.payload["ato_url"],
                    keywords=hit.payload["keywords"],
                    tax_year=hit.payload["tax_year"]
                )
        except Exception:
            pass
        return None
    
    def delete_entry(self, entry_id: str) -> None:
        """Delete an entry by ID."""
        # Convert string ID to UUID for deletion
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry_id))
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[point_id])
        )
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        return self.qdrant_client.get_collection(self.collection_name).__dict__