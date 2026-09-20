"""Web content extractor for ATO pages with RAG-friendly chunking strategy."""
import re
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup, Tag
import json
from knowledge_base.schemas import KnowledgeEntry


class ATOContentExtractor:
    """Extracts and chunks ATO web content for RAG optimization."""
    
    def __init__(self, rate_limit_delay: float = 2.0, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; TaxAssistant/1.0; Educational Research; +https://github.com/example/tax-assistant)'
        })
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.last_request_time = 0
        self.robots_cache = {}
        self.sitemap_cache = {}
    
    def _respect_rate_limit(self):
        """Implement polite rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"Rate limiting: sleeping for {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, '/robots.txt')
        
        if base_url not in self.robots_cache:
            try:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                self._respect_rate_limit()
                rp.read()
                self.robots_cache[base_url] = rp
                print(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                print(f"Could not load robots.txt from {robots_url}: {e}")
                # If we can't load robots.txt, assume it's allowed
                return True
        
        robots_parser = self.robots_cache.get(base_url)
        if robots_parser:
            user_agent = self.session.headers.get('User-Agent', '*')
            can_fetch = robots_parser.can_fetch(user_agent, url)
            if not can_fetch:
                print(f"robots.txt disallows fetching {url}")
            return can_fetch
        
        return True
    
    def _discover_sitemap_urls(self, base_url: str) -> List[str]:
        """Discover URLs from sitemap.xml if available."""
        if base_url in self.sitemap_cache:
            return self.sitemap_cache[base_url]
        
        sitemap_urls = []
        sitemap_locations = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/sitemaps/sitemap.xml')
        ]
        
        # Also check robots.txt for sitemap declarations
        robots_parser = self.robots_cache.get(base_url)
        if robots_parser:
            for sitemap in robots_parser.site_maps():
                sitemap_locations.append(sitemap)
        
        for sitemap_url in sitemap_locations:
            try:
                print(f"Checking sitemap: {sitemap_url}")
                response = self._fetch_with_retries(sitemap_url)
                if response:
                    sitemap_urls.extend(self._parse_sitemap(response.text))
                    break
            except Exception as e:
                print(f"Could not process sitemap {sitemap_url}: {e}")
        
        self.sitemap_cache[base_url] = sitemap_urls
        return sitemap_urls
    
    def _parse_sitemap(self, sitemap_content: str) -> List[str]:
        """Parse sitemap XML and extract URLs."""
        urls = []
        try:
            root = ET.fromstring(sitemap_content)
            
            # Handle sitemap index files
            for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    # Recursively parse sub-sitemaps
                    try:
                        response = self._fetch_with_retries(loc.text)
                        if response:
                            urls.extend(self._parse_sitemap(response.text))
                    except Exception as e:
                        print(f"Error parsing sub-sitemap {loc.text}: {e}")
            
            # Handle regular sitemap files
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    urls.append(loc.text)
            
        except ET.ParseError as e:
            print(f"Could not parse sitemap XML: {e}")
        
        return urls
    
    def _fetch_with_retries(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic and proper error handling."""
        for attempt in range(self.max_retries):
            try:
                self._respect_rate_limit()
                print(f"Fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    backoff_time = (2 ** attempt) * self.rate_limit_delay
                    print(f"Backing off for {backoff_time:.1f}s before retry")
                    time.sleep(backoff_time)
                else:
                    print(f"All {self.max_retries} attempts failed for {url}")
        
        return None
    
    def extract_page(self, url: str) -> List[KnowledgeEntry]:
        """Extract content from a single ATO page and return chunked entries."""
        try:
            # Check robots.txt compliance
            if not self._check_robots_txt(url):
                print(f"Skipping {url} due to robots.txt restrictions")
                return []
            
            # Fetch with retries
            response = self._fetch_with_retries(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response, url)
            
            # Remove boilerplate
            cleaned_soup = self._remove_boilerplate(soup)
            
            # Extract structured content chunks
            chunks = self._extract_chunks(cleaned_soup, metadata)
            
            return chunks
            
        except Exception as e:
            print(f"Error extracting {url}: {e}")
            return []
    
    def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response, url: str) -> Dict[str, Any]:
        """Extract page metadata including last updated dates."""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'jurisdiction': 'AU',
            'source_type': 'web',
            'retrieved_at': datetime.now().strftime('%Y-%m-%d'),
            'last_modified_header': None,
            'last_updated_claimed': None
        }
        
        # Extract HTTP Last-Modified header
        if 'Last-Modified' in response.headers:
            try:
                last_modified = datetime.strptime(
                    response.headers['Last-Modified'], 
                    '%a, %d %b %Y %H:%M:%S %Z'
                )
                metadata['last_modified_header'] = last_modified.isoformat() + 'Z'
            except ValueError:
                pass
        
        # Extract claimed last updated date using multiple strategies
        metadata['last_updated_claimed'] = (
            self._extract_last_updated_from_meta(soup)
            or self._extract_last_updated_from_json_ld(soup)
            or self._extract_last_updated_from_time_tag(soup)
            or self._extract_last_updated_from_text(soup)
        )

        return metadata

    def _normalize_date(self, text: str) -> Optional[str]:
        """Normalize various date strings to YYYY-MM-DD. Returns None if not parseable."""
        if not text:
            return None
        t = text.strip()

        # ISO 8601 like 2025-06-18 or 2025-06-18T10:30:00Z
        m = re.search(r'(20\d{2})-(\d{1,2})-(\d{1,2})', t)
        if m:
            y, mo, d = m.groups()
            return f"{y}-{int(mo):02d}-{int(d):02d}"

        # Month name maps (long and short)
        month_map = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12,
        }

        # Patterns like 18 June 2025
        m = re.search(r'\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(20\d{2})\b', t)
        if m:
            d, mon, y = m.groups()
            mon_i = month_map.get(mon.lower())
            if mon_i:
                return f"{y}-{mon_i:02d}-{int(d):02d}"

        # Patterns like June 18, 2025
        m = re.search(r'\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b', t)
        if m:
            mon, d, y = m.groups()
            mon_i = month_map.get(mon.lower())
            if mon_i:
                return f"{y}-{mon_i:02d}-{int(d):02d}"

        # Australian numeric dd/mm/yyyy
        m = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b', t)
        if m:
            d, mo, y = m.groups()
            y = f"20{y}" if len(y) == 2 else y
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

        return None

    def _extract_last_updated_from_meta(self, soup: BeautifulSoup) -> Optional[str]:
        """Check common meta tags that carry modified/updated timestamps."""
        meta_candidates = []
        # property-based
        meta_candidates.extend(soup.select('meta[property="article:modified_time"]'))
        meta_candidates.extend(soup.select('meta[property="og:updated_time"]'))
        meta_candidates.extend(soup.select('meta[property="dcterms.modified"], meta[property="dcterms:modified"]'))
        # name-based
        meta_candidates.extend(soup.select('meta[name="last-modified"], meta[name="modified"], meta[name="modified-date"], meta[name="updated"], meta[name="dateModified"], meta[name="DC.Date.Modified"], meta[name="dc.date.modified"], meta[name="dcterms.modified"]'))

        for tag in meta_candidates:
            content = tag.get('content') or tag.get('value')
            normalized = self._normalize_date(content) if content else None
            if normalized:
                return normalized
        return None

    def _extract_last_updated_from_json_ld(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse JSON-LD for dateModified if present."""
        for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
            try:
                data = json.loads(script.string or script.text or '{}')
            except Exception:
                continue
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if not isinstance(obj, dict):
                    continue
                for key in ['dateModified', 'dateUpdated', 'modified', 'lastModified']:
                    if key in obj:
                        normalized = self._normalize_date(str(obj[key]))
                        if normalized:
                            return normalized
        return None

    def _extract_last_updated_from_time_tag(self, soup: BeautifulSoup) -> Optional[str]:
        """Look for <time datetime="..."> elements near update labels."""
        time_tags = soup.select('time[datetime]')
        for t in time_tags:
            label_context = (t.get('class') or []) + ((t.parent.get('class') or []) if t.parent else [])
            label_text = ' '.join(label_context).lower() + ' ' + (t.parent.get_text(' ', strip=True).lower() if t.parent else '')
            if any(x in label_text for x in ['updated', 'modified', 'last updated', 'page last updated']):
                normalized = self._normalize_date(t.get('datetime', ''))
                if normalized:
                    return normalized
        for t in time_tags:
            normalized = self._normalize_date(t.get('datetime', ''))
            if normalized:
                return normalized
        return None

    def _extract_last_updated_from_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Scan visible text for common ATO update labels and parse the date."""
        patterns = [
            r'page\s+last\s+updated[:\s]+(.{,40})',
            r'last\s+updated[:\s]+(.{,40})',
            r'last\s+modified[:\s]+(.{,40})',
            r'updated\s+on[:\s]+(.{,40})',
            r'content\s+last\s+updated[:\s]+(.{,40})',
        ]

        for el in soup.find_all(text=True):
            text = (el or '').strip()
            if not text:
                continue
            lower = text.lower()
            for pat in patterns:
                m = re.search(pat, lower, flags=re.IGNORECASE)
                if m:
                    candidate = m.group(1)
                    candidate = candidate.split('\n')[0][:50]
                    normalized = self._normalize_date(candidate)
                    if normalized:
                        return normalized
            if re.search(r'last\s+(updated|modified)', lower):
                normalized = self._normalize_date(text)
                if normalized:
                    return normalized
        normalized = self._normalize_date(soup.get_text(' ', strip=True))
        return normalized
    
    def _remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove navigation, footers, sidebars, and other boilerplate content."""
        # Remove common boilerplate selectors
        selectors_to_remove = [
            'nav', 'header', 'footer', '.sidebar', '.navigation',
            '.breadcrumb', '.print-block', '.share-widget',
            '.back-to-top', '.page-tools', '.feedback',
            '[class*="print"]', '[class*="download"]', '[class*="share"]',
            '.skip-link', '.screen-reader-text'
        ]
        
        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove script and style tags
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()
        
        return soup
    
    def _extract_chunks(self, soup: BeautifulSoup, metadata: Dict[str, Any]) -> List[KnowledgeEntry]:
        """Extract content chunks based on heading structure with overlap."""
        chunks = []
        
        # Find main content area
        main_content = soup.find('main') or soup.find(class_=re.compile(r'content|main')) or soup
        
        # Extract page title
        page_title = soup.find('h1')
        title_text = page_title.get_text(strip=True) if page_title else "Untitled"
        
        # Find all headings that structure the content
        headings = main_content.find_all(['h2', 'h3'], string=True)
        
        # Extract section chunks with overlap
        for i, heading in enumerate(headings):
            section_chunks = self._extract_section_chunks_with_overlap(heading, headings, i, metadata, title_text)
            chunks.extend(section_chunks)
        
        # Handle tables as separate chunks
        tables = main_content.find_all('table')
        for table in tables:
            table_chunks = self._extract_table_chunks_with_overlap(table, metadata, title_text, main_content)
            chunks.extend(table_chunks)
        
        return chunks
    
    def _extract_section_chunks_with_overlap(self, heading: Tag, all_headings: List[Tag], 
                                           index: int, metadata: Dict[str, Any], page_title: str) -> List[KnowledgeEntry]:
        """Extract content chunks for a section - keep natural section boundaries."""
        chunks = []
        section_title = heading.get_text(strip=True)
        
        # Collect all content for this section
        content_parts = []
        current = heading.next_sibling
        
        while current:
            if isinstance(current, Tag):
                if current.name in ['h2', 'h3'] and current in all_headings[index + 1:]:
                    break
                if current.name not in ['table']:  # Tables handled separately
                    text = current.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            elif isinstance(current, str):
                text = current.strip()
                if text:
                    content_parts.append(text)
            current = current.next_sibling
        
        if not content_parts:
            return chunks
        
        # Join all content
        full_content = ' '.join(content_parts)
        
        # Clean the content
        full_content = self._clean_content(full_content)
        
        # Split into chunks with 300-800 token range and 10-15% overlap
        target_size = 2400  # ~600 tokens (middle of 300-800 range)
        min_size = 1200     # ~300 tokens
        max_size = 3200     # ~800 tokens
        overlap_size = int(target_size * 0.125)  # 12.5% overlap
        
        if len(full_content) <= max_size:
            # Content fits in one chunk within token range
            if len(full_content) >= min_size:
                chunks.append(self._create_knowledge_entry(
                    full_content, section_title, heading, metadata, page_title, 0
                ))
            elif len(full_content) >= 50:
                # Small chunk but still useful - keep it
                chunks.append(self._create_knowledge_entry(
                    full_content, section_title, heading, metadata, page_title, 0
                ))
        else:
            # Split large content into overlapping chunks
            chunk_num = 0
            start = 0
            
            while start < len(full_content):
                end = min(start + target_size, len(full_content))
                
                # Find a good break point (sentence or paragraph boundary)
                if end < len(full_content):
                    # Look for sentence ending within last 200 chars
                    search_start = max(end - 200, start)
                    sentence_ends = [m.end() for m in re.finditer(r'[.!?]\s+', full_content[search_start:end])]
                    if sentence_ends:
                        end = search_start + sentence_ends[-1]
                
                chunk_content = full_content[start:end].strip()
                
                if len(chunk_content) >= 50:  # Minimum viable content
                    chunks.append(self._create_knowledge_entry(
                        chunk_content, section_title, heading, metadata, page_title, chunk_num
                    ))
                    chunk_num += 1
                
                # Move start position with overlap
                if end >= len(full_content):
                    break
                start = end - overlap_size
        
        return chunks
    
    def _create_knowledge_entry(self, content: str, section_title: str, heading: Tag, 
                              metadata: Dict[str, Any], page_title: str, chunk_num: int) -> KnowledgeEntry:
        """Create a KnowledgeEntry from processed content."""
        # Extract actual anchor from heading element, fallback to generated
        anchor = self._extract_anchor_from_element(heading) or self._generate_anchor(section_title)
        if chunk_num > 0:
            anchor = f"{anchor}-part-{chunk_num + 1}"
        
        # Determine effective years; no tags (removed as requested)
        effective_years = self._extract_years_from_content(content, section_title)

        # Include effective years in ID to ensure uniqueness
        years_suffix = "-".join(effective_years) if effective_years else "general"
        chunk_id = f"{metadata['domain'].replace('.', '_')}_{anchor}_{years_suffix}_{metadata['retrieved_at'].replace('-', '')}"
        
        title = f"{page_title} - {section_title}"
        if chunk_num > 0:
            title = f"{title} (Part {chunk_num + 1})"
        
        return KnowledgeEntry(
            id=chunk_id,
            url=metadata['url'],
            title=title,
            section=section_title,
            anchor=anchor,
            content=content,
            jurisdiction=metadata['jurisdiction'],
            domain=metadata['domain'],
            source_type=metadata['source_type'],
            last_updated_claimed=metadata['last_updated_claimed'],
            last_modified_header=metadata['last_modified_header'],
            retrieved_at=metadata['retrieved_at'],
            effective_years=effective_years,
            tags=[]
        )
    
    def _extract_section_chunk(self, heading: Tag, all_headings: List[Tag], 
                             index: int, metadata: Dict[str, Any], page_title: str) -> Optional[KnowledgeEntry]:
        """Extract a content chunk for a specific section."""
        section_title = heading.get_text(strip=True)
        
        # Generate anchor from heading
        anchor = self._generate_anchor(section_title)
        
        # Collect content until next heading of same or higher level
        content_parts = []
        current = heading.next_sibling
        
        while current:
            if isinstance(current, Tag):
                if current.name in ['h2', 'h3'] and current in all_headings[index + 1:]:
                    break
                if current.name not in ['table']:  # Tables handled separately
                    text = current.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            elif isinstance(current, str):
                text = current.strip()
                if text:
                    content_parts.append(text)
            current = current.next_sibling
        
        if not content_parts:
            return None
        
        content = ' '.join(content_parts)
        content = self._clean_content(content)
        
        # Skip if content too short
        if len(content) < 50:
            return None
        
        # Clean the content
        content = self._clean_content(content)
        
        # Determine effective years; no tags (removed)
        effective_years = self._extract_years_from_content(content, section_title)
        
        # Include effective years in ID to ensure uniqueness
        years_suffix = "-".join(effective_years) if effective_years else "general"
        chunk_id = f"{metadata['domain'].replace('.', '_')}_{anchor}_{years_suffix}_{metadata['retrieved_at'].replace('-', '')}"
        
        return KnowledgeEntry(
            id=chunk_id,
            url=metadata['url'],
            title=f"{page_title} - {section_title}",
            section=section_title,
            anchor=anchor,
            content=content,
            jurisdiction=metadata['jurisdiction'],
            domain=metadata['domain'],
            source_type=metadata['source_type'],
            last_updated_claimed=metadata['last_updated_claimed'],
            last_modified_header=metadata['last_modified_header'],
            retrieved_at=metadata['retrieved_at'],
            effective_years=effective_years,
            tags=[]
        )
    
    def _format_table(self, table: Tag, table_title: str) -> str:
        """Format table content in clean, natural format for RAG."""
        if not table:
            return ""
            
        content_parts = [table_title]  # Just the title, no "Table:" prefix
        
        # Extract table headers
        headers = []
        header_row = table.find('thead')
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
        else:
            # Try to find headers in first row
            first_row = table.find('tr')
            if first_row:
                header_cells = first_row.find_all(['th', 'td'])
            else:
                header_cells = []
        
        for cell in header_cells:
            cell_text = cell.get_text(strip=True)
            if cell_text:
                headers.append(cell_text)
        
        # Add headers as a simple line
        if headers:
            content_parts.append(" | ".join(headers))
            content_parts.append("")  # Empty line for separation
        
        # Extract table rows (skip header row if it exists)
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = table.find_all('tr')
            # Skip first row if it contains headers
            if rows and all(cell.name == 'th' for cell in rows[0].find_all(['th', 'td'])):
                rows = rows[1:]
        
        # Process each data row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = []
            
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                # Clean and normalize cell content
                if cell_text:
                    # Handle currency and percentage formatting
                    cell_text = re.sub(r'\$(\d+),(\d{3})', r'$\1,\2', cell_text)
                    cell_text = re.sub(r'(\d+)\s*%', r'\1%', cell_text)
                    cell_text = re.sub(r'(\d+)\s*c\b', r'\1 cents', cell_text)
                    row_data.append(cell_text)
                else:
                    row_data.append("")
            
            if row_data:
                # Skip header row duplicates (check if row data matches headers)
                if headers and row_data == headers:
                    continue
                
                # Simple pipe-separated format
                clean_row = " | ".join(row_data)
                if clean_row.strip():  # Only add non-empty rows
                    content_parts.append(clean_row)
        
        return "\n".join(content_parts)
    
    def _extract_table_chunks_with_overlap(self, table: Tag, metadata: Dict[str, Any], page_title: str, soup_context: BeautifulSoup = None) -> List[KnowledgeEntry]:
        """Extract table content with chunking and overlap if needed."""
        chunks = []
        
        # Get table caption first (preferred)
        caption = table.find('caption')
        if caption:
            table_title = caption.get_text(strip=True)
        else:
            # Look for preceding heading in DOM tree
            prev_heading = table.find_previous(['h2', 'h3', 'h4'])
            if prev_heading:
                table_title = prev_heading.get_text(strip=True)
            else:
                table_title = "Data Table"
        
        # Extract and format table content for better readability
        full_content = self._format_table(table, table_title)
        
        if not full_content:
            return chunks
        
        # Get table headers for potential reuse in chunks
        content_lines = full_content.split('\n')
        header_info = []
        for line in content_lines[:3]:  # Check first few lines for headers
            if line.startswith('Table:') or line.startswith('Columns:'):
                header_info.append(line)
        
        # Split table into chunks with 300-800 token range and 10-15% overlap if needed
        target_size = 2400  # ~600 tokens
        min_size = 1200     # ~300 tokens
        max_size = 3200     # ~800 tokens
        overlap_size = int(target_size * 0.125)  # 12.5% overlap
        
        if len(full_content) <= max_size:
            # Table fits in one chunk within token range
            if len(full_content) >= min_size:
                chunks.append(self._create_table_knowledge_entry(
                    full_content, table_title, table, metadata, page_title, 0
                ))
            elif len(full_content) >= 50:
                # Small table but still useful - keep it
                chunks.append(self._create_table_knowledge_entry(
                    full_content, table_title, table, metadata, page_title, 0
                ))
        else:
            # Split large table into chunks with overlap
            chunk_num = 0
            start = 0
            
            while start < len(full_content):
                end = min(start + target_size, len(full_content))
                
                # For tables, try to break at row boundaries
                if end < len(full_content):
                    # Look for "Row " markers or newlines within last 300 chars
                    search_start = max(end - 300, start)
                    search_text = full_content[search_start:end]
                    
                    # Look for row boundaries
                    row_matches = [m.start() for m in re.finditer(r'\nRow \d+', search_text)]
                    if row_matches:
                        end = search_start + row_matches[-1] + 1
                    else:
                        # Fallback to newline boundaries
                        newlines = [i for i, char in enumerate(search_text) if char == '\n']
                        if newlines:
                            end = search_start + newlines[-1] + 1
                
                chunk_content = full_content[start:end].strip()
                
                # Ensure each chunk has table headers if this is not the first chunk
                if chunk_num > 0 and header_info:
                    # Check if headers are already present
                    if not any(header in chunk_content for header in header_info):
                        header_text = '\n'.join(header_info)
                        chunk_content = f"{header_text}\n\n{chunk_content}"
                
                if len(chunk_content) >= 50:  # Minimum viable content
                    chunks.append(self._create_table_knowledge_entry(
                        chunk_content, table_title, table, metadata, page_title, chunk_num
                    ))
                    chunk_num += 1
                
                # Move start position with overlap
                if end >= len(full_content):
                    break
                start = end - overlap_size
        
        return chunks
    
    def _create_table_knowledge_entry(self, content: str, table_title: str, table: Tag,
                                    metadata: Dict[str, Any], page_title: str, chunk_num: int) -> KnowledgeEntry:
        """Create a KnowledgeEntry for table content."""
        # For tables, find the associated heading's anchor
        table_heading = table.find_previous(['h2', 'h3', 'h4'])
        
        anchor = self._extract_anchor_from_element(table_heading) or self._generate_anchor(table_title)
        if chunk_num > 0:
            anchor = f"{anchor}-part-{chunk_num + 1}"
        
        effective_years = self._extract_years_from_content(content, table_title)

        # Include section text in the ID to ensure uniqueness
        sections_text = re.sub(r'\s+', '_', table_title.lower())
        chunk_id = f"{metadata['domain'].replace('.', '_')}_table_{anchor}_{sections_text}_{metadata['retrieved_at'].replace('-', '')}"
        
        title = f"{page_title} - {table_title}"
        if chunk_num > 0:
            title = f"{title} (Part {chunk_num + 1})"
        
        return KnowledgeEntry(
            id=chunk_id,
            url=metadata['url'],
            title=title,
            section=table_title,
            anchor=anchor,
            content=content,
            jurisdiction=metadata['jurisdiction'],
            domain=metadata['domain'],
            source_type=metadata['source_type'],
            last_updated_claimed=metadata['last_updated_claimed'],
            last_modified_header=metadata['last_modified_header'],
            retrieved_at=metadata['retrieved_at'],
            effective_years=effective_years,
            tags=[]
        )
    
    def _extract_table_chunk(self, table: Tag, metadata: Dict[str, Any], page_title: str) -> Optional[KnowledgeEntry]:
        """Extract a table as a separate chunk (legacy method - prefer _extract_table_chunks_with_overlap)."""
        # Get table caption first (preferred)
        caption = table.find('caption')
        if caption:
            table_title = caption.get_text(strip=True)
        else:
            # Look for preceding heading in DOM tree
            prev_heading = table.find_previous(['h2', 'h3', 'h4'])
            if prev_heading:
                table_title = prev_heading.get_text(strip=True)
            else:
                table_title = "Data Table"
        
        # Extract and format table content for better readability
        content = self._format_table(table, table_title)
        
        if not content or len(content) < 50:
            return None
        
        # Generate metadata
        table_heading = table.find_previous(['h2', 'h3', 'h4']) if hasattr(table, 'find_previous') else None
        anchor = self._extract_anchor_from_element(table_heading) or self._generate_anchor(table_title)
        effective_years = self._extract_years_from_content(content, table_title)
        
        # Include title text in ID to ensure uniqueness
        title_text = re.sub(r'\s+', '_', table_title.lower())
        chunk_id = f"{metadata['domain'].replace('.', '_')}_{anchor}_{title_text}_{metadata['retrieved_at'].replace('-', '')}"
        return KnowledgeEntry(
            id=chunk_id,
            url=metadata['url'],
            title=f"{page_title} - {table_title}",
            section=table_title,
            anchor=anchor,
            content=content,
            jurisdiction=metadata['jurisdiction'],
            domain=metadata['domain'],
            source_type=metadata['source_type'],
            last_updated_claimed=metadata['last_updated_claimed'],
            last_modified_header=metadata['last_modified_header'],
            retrieved_at=metadata['retrieved_at'],
            effective_years=effective_years,
            tags=[]
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text with comprehensive cleanup."""
        # Fix unicode issues first
        content = content.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Normalize unicode characters
        content = content.replace('\u2013', '-')  # en dash to hyphen
        content = content.replace('\u2014', '-')  # em dash to hyphen
        content = content.replace('\u2019', "'")  # right single quote
        content = content.replace('\u201c', '"')  # left double quote
        content = content.replace('\u201d', '"')  # right double quote
        content = content.replace('\u00a0', ' ')  # non-breaking space
        content = content.replace('\u00b7', '·')  # middle dot
        
        # Collapse whitespace (including tabs, newlines, multiple spaces)
        content = re.sub(r'\s+', ' ', content)
        
        # Canonicalize number formats
        content = re.sub(r'\$(\d+),(\d{3})', r'$\1,\2', content)  # Ensure proper comma placement
        content = re.sub(r'(\d+)\s*%', r'\1%', content)  # Remove spaces before %
        content = re.sub(r'(\d+)\s*c\b', r'\1c', content)  # Remove spaces before 'c' (cents)
        content = re.sub(r'(\d+)\s*cents?\b', r'\1 cents', content)  # Normalize cents
        
        # Normalize currency expressions
        content = re.sub(r'\$(\d+)\s+(\d+)', r'$\1\2', content)  # Fix separated numbers
        content = re.sub(r'(\d+)\.00\b', r'\1', content)  # Remove .00 from whole numbers
        
        # Clean up common formatting issues
        content = re.sub(r'\s*\|\s*', ' | ', content)  # Normalize table separators
        content = re.sub(r'\s*-\s*', ' - ', content)  # Normalize dashes
        content = re.sub(r'\s*:\s*', ': ', content)  # Normalize colons
        
        # Remove duplicate consecutive words (common OCR/parsing error)
        words = content.split()
        deduplicated = []
        prev_word = None
        for word in words:
            if word != prev_word or len(word) <= 3:  # Keep short words even if repeated
                deduplicated.append(word)
            prev_word = word
        content = ' '.join(deduplicated)
        
        # Final cleanup
        content = re.sub(r'\s+', ' ', content)  # Final whitespace collapse
        content = content.strip()
        
        return content
    
    def _extract_anchor_from_element(self, element: Tag) -> Optional[str]:
        """Extract the actual anchor ID from an HTML element."""
        if element and element.get('id'):
            return element.get('id')
        return None
    
    def _generate_anchor(self, text: str) -> str:
        """Generate kebab-case anchor from text as fallback."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor.strip('-')
    
    
    def _extract_years_from_content(self, content: str, title: str) -> List[str]:
        """Extract year references from content and title for temporal context."""
        years = []
        
        # Look for various year patterns: "2025", "2024-25", "2025-26"
        combined_text = content + " " + title
        year_matches = re.findall(r'20\d{2}(?:[-–]\d{2})?', combined_text)
        for match in year_matches:
            normalized = match.replace('–', '-')  # Normalize dash
            if normalized not in years:
                years.append(normalized)
        
        return years[:5]  # Limit to first 5 years to avoid noise
    
    # Tags generation removed – data will not include tags


def extract_ato_knowledge(use_sitemap: bool = True) -> List[KnowledgeEntry]:
    """Extract knowledge from specified URLs and optionally from sitemap discovery."""
    extractor = ATOContentExtractor(rate_limit_delay=3.0, max_retries=3)
    
    target_urls = [
        "https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents",
        "https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy-surcharge/medicare-levy-surcharge-income-thresholds-and-rates"
    ]
    
    all_urls = target_urls.copy()
    
    # Discover additional URLs from sitemap if requested
    if use_sitemap:
        print("Discovering URLs from ATO sitemap...")
        try:
            sitemap_urls = extractor._discover_sitemap_urls("https://www.ato.gov.au")
            
            # Only allow the two specific URLs we want - filter sitemap for exact matches
            allowed_urls = set(target_urls)
            
            for url in sitemap_urls:
                if url in allowed_urls and url not in all_urls:
                    all_urls.append(url)
                    print(f"Found target URL in sitemap: {url}")
            
            print(f"Total URLs to process: {len(all_urls)} (restricted to specified URLs only)")
            
        except Exception as e:
            print(f"Sitemap discovery failed, proceeding with target URLs only: {e}")
    
    all_entries = []
    successful_extractions = 0
    
    for i, url in enumerate(all_urls):
        print(f"\n[{i+1}/{len(all_urls)}] Extracting content from {url}...")
        entries = extractor.extract_page(url)
        if entries:
            all_entries.extend(entries)
            successful_extractions += 1
            print(f"✅ Extracted {len(entries)} chunks from {url}")
        else:
            print(f"❌ No content extracted from {url}")
    
    print(f"\n🎯 Extraction Summary:")
    print(f"   URLs processed: {len(all_urls)}")
    print(f"   Successful extractions: {successful_extractions}")
    print(f"   Total knowledge chunks: {len(all_entries)}")
    
    return all_entries


if __name__ == "__main__":
    entries = extract_ato_knowledge()
    print(f"Total extracted entries: {len(entries)}")
    
    # Show sample entry
    if entries:
        print("\nSample entry:")
        print(f"ID: {entries[0].id}")
        print(f"Title: {entries[0].title}")
        print(f"Content: {entries[0].content[:200]}...")
        print(f"Tags: {entries[0].tags}")
        print(f"Effective years: {entries[0].effective_years}")
