#!/usr/bin/env python3
"""
Parallelized PDF Downloader for Literature Review Corpus

Reads consultation table CSV and downloads all PDFs where keep_in_corpus=TRUE.
Features:
- Parallel downloads with configurable workers
- Exponential backoff retry logic
- Comprehensive logging
- Progress tracking
- Resume capability (skips existing files)

Usage:
    python download_pdfs.py consultation_table.csv --output-dir ./pdfs --workers 5
"""

import argparse
import csv
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_download.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create requests session with retry strategy."""
    session = requests.Session()
    
    # Retry strategy with exponential backoff
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,  # Wait 1, 2, 4, 8, 16 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set reasonable timeout
    session.timeout = 30
    
    # User agent to avoid blocking
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    })
    
    return session


def sanitize_filename(authors: str, year: str, title: str) -> str:
    """
    Create safe filename from citation metadata.
    
    Format: AuthorYear_TitleWords.pdf
    Example: SmithJones2023_ClimateFinance.pdf
    """
    # Extract first author's last name
    first_author = authors.split(';')[0].split(',')[0].strip()
    first_author = first_author.replace(' ', '')
    
    # Take first 3 significant words from title
    title_words = [w for w in title.split() if len(w) > 3][:3]
    title_part = ''.join(title_words).replace(' ', '')
    
    # Remove unsafe characters
    safe_chars = ''.join(c for c in f"{first_author}{year}_{title_part}" 
                        if c.isalnum() or c in ['_', '-'])
    
    return f"{safe_chars}.pdf"


def download_pdf(
    row: Dict[str, str], 
    output_dir: Path, 
    session: requests.Session
) -> Tuple[str, bool, str]:
    """
    Download a single PDF with exponential backoff.
    
    Returns:
        Tuple of (filename, success, message)
    """
    authors = row['authors']
    year = row['year']
    title = row['title']
    url = row['url']
    doi = row.get('doi', '')
    
    filename = sanitize_filename(authors, year, title)
    filepath = output_dir / filename
    
    # Skip if already downloaded
    if filepath.exists():
        return filename, True, "Already exists (skipped)"
    
    # Try URL first, then DOI if URL fails
    urls_to_try = [url]
    if doi:
        urls_to_try.append(f"https://doi.org/{doi}")
    
    for attempt_url in urls_to_try:
        if not attempt_url or attempt_url.lower() == 'nan':
            continue
            
        try:
            logger.info(f"Downloading: {filename} from {attempt_url}")
            
            response = session.get(attempt_url, timeout=30)
            response.raise_for_status()
            
            # Check if response is actually PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"{filename}: Not a PDF ({content_type})")
                continue
            
            # Write to file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Downloaded: {filename}")
            return filename, True, "Success"
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed {attempt_url}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error for {filename}: {str(e)}")
            continue
    
    return filename, False, "All download attempts failed"


def load_consultation_table(csv_path: Path) -> List[Dict[str, str]]:
    """Load consultation table and filter for keep_in_corpus=TRUE."""
    to_download = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keep = row.get('keep_in_corpus', '').upper()
            if keep == 'TRUE' or keep == '1' or keep == 'YES':
                to_download.append(row)
    
    logger.info(f"Loaded {len(to_download)} PDFs to download from {csv_path}")
    return to_download


def download_corpus(
    csv_path: Path,
    output_dir: Path,
    max_workers: int = 5
) -> Tuple[int, int]:
    """
    Download entire corpus in parallel.
    
    Returns:
        Tuple of (successful_downloads, failed_downloads)
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load documents to download
    documents = load_consultation_table(csv_path)
    
    if not documents:
        logger.warning("No documents marked for download!")
        return 0, 0
    
    # Track statistics
    successful = 0
    failed = 0
    
    # Create session for reuse
    session = create_session()
    
    # Download in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_pdf, doc, output_dir, session): doc
            for doc in documents
        }
        
        for future in as_completed(futures):
            filename, success, message = future.result()
            
            if success:
                successful += 1
            else:
                failed += 1
                logger.error(f"✗ Failed: {filename} - {message}")
            
            # Progress update
            total = successful + failed
            logger.info(f"Progress: {total}/{len(documents)} "
                       f"({successful} ✓, {failed} ✗)")
    
    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description='Download PDFs from literature review consultation table'
    )
    parser.add_argument(
        'csv_file',
        type=Path,
        help='Path to consultation table CSV file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('./pdfs'),
        help='Output directory for downloaded PDFs (default: ./pdfs)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel download workers (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.csv_file.exists():
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("PDF Corpus Downloader")
    logger.info(f"Input CSV: {args.csv_file}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Parallel workers: {args.workers}")
    logger.info("="*60)
    
    # Start download
    start_time = time.time()
    
    successful, failed = download_corpus(
        args.csv_file,
        args.output_dir,
        args.workers
    )
    
    elapsed = time.time() - start_time
    
    # Summary
    logger.info("="*60)
    logger.info("Download Complete")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total time: {elapsed:.1f} seconds")
    logger.info(f"PDFs saved to: {args.output_dir}")
    logger.info("="*60)
    
    if failed > 0:
        logger.warning("Some downloads failed. Check pdf_download.log for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
