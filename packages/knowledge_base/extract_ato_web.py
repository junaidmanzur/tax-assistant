#!/usr/bin/env python3
"""Extract ATO web knowledge base data and save to atoweb directory."""

import sys
import json
from pathlib import Path

# Add packages to Python path
sys.path.insert(0, 'packages')

from knowledge_base.extractor import extract_ato_knowledge

def main():
    print("=== Extracting ATO Web Knowledge Data ===\n")
    
    # Extract all entries
    entries = extract_ato_knowledge()
    print(f"✅ Successfully extracted {len(entries)} knowledge entries")
    
    # Convert to dictionaries for JSON serialization
    all_data = [entry.dict() for entry in entries]
    
    # Save to JSON file in atoweb directory
    output_file = Path("data/atoweb/tax-rates-australian-residents.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved ALL {len(all_data)} entries to: {output_file}")
    
    # Show summary statistics
    print(f"\n📊 Data Summary:")
    
    # Count by tags
    tag_counts = {}
    section_counts = {}
    content_lengths = []
    
    for entry in entries:
        content_lengths.append(len(entry.content))
        
        # Count tags
        for tag in entry.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Count sections
        if entry.section:
            section_counts[entry.section] = section_counts.get(entry.section, 0) + 1
    
    print(f"   Total entries: {len(entries)}")
    print(f"   Average content length: {sum(content_lengths)//len(content_lengths)} chars")
    print(f"   Min content length: {min(content_lengths)} chars")
    print(f"   Max content length: {max(content_lengths)} chars")
    
    print(f"\n🏷️  Top Tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {tag}: {count} entries")
    
    print(f"\n📑 Top Sections:")
    for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {section}: {count} entries")

if __name__ == "__main__":
    main()