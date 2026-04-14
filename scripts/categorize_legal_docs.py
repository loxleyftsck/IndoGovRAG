"""
Legal Document Categorization System (Lege/Jure/Lex)

Automatically categorizes documents into:
- Legal (UU, PP, Perpres, Permen) 
- Operational (Panduan, Syarat, Prosedur)
- FAQ/Tips

Enables smart retrieval based on query type.
"""

import json
import re
from typing import Dict, List, Literal
from pathlib import Path
from enum import Enum

class DocumentCategory(Enum):
    """Document category types"""
    # Legal Documents (Lege/Jure)
    LEGAL_UU = "legal_uu"                    # Undang-Undang
    LEGAL_PP = "legal_pp"                    # Peraturan Pemerintah
    LEGAL_PERPRES = "legal_perpres"          # Peraturan Presiden
    LEGAL_PERMEN = "legal_permen"            # Peraturan Menteri
    LEGAL_PERDA = "legal_perda"              # Peraturan Daerah
    LEGAL_OTHER = "legal_other"              # Other legal
    
    # Operational Documents (Lex)
    OPERATIONAL_GUIDE = "operational_guide"   # Panduan/Guide
    OPERATIONAL_REQ = "operational_req"       # Syarat/Requirements
    OPERATIONAL_PROC = "operational_proc"     # Prosedur/Procedures
    
    # Support Documents
    FAQ = "faq"                              # FAQ
    TIPS = "tips"                            # Tips & Tricks

class LegalDocumentClassifier:
    """
    Classifies documents into legal vs operational categories
    """
    
    # Legal indicators
    LEGAL_PATTERNS = {
        'uu': r'(?i)(undang[-\s]undang|^uu\s|\buu\b|uu\s*no\.?\s*\d+)',
        'pp': r'(?i)(peraturan\s+pemerintah|^pp\s|\bpp\b|pp\s*no\.?\s*\d+)',
        'perpres': r'(?i)(peraturan\s+presiden|^perpres\s|perpres\s*no\.?\s*\d+)',
        'permen': r'(?i)(peraturan\s+menteri|^permen\s|permen\s*\w+\s*no\.?\s*\d+)',
        'perda': r'(?i)(peraturan\s+daerah|^perda\s|perda\s*no\.?\s*\d+)',
    }
    
    # Legal source URLs
    LEGAL_SOURCES = [
        'jdih.setkab.go.id',
        'peraturan.go.id',
        'jdih.kemenkeu.go.id',
        'jdih',
        '/PUU',
        '/peraturan/',
    ]
    
    # Operational indicators
    OPERATIONAL_KEYWORDS = {
        'guide': ['panduan', 'petunjuk', 'cara', 'tutorial'],
        'req': ['syarat', 'persyaratan', 'requirement'],
        'proc': ['prosedur', 'tahapan', 'langkah', 'proses'],
        'faq': ['faq', 'pertanyaan', 'tanya jawab'],
        'tips': ['tips', 'trik', 'kiat'],
    }
    
    def classify(self, doc: Dict) -> DocumentCategory:
        """
        Classify a single document
        
        Args:
            doc: Document dict with 'title', 'source_url', 'content'
            
        Returns:
            DocumentCategory enum
        """
        title = doc.get('title', '').lower()
        url = doc.get('source_url', '').lower()
        content = doc.get('content', '')[:500].lower()  # First 500 chars
        
        # Check if legal document
        legal_cat = self._check_legal(title, url, content)
        if legal_cat:
            return legal_cat
        
        # Check operational type
        operational_cat = self._check_operational(title, content)
        if operational_cat:
            return operational_cat
        
        # Default: operational guide
        return DocumentCategory.OPERATIONAL_GUIDE
    
    def _check_legal(self, title: str, url: str, content: str) -> DocumentCategory | None:
        """Check if document is legal"""
        
        # Check URL first (most reliable)
        if any(src in url for src in self.LEGAL_SOURCES):
            # Determine type from title/content
            for doc_type, pattern in self.LEGAL_PATTERNS.items():
                if re.search(pattern, title) or re.search(pattern, content):
                    return DocumentCategory[f'LEGAL_{doc_type.upper()}']
            return DocumentCategory.LEGAL_OTHER
        
        # Check title patterns
        for doc_type, pattern in self.LEGAL_PATTERNS.items():
            if re.search(pattern, title):
                return DocumentCategory[f'LEGAL_{doc_type.upper()}']
        
        # Check content for strong legal markers
        legal_markers = ['pasal', 'ayat', 'bab', 'bagian', 'ketentuan umum']
        marker_count = sum(1 for marker in legal_markers if marker in content)
        
        if marker_count >= 3:  # Strong legal structure
            # Try to determine type
            for doc_type, pattern in self.LEGAL_PATTERNS.items():
                if re.search(pattern, content):
                    return DocumentCategory[f'LEGAL_{doc_type.upper()}']
            return DocumentCategory.LEGAL_OTHER
        
        return None
    
    def _check_operational(self, title: str, content: str) -> DocumentCategory | None:
        """Check operational document type"""
        
        # Check FAQ
        if any(kw in title or kw in content for kw in self.OPERATIONAL_KEYWORDS['faq']):
            return DocumentCategory.FAQ
        
        # Check Tips
        if any(kw in title for kw in self.OPERATIONAL_KEYWORDS['tips']):
            return DocumentCategory.TIPS
        
        # Check Requirements
        if any(kw in title for kw in self.OPERATIONAL_KEYWORDS['req']):
            return DocumentCategory.OPERATIONAL_REQ
        
        # Check Procedures
        if any(kw in title for kw in self.OPERATIONAL_KEYWORDS['proc']):
            return DocumentCategory.OPERATIONAL_PROC
        
        # Default operational
        return DocumentCategory.OPERATIONAL_GUIDE
    
    def enrich_metadata(self, doc: Dict) -> Dict:
        """
        Add category metadata to document
        
        Args:
            doc: Original document dict
            
        Returns:
            Enriched document with metadata
        """
        category = self.classify(doc)
        
        doc['metadata'] = doc.get('metadata', {})
        doc['metadata']['doc_category'] = category.value
        doc['metadata']['is_legal'] = category.value.startswith('legal_')
        doc['metadata']['category_confidence'] = self._calculate_confidence(doc, category)
        
        # Add hierarchical tags
        if category.value.startswith('legal_'):
            doc['metadata']['doc_type'] = 'legal'
            doc['metadata']['legal_type'] = category.value.replace('legal_', '')
        else:
            doc['metadata']['doc_type'] = 'operational'
            doc['metadata']['operational_type'] = category.value.replace('operational_', '')
        
        return doc
    
    def _calculate_confidence(self, doc: Dict, category: DocumentCategory) -> float:
        """Calculate classification confidence (0.0-1.0)"""
        confidence = 0.5  # Base
        
        title = doc.get('title', '').lower()
        url = doc.get('source_url', '').lower()
        
        # Boost for URL match
        if category.value.startswith('legal_'):
            if any(src in url for src in self.LEGAL_SOURCES):
                confidence += 0.4
        
        # Boost for title pattern match
        category_key = category.value.replace('legal_', '').replace('operational_', '')
        if category_key in self.LEGAL_PATTERNS:
            if re.search(self.LEGAL_PATTERNS[category_key], title):
                confidence += 0.3
        
        return min(confidence, 1.0)


def categorize_all_documents(input_files: List[str], output_file: str):
    """
    Categorize all documents from input files
    
    Args:
        input_files: List of JSON file paths
        output_file: Output path for categorized documents
    """
    classifier = LegalDocumentClassifier()
    
    all_docs = []
    stats = {
        'total': 0,
        'legal': 0,
        'operational': 0,
        'by_category': {}
    }
    
    # Load and categorize
    for file_path in input_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)
            
        for doc in docs:
            enriched = classifier.enrich_metadata(doc)
            all_docs.append(enriched)
            
            # Update stats
            stats['total'] += 1
            category = enriched['metadata']['doc_category']
            
            if enriched['metadata']['is_legal']:
                stats['legal'] += 1
            else:
                stats['operational'] += 1
            
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
    
    # Save categorized documents
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    
    # Print stats
    print("\n" + "="*60)
    print("📊 CATEGORIZATION COMPLETE")
    print("="*60)
    print(f"Total documents: {stats['total']}")
    print(f"  Legal: {stats['legal']} ({stats['legal']/stats['total']*100:.1f}%)")
    print(f"  Operational: {stats['operational']} ({stats['operational']/stats['total']*100:.1f}%)")
    
    print(f"\nBy Category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    print(f"\n✅ Saved to: {output_path}")
    print("="*60 + "\n")
    
    return all_docs, stats


def main():
    """Main execution"""
    import sys
    
    # Input files
    input_files = [
        'data/scraped/jina_government_20260111_203413.json',
        'data/scraped/jina_extended_20260111_205123.json',
    ]
    
    output_file = 'data/scraped/categorized_all_documents.json'
    
    print("="*60)
    print("🏛️ Legal Document Categorization System")
    print("="*60)
    print("Purpose: Separate Legal (Lege/Jure) from Operational (Lex)")
    print("="*60 + "\n")
    
    # Categorize
    docs, stats = categorize_all_documents(input_files, output_file)
    
    # Example: Show some legal docs
    legal_docs = [d for d in docs if d['metadata']['is_legal']]
    if legal_docs:
        print(f"\n📜 Sample Legal Documents ({len(legal_docs)} total):")
        for doc in legal_docs[:5]:
            print(f"  - {doc['title'][:60]}...")
            print(f"    Category: {doc['metadata']['doc_category']}")
            print(f"    Confidence: {doc['metadata']['category_confidence']:.2f}")
    else:
        print("\n⚠️  No legal documents found!")
        print("   Recommendation: Manually add UU/PP/Perpres documents")
    
    print("\n" + "="*60)
    print("✅ Categorization system ready!")
    print("="*60)


if __name__ == "__main__":
    main()
