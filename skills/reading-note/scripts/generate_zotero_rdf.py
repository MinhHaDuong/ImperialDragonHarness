#!/usr/bin/env python3
"""
Generate Zotero RDF file from metadata and reading note.
Creates a format compatible with Zotero import.
"""

import json
import sys
from datetime import datetime
from xml.sax.saxutils import escape

def generate_zotero_rdf(metadata, note_content, output_file):
    """
    Generate Zotero RDF file with metadata and attached note.
    
    Args:
        metadata: Dict with article metadata (title, authors, doi, etc.)
        note_content: String with full reading note content
        output_file: Path to output RDF file
    """
    
    # Build RDF structure
    rdf_parts = []
    
    # RDF header
    rdf_parts.append('''<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns:z="http://www.zotero.org/namespaces/export#"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:bib="http://purl.org/net/biblio#"
 xmlns:foaf="http://xmlns.com/foaf/0.1/"
 xmlns:link="http://purl.org/rss/1.0/modules/link/"
 xmlns:prism="http://prismstandard.org/namespaces/1.2/basic/">
''')
    
    # Determine item type
    item_type = metadata.get('type', 'journal-article')
    zotero_type = 'journalArticle' if 'article' in item_type else 'document'
    
    # Article entry
    item_uri = f"urn:isbn:{metadata.get('doi', 'unknown')}"
    
    rdf_parts.append(f'''    <bib:Article rdf:about="{escape(item_uri)}">
        <z:itemType>{zotero_type}</z:itemType>
        <dc:title>{escape(metadata.get('title', 'Unknown Title'))}</dc:title>
''')
    
    # Authors
    authors = metadata.get('authors', 'Unknown Author')
    for author in authors.split(', '):
        if author and author != 'et al.':
            rdf_parts.append(f'        <bib:authors><rdf:Seq><rdf:li><foaf:Person><foaf:surname>{escape(author.split()[-1])}</foaf:surname></foaf:Person></rdf:li></rdf:Seq></bib:authors>\n')
    
    # Publication details
    if metadata.get('journal'):
        rdf_parts.append(f'        <prism:publicationName>{escape(metadata["journal"])}</prism:publicationName>\n')
    
    if metadata.get('volume'):
        rdf_parts.append(f'        <prism:volume>{escape(str(metadata["volume"]))}</prism:volume>\n')
    
    if metadata.get('issue'):
        rdf_parts.append(f'        <prism:number>{escape(str(metadata["issue"]))}</prism:number>\n')
    
    if metadata.get('pages'):
        rdf_parts.append(f'        <bib:pages>{escape(metadata["pages"])}</bib:pages>\n')
    
    if metadata.get('year'):
        rdf_parts.append(f'        <dc:date>{escape(metadata["year"])}</dc:date>\n')
    
    # DOI and URL
    if metadata.get('doi'):
        rdf_parts.append(f'        <dc:identifier>DOI {escape(metadata["doi"])}</dc:identifier>\n')
    
    if metadata.get('url'):
        rdf_parts.append(f'        <dc:identifier>{escape(metadata["url"])}</dc:identifier>\n')
    
    # Abstract if available
    if metadata.get('abstract'):
        rdf_parts.append(f'        <dcterms:abstract>{escape(metadata["abstract"][:500])}...</dcterms:abstract>\n')
    
    # Close article entry
    rdf_parts.append('    </bib:Article>\n')
    
    # Add note as attachment
    note_uri = f"{item_uri}/note"
    rdf_parts.append(f'''    <z:Attachment rdf:about="{escape(note_uri)}">
        <z:itemType>note</z:itemType>
        <z:linkMode>1</z:linkMode>
        <dc:title>Reading Note</dc:title>
        <link:link rdf:resource="{escape(item_uri)}"/>
        <dcterms:dateSubmitted>{datetime.now().isoformat()}</dcterms:dateSubmitted>
        <z:note><![CDATA[{note_content}]]></z:note>
    </z:Attachment>
''')
    
    # Close RDF
    rdf_parts.append('</rdf:RDF>\n')
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(rdf_parts))
    
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_zotero_rdf.py <metadata.json> <reading_note.md> [output.rdf]", file=sys.stderr)
        sys.exit(1)
    
    metadata_file = sys.argv[1]
    note_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'zotero_import.rdf'
    
    # Load metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Load reading note
    with open(note_file, 'r', encoding='utf-8') as f:
        note_content = f.read()
    
    # Generate RDF
    if generate_zotero_rdf(metadata, note_content, output_file):
        print(f"Zotero RDF file created: {output_file}")
        print(f"Import this file into Zotero: File → Import → {output_file}")
        return 0
    else:
        print("Error generating RDF file", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
