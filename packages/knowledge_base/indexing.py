"""Indexing utilities for loading and managing knowledge base entries."""
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv, find_dotenv
from knowledge_base.schemas import KnowledgeEntry
from knowledge_base.client import KnowledgeBaseClient

# Load .env file from project root
load_dotenv(find_dotenv())


class KnowledgeIndexer:
    """Handles loading and indexing knowledge base entries from JSON files."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the indexer with data directory path."""
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        self.client = KnowledgeBaseClient()
    
    def load_entries_from_file(self, file_path: Path) -> List[KnowledgeEntry]:
        """Load knowledge entries from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entries = []
            for entry_data in data:
                try:
                    entry = KnowledgeEntry(**entry_data)
                    entries.append(entry)
                except Exception as e:
                    print(f"Error parsing entry {entry_data.get('id', 'unknown')} in {file_path}: {e}")
            
            return entries
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return []
    
    def load_all_entries(self) -> List[KnowledgeEntry]:
        """Load all knowledge entries from all JSON files in data directory."""
        all_entries = []
        
        # Load from root data directory
        for json_file in self.data_dir.glob("*.json"):
            entries = self.load_entries_from_file(json_file)
            all_entries.extend(entries)
            print(f"Loaded {len(entries)} entries from {json_file.name}")
        
        # Load from subdirectories
        for subdir in self.data_dir.iterdir():
            if subdir.is_dir():
                for json_file in subdir.glob("*.json"):
                    entries = self.load_entries_from_file(json_file)
                    all_entries.extend(entries)
                    print(f"Loaded {len(entries)} entries from {subdir.name}/{json_file.name}")
        
        return all_entries
    
    def index_all_entries(self, force_reindex: bool = False) -> int:
        """Load and index all entries into the vector database."""
        if force_reindex:
            print("Force reindexing: clearing existing collection...")
            # Note: In production, implement collection clearing
            # For now, we'll just add/update entries
        
        entries = self.load_all_entries()
        if not entries:
            print("No entries found to index")
            return 0
        
        print(f"Indexing {len(entries)} entries into vector database...")
        self.client.add_entries_batch(entries)
        print(f"Successfully indexed {len(entries)} entries")
        
        return len(entries)
    
    def validate_entries(self) -> Dict[str, List[str]]:
        """Validate all entries and return validation results."""
        entries = self.load_all_entries()
        results = {
            "valid": [],
            "errors": [],
            "warnings": []
        }
        
        seen_ids = set()
        for entry in entries:
            # Check for duplicate IDs
            if entry.id in seen_ids:
                results["errors"].append(f"Duplicate ID found: {entry.id}")
            else:
                seen_ids.add(entry.id)
                results["valid"].append(entry.id)
            
            # Check URL accessibility (basic format check)
            if not entry.ato_url.startswith("https://www.ato.gov.au"):
                results["warnings"].append(f"Non-ATO URL for {entry.id}: {entry.ato_url}")
            
            # Check content length
            if len(entry.content) < 100:
                results["warnings"].append(f"Short content for {entry.id}: {len(entry.content)} chars")
            
            # Check keywords
            if len(entry.keywords) < 2:
                results["warnings"].append(f"Few keywords for {entry.id}: {len(entry.keywords)}")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        entries = self.load_all_entries()
        
        stats = {
            "total_entries": len(entries),
            "by_category": {},
            "by_tax_year": {},
            "avg_content_length": 0,
            "total_keywords": 0
        }
        
        total_content_length = 0
        all_keywords = set()
        
        for entry in entries:
            # Category stats
            stats["by_category"][entry.category] = stats["by_category"].get(entry.category, 0) + 1
            
            # Tax year stats
            stats["by_tax_year"][entry.tax_year] = stats["by_tax_year"].get(entry.tax_year, 0) + 1
            
            # Content stats
            total_content_length += len(entry.content)
            all_keywords.update(entry.keywords)
        
        if entries:
            stats["avg_content_length"] = total_content_length // len(entries)
        stats["total_keywords"] = len(all_keywords)
        
        return stats


def main():
    """Main function for command-line usage."""
    indexer = KnowledgeIndexer()
    
    print("=== Knowledge Base Indexer ===")
    
    # Show statistics
    print("\n1. Current Statistics:")
    stats = indexer.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Categories: {dict(stats['by_category'])}")
    print(f"   Tax years: {dict(stats['by_tax_year'])}")
    print(f"   Avg content length: {stats['avg_content_length']} chars")
    
    # Validate entries
    print("\n2. Validation Results:")
    validation = indexer.validate_entries()
    print(f"   Valid entries: {len(validation['valid'])}")
    print(f"   Errors: {len(validation['errors'])}")
    print(f"   Warnings: {len(validation['warnings'])}")
    
    if validation["errors"]:
        print("   Error details:")
        for error in validation["errors"]:
            print(f"     - {error}")
    
    # Index entries
    print("\n3. Indexing entries...")
    try:
        indexed_count = indexer.index_all_entries()
        print(f"   Successfully indexed {indexed_count} entries")
    except Exception as e:
        print(f"   Error during indexing: {e}")


if __name__ == "__main__":
    main()