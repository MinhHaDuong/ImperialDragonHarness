#!/usr/bin/env python3
"""
ISTEX Search API Client

Queries search.istex.fr French academic database and structures results
for ingestion into consultation table.

API Documentation: https://api.istex.fr/documentation/

Usage:
    python search_istex.py "climate finance" --year-start 1990 --year-end 2025 --output results_istex.csv
"""

import argparse
import csv
import sys
import time
from typing import List, Dict

import requests

API_BASE = "https://api.istex.fr"

def build_query(
    keywords: str,
    year_start: int = None,
    year_end: int = None,
    doc_types: List[str] = None
) -> str:
    """
    Build ISTEX query string.
    
    Args:
        keywords: Search terms
        year_start: Earliest publication year
        year_end: Latest publication year
        doc_types: List of document types to include
        
    Returns:
        Query string for ISTEX API
    """
    query_parts = [keywords]
    
    if year_start and year_end:
        query_parts.append(f"publicationDate:[{year_start} TO {year_end}]")
    elif year_start:
        query_parts.append(f"publicationDate:[{year_start} TO *]")
    elif year_end:
        query_parts.append(f"publicationDate:[* TO {year_end}]")
    
    if doc_types:
        type_query = " OR ".join([f'genre.raw:"{dt}"' for dt in doc_types])
        query_parts.append(f"({type_query})")
    
    return " AND ".join(query_parts)


def search_istex(
    query: str,
    size: int = 100,
    offset: int = 0
) -> Dict:
    """
    Execute search against ISTEX API.
    
    Args:
        query: Constructed query string
        size: Number of results per page
        offset: Starting position
        
    Returns:
        JSON response from API
    """
    params = {
        'q': query,
        'size': min(size, 100),  # API max is 100 per page
        'offset': offset,
        'output': 'id,author,title,publicationDate,genre,abstract,doi,fulltext'
    }
    
    url = f"{API_BASE}/document/"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying ISTEX: {e}", file=sys.stderr)
        return None


def extract_results(response: Dict) -> List[Dict[str, str]]:
    """
    Extract and structure results for consultation table.
    
    Returns list of dicts with keys:
        source_id, search_source, category, authors, year, title, 
        doi, url, abstract
    """
    if not response or 'hits' not in response:
        return []
    
    results = []
    
    for hit in response['hits']:
        # Extract authors
        authors_list = []
        for author in hit.get('author', []):
            name = author.get('name', '')
            if name:
                authors_list.append(name)
        authors = "; ".join(authors_list)
        
        # Determine category from genre
        genre = hit.get('genre', [''])[0] if isinstance(hit.get('genre'), list) else hit.get('genre', '')
        category = map_genre_to_bibtex(genre)
        
        # Extract year from publicationDate
        pub_date = hit.get('publicationDate', '')
        year = pub_date[:4] if len(pub_date) >= 4 else ''
        
        # Get fulltext URL if available
        fulltext = hit.get('fulltext', [])
        pdf_url = ''
        if fulltext:
            for ft in fulltext:
                if ft.get('mimetype') == 'application/pdf':
                    pdf_url = ft.get('uri', '')
                    break
        
        result = {
            'source_id': hit.get('id', ''),
            'search_source': 'search.istex.fr',
            'category': category,
            'authors': authors,
            'year': year,
            'title': hit.get('title', ''),
            'doi': hit.get('doi', [''])[0] if isinstance(hit.get('doi'), list) else hit.get('doi', ''),
            'url': pdf_url,
            'abstract': hit.get('abstract', '')
        }
        
        results.append(result)
    
    return results


def map_genre_to_bibtex(genre: str) -> str:
    """Map ISTEX genre to BibLaTeX category."""
    genre_map = {
        'research-article': '@article',
        'article': '@article',
        'review-article': '@article',
        'book': '@book',
        'chapter': '@incollection',
        'conference': '@inproceedings',
        'report': '@report',
        'other': '@misc'
    }
    
    genre_lower = genre.lower()
    for key, value in genre_map.items():
        if key in genre_lower:
            return value
    
    return '@misc'


def search_all(
    query: str,
    max_results: int = 500
) -> List[Dict[str, str]]:
    """
    Search with pagination to get up to max_results.
    """
    all_results = []
    offset = 0
    page_size = 100
    
    while len(all_results) < max_results:
        print(f"Fetching results {offset} to {offset + page_size}...", file=sys.stderr)
        
        response = search_istex(query, size=page_size, offset=offset)
        
        if not response:
            break
        
        results = extract_results(response)
        
        if not results:
            break
        
        all_results.extend(results)
        
        # Check if more results available
        total = response.get('total', 0)
        if offset + page_size >= total or offset + page_size >= max_results:
            break
        
        offset += page_size
        time.sleep(0.5)  # Rate limiting courtesy
    
    return all_results[:max_results]


def save_to_csv(results: List[Dict[str, str]], output_file: str):
    """Save results to CSV file."""
    if not results:
        print("No results to save", file=sys.stderr)
        return
    
    fieldnames = ['source_id', 'search_source', 'category', 'authors', 'year', 
                  'title', 'doi', 'url', 'abstract']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Saved {len(results)} results to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Search ISTEX French academic database'
    )
    parser.add_argument('keywords', help='Search keywords')
    parser.add_argument('--year-start', type=int, help='Earliest publication year')
    parser.add_argument('--year-end', type=int, help='Latest publication year')
    parser.add_argument('--max-results', type=int, default=500, help='Maximum results to retrieve')
    parser.add_argument('--output', default='results_istex.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Build query
    query = build_query(args.keywords, args.year_start, args.year_end)
    
    print(f"Query: {query}")
    print("Searching ISTEX...")
    
    # Search
    results = search_all(query, args.max_results)
    
    print(f"Found {len(results)} results")
    
    # Save
    save_to_csv(results, args.output)


if __name__ == '__main__':
    main()
