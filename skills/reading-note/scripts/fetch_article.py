#!/usr/bin/env python3
"""
Fetch article metadata and PDF from DOI or citation.
Handles multiple sources: DOI.org, Crossref, Unpaywall, arXiv, HAL.
"""

import json
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def clean_doi(doi_or_url):
    """Extract clean DOI from various input formats."""
    # Handle full URLs
    if doi_or_url.startswith('http'):
        # Extract DOI from URL
        match = re.search(r'10\.\d{4,}/[^\s]+', doi_or_url)
        if match:
            doi_or_url = match.group(0)
    
    # Clean up DOI
    doi = doi_or_url.strip()
    doi = doi.replace('doi:', '').replace('DOI:', '')
    doi = doi.strip('/')
    
    return doi

def fetch_crossref_metadata(doi):
    """Fetch metadata from Crossref API."""
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    headers = {'User-Agent': 'ReadingNoteBot/1.0 (mailto:research@example.org)'}
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('message', {})
    except (HTTPError, URLError) as e:
        print(f"Warning: Crossref fetch failed: {e}", file=sys.stderr)
        return None

def fetch_unpaywall_pdf(doi):
    """Try to get open access PDF URL from Unpaywall."""
    email = "research@example.org"  # Required by Unpaywall API
    url = f"https://api.unpaywall.org/v2/{quote(doi, safe='')}?email={email}"
    
    try:
        req = Request(url)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Try best_oa_location first
            if data.get('best_oa_location', {}).get('url_for_pdf'):
                return data['best_oa_location']['url_for_pdf']
            
            # Try oa_locations
            for loc in data.get('oa_locations', []):
                if loc.get('url_for_pdf'):
                    return loc['url_for_pdf']
                    
    except (HTTPError, URLError) as e:
        print(f"Info: Unpaywall check failed (article may not be OA): {e}", file=sys.stderr)
    
    return None

def check_arxiv(doi_or_title):
    """Check if article is on arXiv based on DOI or title."""
    # arXiv DOI pattern: 10.48550/arXiv.*
    if isinstance(doi_or_title, str) and '10.48550/arXiv' in doi_or_title:
        arxiv_id = doi_or_title.split('arXiv.')[-1]
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    return None

def download_pdf(url, output_path):
    """Download PDF from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            content_type = response.headers.get('Content-Type', '')
            
            if 'pdf' not in content_type.lower():
                print(f"Warning: URL may not be PDF (Content-Type: {content_type})", file=sys.stderr)
            
            with open(output_path, 'wb') as f:
                f.write(response.read())
            
            return True
            
    except (HTTPError, URLError) as e:
        print(f"Error downloading PDF: {e}", file=sys.stderr)
        return False

def format_authors(authors_list):
    """Format author list from Crossref data."""
    if not authors_list:
        return "Unknown Author"
    
    formatted = []
    for author in authors_list[:3]:  # First 3 authors
        family = author.get('family', '')
        given = author.get('given', '')
        if family and given:
            formatted.append(f"{given} {family}")
        elif family:
            formatted.append(family)
    
    if len(authors_list) > 3:
        formatted.append("et al.")
    
    return ", ".join(formatted)

def extract_year(date_parts):
    """Extract year from Crossref date-parts."""
    if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
        return str(date_parts[0][0])
    return "n.d."

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_article.py <DOI or citation>", file=sys.stderr)
        sys.exit(1)
    
    doi_input = ' '.join(sys.argv[1:])
    doi = clean_doi(doi_input)
    
    print(f"Fetching metadata for DOI: {doi}")
    
    # Fetch metadata
    metadata = fetch_crossref_metadata(doi)
    
    if not metadata:
        print("Error: Could not fetch metadata from Crossref", file=sys.stderr)
        sys.exit(1)
    
    # Extract key fields
    result = {
        'doi': doi,
        'title': metadata.get('title', ['Unknown Title'])[0] if metadata.get('title') else 'Unknown Title',
        'authors': format_authors(metadata.get('author', [])),
        'year': extract_year(metadata.get('published', {}).get('date-parts')),
        'journal': metadata.get('container-title', [''])[0] if metadata.get('container-title') else '',
        'volume': metadata.get('volume', ''),
        'issue': metadata.get('issue', ''),
        'pages': metadata.get('page', ''),
        'url': metadata.get('URL', f'https://doi.org/{doi}'),
        'abstract': metadata.get('abstract', ''),
        'type': metadata.get('type', 'journal-article'),
    }
    
    # Output metadata as JSON
    print(json.dumps(result, indent=2))
    
    # Try to fetch PDF
    print("\nAttempting to fetch PDF...", file=sys.stderr)
    
    pdf_url = None
    
    # Check arXiv first
    pdf_url = check_arxiv(doi)
    
    # Try Unpaywall if not arXiv
    if not pdf_url:
        pdf_url = fetch_unpaywall_pdf(doi)
    
    if pdf_url:
        output_file = f"article_{doi.replace('/', '_')}.pdf"
        print(f"Found PDF URL: {pdf_url}", file=sys.stderr)
        print(f"Downloading to: {output_file}", file=sys.stderr)
        
        if download_pdf(pdf_url, output_file):
            print(f"PDF downloaded successfully: {output_file}", file=sys.stderr)
            result['pdf_file'] = output_file
        else:
            print("PDF download failed", file=sys.stderr)
    else:
        print("No open access PDF found. You may need to download manually.", file=sys.stderr)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
