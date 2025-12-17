"""
JDIH Document Scraper
Download Indonesian government documents from JDIH portals

Features:
- Multi-portal support (BPK, Kemenkeu, Kemnaker, etc.)
- Category filtering
- Download management
- Progress tracking
- Inventory creation
"""

import requests
from bs4 import BeautifulSoup
import time
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from datetime import datetime
from tqdm import tqdm


@dataclass
class Document:
    """JDIH document metadata."""
    title: str
    url: str
    doc_type: str  # UU, PP, Perpres, Permen, etc.
    number: str
    year: str
    category: str
    portal: str
    file_path: Optional[str] = None
    downloaded: bool = False
    download_date: Optional[str] = None


class JDIHScraper:
    """
    Web scraper for JDIH (Jaringan Dokumentasi dan Informasi Hukum) portals.
    
    Supported portals:
    - BPK (Badan Pemeriksa Keuangan)
    - Kemenkeu (Kementerian Keuangan)
    - Kemnaker (Kementerian Ketenagakerjaan)
    - And more...
    """
    
    PORTALS = {
        "bpk": "https://jdih.bpk.go.id",
        "kemenkeu": "https://jdih.kemenkeu.go.id",
        "kemnaker": "https://jdih.kemnaker.go.id",
        # Add more as needed
    }
    
    CATEGORIES = [
        "civil_administration",   # KTP, KK, Akta
        "employment",              # Ketenagakerjaan
        "business_licensing",      # Perizinan usaha
        "social_assistance",       # Bantuan sosial
        "general_governance",      # Pemerintahan umum
    ]
    
    def __init__(
        self,
        download_dir: str = "data/documents/pdfs",
        max_docs: int = 50,
        delay: float = 2.0
    ):
        """
        Initialize JDIH scraper.
        
        Args:
            download_dir: Directory to save PDFs
            max_docs: Maximum documents to download
            delay: Delay between requests (seconds, be respectful!)
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_docs = max_docs
        self.delay = delay
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot)'
        })
        
        self.inventory: List[Document] = []
        self.downloaded_count = 0
    
    def search_portal(
        self,
        portal_name: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Document]:
        """
        Search a specific JDIH portal.
        
        Args:
            portal_name: Portal identifier (e.g., 'bpk')
            category: Document category filter
            limit: Max results to return
        
        Returns:
            List of Document objects
        """
        if portal_name not in self.PORTALS:
            raise ValueError(f"Unknown portal: {portal_name}")
        
        base_url = self.PORTALS[portal_name]
        
        # Note: Actual implementation would use portal-specific search API
        # This is a placeholder structure
        
        print(f"🔍 Searching {portal_name.upper()} portal...")
        
        documents = []
        
        # Placeholder: Would make actual HTTP requests here
        # For now, return empty list (manual download in Week 1)
        
        return documents
    
    def download_document(self, doc: Document) -> bool:
        """
        Download a single document.
        
        Args:
            doc: Document to download
        
        Returns:
            True if successful, False otherwise
        """
        if self.downloaded_count >= self.max_docs:
            print(f"📊 Reached max download limit ({self.max_docs})")
            return False
        
        try:
            print(f"📥 Downloading: {doc.title[:50]}...")
            
            # Make request
            response = self.session.get(doc.url, timeout=30)
            response.raise_for_status()
            
            # Generate filename
            filename = self._generate_filename(doc)
            filepath = self.download_dir / filename
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Update document
            doc.file_path = str(filepath)
            doc.downloaded = True
            doc.download_date = datetime.now().isoformat()
            
            self.downloaded_count += 1
            
            # Be respectful - delay between requests
            time.sleep(self.delay)
            
            print(f"   ✅ Saved to: {filename}")
            return True
        
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
    
    def _generate_filename(self, doc: Document) -> str:
        """Generate safe filename from document metadata."""
        # Clean title for filename
        clean_title = "".join(
            c if c.isalnum() or c in (' ', '_', '-') else '_'
            for c in doc.title[:50]
        )
        clean_title = clean_title.strip().replace(' ', '_')
        
        # Format: DocType_Number_Year_Title.pdf
        filename = f"{doc.doc_type}_{doc.number}_{doc.year}_{clean_title}.pdf"
        
        return filename
    
    def download_batch(
        self,
        documents: List[Document],
        show_progress: bool = True
    ) -> int:
        """
        Download multiple documents.
        
        Args:
            documents: List of documents to download
            show_progress: Show progress bar
        
        Returns:
            Number of successfully downloaded documents
        """
        success_count = 0
        
        iterator = tqdm(documents) if show_progress else documents
        
        for doc in iterator:
            if self.download_document(doc):
                success_count += 1
                self.inventory.append(doc)
        
        return success_count
    
    def save_inventory(self, filepath: str = "data/documents/inventory.csv"):
        """Save document inventory to CSV."""
        import csv
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Title', 'Type', 'Number', 'Year', 'Category', 
                'Portal', 'Downloaded', 'File Path', 'Download Date'
            ])
            
            # Data
            for doc in self.inventory:
                writer.writerow([
                    doc.title,
                    doc.doc_type,
                    doc.number,
                    doc.year,
                    doc.category,
                    doc.portal,
                    doc.downloaded,
                    doc.file_path or '',
                    doc.download_date or ''
                ])
        
        print(f"📊 Inventory saved to: {filepath}")
    
    def load_manual_documents(self, metadata_file: str) -> List[Document]:
        """
        Load manually downloaded documents from metadata file.
        
        For Week 1, we'll manually download ~50 PDFs and create metadata JSON.
        
        Args:
            metadata_file: Path to JSON metadata file
        
        Returns:
            List of Document objects
        """
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        
        for item in data['documents']:
            doc = Document(
                title=item['title'],
                url=item.get('url', ''),
                doc_type=item['type'],
                number=item['number'],
                year=item['year'],
                category=item['category'],
                portal=item['portal'],
                file_path=item.get('file_path'),
                downloaded=True,
                download_date=item.get('download_date')
            )
            documents.append(doc)
        
        self.inventory.extend(documents)
        print(f"📚 Loaded {len(documents)} documents from metadata")
        
        return documents
    
    def get_stats(self) -> Dict:
        """Get download statistics."""
        stats = {
            "total_documents": len(self.inventory),
            "downloaded": sum(1 for d in self.inventory if d.downloaded),
            "by_type": {},
            "by_category": {},
            "by_portal": {},
        }
        
        for doc in self.inventory:
            # By type
            stats["by_type"][doc.doc_type] = stats["by_type"].get(doc.doc_type, 0) + 1
            
            # By category
            stats["by_category"][doc.category] = stats["by_category"].get(doc.category, 0) + 1
            
            # By portal
            stats["by_portal"][doc.portal] = stats["by_portal"].get(doc.portal, 0) + 1
        
        return stats
    
    def print_stats(self):
        """Print download statistics."""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 DOWNLOAD STATISTICS")
        print("="*60)
        print(f"Total Documents:  {stats['total_documents']}")
        print(f"Downloaded:       {stats['downloaded']}")
        
        print("\n📄 By Document Type:")
        for doc_type, count in sorted(stats['by_type'].items()):
            print(f"  {doc_type}: {count}")
        
        print("\n📁 By Category:")
        for category, count in sorted(stats['by_category'].items()):
            print(f"  {category}: {count}")
        
        print("\n🌐 By Portal:")
        for portal, count in sorted(stats['by_portal'].items()):
            print(f"  {portal}: {count}")
        
        print("="*60 + "\n")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_sample_metadata():
    """Create sample metadata file for manual downloads (Week 1)."""
    
    metadata = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "description": "Manually downloaded Indonesian government documents",
        "documents": [
            {
                "title": "Peraturan Presiden tentang KTP Elektronik",
                "type": "Perpres",
                "number": "26",
                "year": "2009",
                "category": "civil_administration",
                "portal": "manual",
                "url": "https://jdih.example.com/docs/...",
                "file_path": "data/documents/pdfs/Perpres_26_2009_KTP_Elektronik.pdf",
                "download_date": datetime.now().isoformat()
            },
            # Add more documents here...
        ]
    }
    
    output_path = "data/documents/metadata.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Sample metadata created: {output_path}")
    print(f"   Edit this file and add your manually downloaded documents!")


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_scraper():
    """Demo the scraper functionality."""
    
    print("🧪 JDIH Scraper Demo\n")
    
    # Initialize scraper
    scraper = JDIHScraper(max_docs=10, delay=1.0)
    
    # For Week 1, we'll use manual download approach
    print("📋 Week 1 Approach: Manual Download")
    print("="*60)
    print("1. Create sample metadata file")
    print("2. Manually download ~50 PDFs from JDIH portals")
    print("3. Update metadata.json with document info")
    print("4. Load documents into inventory")
    print("="*60 + "\n")
    
    # Create sample metadata
    create_sample_metadata()
    
    # Show statistics (would be populated after manual downloads)
    scraper.print_stats()
    
    # Save inventory
    scraper.save_inventory()
    
    print("✅ Demo complete!")
    print("\n📝 Next steps:")
    print("   1. Download PDFs from JDIH portals (see DATA_SOURCE_AUDIT.md)")
    print("   2. Place PDFs in data/documents/pdfs/")
    print("   3. Update data/documents/metadata.json")
    print("   4. Run scraper.load_manual_documents('data/documents/metadata.json')")


if __name__ == "__main__":
    demo_scraper()
