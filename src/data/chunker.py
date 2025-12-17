"""
Document Chunking for RAG Pipeline

Implements semantic chunking strategy:
- Target: 512 tokens per chunk
- Preserve context boundaries
- Add metadata for retrieval
- Calculate coherence scores
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class Chunk:
    """Document chunk with metadata."""
    text: str
    doc_id: str
    chunk_id: int
    start_char: int
    end_char: int
    num_tokens: int
    metadata: Dict
    coherence_score: Optional[float] = None


class DocumentChunker:
    """
    Semantic chunking for Indonesian government documents.
    
    Strategy:
    - Split on natural boundaries (paragraphs, sections)
    - Target 512 tokens (configurable)
    - Overlap for context preservation
    - Maintain document structure metadata
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 128,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target tokens per chunk
            overlap: Token overlap between chunks
            min_chunk_size: Minimum chunk size
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk(
        self,
        text: str,
        doc_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Chunk document into semantic segments.
        
        Args:
            text: Document text
            doc_id: Document identifier
            metadata: Optional document metadata
        
        Returns:
            List of Chunk objects
        """
        if not metadata:
            metadata = {}
        
        # Split into paragraphs first (natural boundaries)
        paragraphs = self._split_paragraphs(text)
        
        # Group paragraphs into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        char_position = 0
        
        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            
            # If paragraph alone exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk,
                        doc_id,
                        len(chunks),
                        char_position - len(''.join(current_chunk)),
                        char_position,
                        metadata
                    )
                    chunks.append(chunk)
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph
                para_chunks = self._split_large_text(para, doc_id, len(chunks), metadata)
                chunks.extend(para_chunks)
            
            # Add paragraph to current chunk
            elif current_tokens + para_tokens <= self.chunk_size:
                current_chunk.append(para)
                current_tokens += para_tokens
            
            # Start new chunk
            else:
                # Save current chunk
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk,
                        doc_id,
                        len(chunks),
                        char_position - len(''.join(current_chunk)),
                        char_position,
                        metadata
                    )
                    chunks.append(chunk)
                
                # Start new with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_tokens = self._count_tokens(''.join(current_chunk))
            
            char_position += len(para)
        
        # Add final chunk
        if current_chunk and current_tokens >= self.min_chunk_size:
            chunk = self._create_chunk(
                current_chunk,
                doc_id,
                len(chunks),
                char_position - len(''.join(current_chunk)),
                char_position,
                metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or explicit markers
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # Clean and filter
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_large_text(
        self,
        text: str,
        doc_id: str,
        start_chunk_id: int,
        metadata: Dict
    ) -> List[Chunk]:
        """Split text that exceeds chunk size."""
        chunks = []
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_tokens = 0
        char_pos = 0
        
        for sentence in sentences:
            sent_tokens = self._count_tokens(sentence)
            
            if current_tokens + sent_tokens <= self.chunk_size:
                current_chunk.append(sentence)
                current_tokens += sent_tokens
            else:
                # Save current
                if current_chunk:
                    chunk = self._create_chunk(
                        current_chunk,
                        doc_id,
                        start_chunk_id + len(chunks),
                        char_pos - len(''.join(current_chunk)),
                        char_pos,
                        metadata
                    )
                    chunks.append(chunk)
                
                # Start new
                current_chunk = [sentence]
                current_tokens = sent_tokens
            
            char_pos += len(sentence)
        
        # Final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk,
                doc_id,
                start_chunk_id + len(chunks),
                char_pos - len(''.join(current_chunk)),
                char_pos,
                metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (could be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, chunks: List[str]) -> str:
        """Get overlap text from previous chunks."""
        if not chunks:
            return ""
        
        # Take last chunk's last portion for overlap
        last_chunk = chunks[-1]
        tokens = self._count_tokens(last_chunk)
        
        if tokens <= self.overlap:
            return last_chunk
        
        # Take approximately overlap tokens from end
        words = last_chunk.split()
        overlap_words = words[-self.overlap:]
        return ' '.join(overlap_words)
    
    def _create_chunk(
        self,
        text_parts: List[str],
        doc_id: str,
        chunk_id: int,
        start_char: int,
        end_char: int,
        metadata: Dict
    ) -> Chunk:
        """Create Chunk object."""
        text = '\n\n'.join(text_parts)
        tokens = self._count_tokens(text)
        
        chunk_metadata = {
            **metadata,
            'has_title': self._has_title(text),
            'has_list': self._has_list(text),
            'has_numbers': bool(re.search(r'\d+', text)),
        }
        
        return Chunk(
            text=text,
            doc_id=doc_id,
            chunk_id=chunk_id,
            start_char=start_char,
            end_char=end_char,
            num_tokens=tokens,
            metadata=chunk_metadata
        )
    
    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count.
        
        Simple approximation: ~1.3 words per token for Indonesian
        """
        words = len(text.split())
        return int(words / 1.3)
    
    def _has_title(self, text: str) -> bool:
        """Check if chunk starts with title."""
        lines = text.split('\n')
        if not lines:
            return False
        
        first_line = lines[0].strip()
        
        # Heuristics for titles
        if first_line.isupper() and len(first_line.split()) <= 10:
            return True
        
        if re.match(r'^(BAB|Pasal|Bagian)\s+[IVXLCDM\d]+', first_line):
            return True
        
        return False
    
    def _has_list(self, text: str) -> bool:
        """Check if chunk contains list."""
        return bool(re.search(r'^\s*[\d\-\•]\s+', text, re.MULTILINE))
    
    def calculate_coherence(self, chunk: Chunk) -> float:
        """
        Calculate chunk coherence score (0-1).
        
        Higher score = more semantically coherent
        
        Factors:
        - Complete sentences
        - No abrupt cuts
        - Logical flow
        """
        text = chunk.text
        score = 1.0
        
        # Penalty for starting mid-sentence (lowercase start)
        if text and text[0].islower():
            score -= 0.2
        
        # Penalty for ending mid-sentence (no punctuation)
        if text and text[-1] not in '.!?':
            score -= 0.2
        
        # Bonus for having title
        if chunk.metadata.get('has_title'):
            score += 0.1
        
        # Penalty for very short chunks
        if chunk.num_tokens < self.min_chunk_size:
            score -= 0.3
        
        # Ensure 0-1 range
        return max(0.0, min(1.0, score))
    
    def chunk_batch(
        self,
        documents: List[tuple[str, str, Dict]],
        calculate_coherence: bool = True
    ) -> List[List[Chunk]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of (text, doc_id, metadata) tuples
            calculate_coherence: Calculate coherence scores
        
        Returns:
            List of chunk lists (one per document)
        """
        from tqdm import tqdm
        
        all_chunks = []
        
        for text, doc_id, metadata in tqdm(documents, desc="Chunking documents"):
            chunks = self.chunk(text, doc_id, metadata)
            
            if calculate_coherence:
                for chunk in chunks:
                    chunk.coherence_score = self.calculate_coherence(chunk)
            
            all_chunks.append(chunks)
        
        return all_chunks


# =============================================================================
# TESTING
# =============================================================================

def demo_chunker():
    """Demo document chunking."""
    
    print("🧪 Document Chunker Demo\n")
    
    # Sample Indonesian government document
    sample_doc = """
PERATURAN PRESIDEN REPUBLIK INDONESIA
NOMOR 26 TAHUN 2009

TENTANG PENERAPAN KARTU TANDA PENDUDUK BERBASIS NOMOR INDUK KEPENDUDUKAN SECARA NASIONAL

BAB I
KETENTUAN UMUM

Pasal 1
Dalam Peraturan Presiden ini, yang dimaksud dengan:

1. Kartu Tanda Penduduk, yang selanjutnya disingkat KTP adalah identitas resmi 
   penduduk sebagai bukti diri yang diterbitkan oleh Instansi Pelaksana yang 
   berlaku di seluruh wilayah Negara Kesatuan Republik Indonesia.

2. Nomor Induk Kependudukan, yang selanjutnya disingkat NIK adalah nomor identitas 
   penduduk yang bersifat unik atau khas, tunggal dan melekat pada seseorang yang 
   terdaftar sebagai Penduduk Indonesia.

3. Database Kependudukan adalah kumpulan data yang tersimpan secara sistematis dan 
   dapat diakses melalui sistem aplikasi tertentu.

BAB II
PENERAPAN KTP BERBASIS NIK

Pasal 2
(1) Setiap Penduduk yang telah berumur 17 tahun atau telah kawin atau pernah kawin 
    wajib memiliki KTP.

(2) KTP sebagaimana dimaksud pada ayat (1) berlaku sebagai identitas yang sah untuk 
    mendapatkan pelayanan publik.

(3) KTP berbasis NIK sebagaimana dimaksud pada ayat (1) diterbitkan oleh Pemerintah 
    Kabupaten/Kota.
"""
    
    # Initialize chunker
    chunker = DocumentChunker(
        chunk_size=150,  # Smaller for demo
        overlap=30,
        min_chunk_size=50
    )
    
    # Chunk document
    chunks = chunker.chunk(
        text=sample_doc,
        doc_id="Perpres_26_2009",
        metadata={
            'doc_type': 'Perpres',
            'number': '26',
            'year': '2009',
            'category': 'civil_administration'
        }
    )
    
    print(f"📊 Chunking Results")
    print("="*60)
    print(f"Total Chunks: {len(chunks)}")
    print(f"Avg Tokens/Chunk: {sum(c.num_tokens for c in chunks) / len(chunks):.1f}")
    
    # Calculate coherence
    for chunk in chunks:
        chunk.coherence_score = chunker.calculate_coherence(chunk)
    
    avg_coherence = sum(c.coherence_score for c in chunks) / len(chunks)
    print(f"Avg Coherence: {avg_coherence:.2f}")
    
    print(f"\n📝 Chunks Preview:")
    print("="*60)
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\nChunk {i+1}:")
        print(f"  Tokens: {chunk.num_tokens}")
        print(f"  Coherence: {chunk.coherence_score:.2f}")
        print(f"  Has Title: {chunk.metadata.get('has_title')}")
        print(f"  Has List: {chunk.metadata.get('has_list')}")
        print(f"  Text Preview:")
        print(f"  {chunk.text[:200]}...")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo_chunker()
