"""
Reindex All Documents Script

Loads all .txt/.md files from data/documents/, chunks them, embeds,
and stores in ChromaDB.

Usage:
    python scripts/reindex_all.py
"""

import sys
import logging
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Wrap stdout/stderr with UTF-8 BEFORE basicConfig so the handler inherits it
import io as _io
if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, _io.TextIOWrapper):
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, _io.TextIOWrapper):
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("reindex")

from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing
from src.data.chunker import DocumentChunker


def load_documents_from_folder(folder: Path):
    """Load all .txt and .md files from a folder."""
    docs = []
    if not folder.exists():
        logger.warning(f"Documents folder does not exist: {folder}")
        return docs

    files = list(folder.glob("*.txt")) + list(folder.glob("*.md"))
    logger.info(f"Found {len(files)} document files in {folder}")

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8")
            if not text.strip():
                logger.warning(f"Skipping empty file: {file_path.name}")
                continue

            # Derive doc_id from filename (strip extension)
            doc_id = file_path.stem

            # Infer metadata from filename patterns
            metadata = {"source_file": file_path.name}
            name_lower = file_path.stem.lower()

            if "ktp" in name_lower or "nik" in name_lower:
                metadata["category"] = "administrasi_kependudukan"
                metadata["doc_type"] = "Perpres"
            elif "bpjs" in name_lower or "kesehatan" in name_lower:
                metadata["category"] = "kesehatan"
                metadata["doc_type"] = "PP"
            elif "npwp" in name_lower or "pajak" in name_lower or "perpajakan" in name_lower:
                metadata["category"] = "perpajakan"
                metadata["doc_type"] = "UU"
            elif "umkm" in name_lower or "usaha" in name_lower or "ekonomi" in name_lower:
                metadata["category"] = "ekonomi"
                metadata["doc_type"] = "Perpres"
            elif "pendidikan" in name_lower:
                metadata["category"] = "pendidikan"
                metadata["doc_type"] = "UU"
            else:
                metadata["category"] = "umum"
                metadata["doc_type"] = "dokumen"

            docs.append((text, doc_id, metadata))
            logger.info(f"  Loaded: {file_path.name} ({len(text)} chars)")

        except Exception as e:
            logger.error(f"  Failed to load {file_path.name}: {e}")
            continue

    return docs


def main():
    logger.info("=" * 60)
    logger.info("[REINDEX] Starting full document reindex...")
    logger.info("=" * 60)

    # Paths
    docs_folder = BASE_DIR / "data" / "documents"
    chroma_dir = BASE_DIR / "data" / "vector_db" / "chroma"

    # 1. Load documents
    logger.info(f"[STEP 1] Loading documents from: {docs_folder}")
    documents = load_documents_from_folder(docs_folder)

    if not documents:
        logger.warning("[WARN] No documents found to index!")
        logger.info("  Falling back to sample documents...")
        # Use load_sample_docs logic inline
        documents = _get_sample_documents()
        logger.info(f"  Loaded {len(documents)} sample documents as fallback")
    else:
        logger.info(f"[STEP 1] Loaded {len(documents)} documents")

    # 2. Chunk documents
    logger.info("[STEP 2] Chunking documents...")
    chunker = DocumentChunker(
        chunk_size=512,
        overlap=64,
        min_chunk_size=100
    )

    all_chunks = []
    total_docs = len(documents)
    failed_docs = 0

    for i, (text, doc_id, metadata) in enumerate(documents):
        try:
            chunks = chunker.chunk(text, doc_id, metadata)
            # Calculate coherence
            for chunk in chunks:
                chunk.coherence_score = chunker.calculate_coherence(chunk)
            all_chunks.extend(chunks)
            logger.info(f"  Doc {i+1}/{total_docs}: {doc_id} -> {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"  Failed to chunk {doc_id}: {e}")
            failed_docs += 1
            continue

    if not all_chunks:
        logger.error("[ERR] No chunks produced! Aborting indexing.")
        return

    logger.info(f"[STEP 2] Produced {len(all_chunks)} total chunks from {total_docs} docs")

    # 3. Prepare chunks for indexing
    logger.info("[STEP 3] Preparing chunks for ChromaDB...")
    prepared_chunks = prepare_chunks_for_indexing(all_chunks)

    # 4. Clear existing collection and re-index
    logger.info(f"[STEP 4] Connecting to ChromaDB at: {chroma_dir}")
    store = VectorStore(persist_directory=str(chroma_dir))

    initial_count = store.collection.count()
    logger.info(f"  Current chunks in DB: {initial_count}")

    # Delete all existing chunks
    logger.info("  Clearing existing collection...")
    store.delete_all()

    # Add new chunks
    logger.info(f"  Adding {len(prepared_chunks)} chunks...")
    added = store.add_chunks(prepared_chunks, show_progress=True)

    final_count = store.collection.count()
    logger.info(f"  Final chunk count: {final_count}")

    # 5. Summary
    logger.info("=" * 60)
    logger.info("[OK] Reindex complete!")
    logger.info(f"   Documents processed: {total_docs} ({failed_docs} failed)")
    logger.info(f"   Total chunks indexed: {final_count}")
    logger.info(f"   ChromaDB path: {chroma_dir}")
    logger.info("=" * 60)

    # Verify search still works
    logger.info("[VERIFY] Testing vector search...")
    test_results = store.search("KTP elektronik", n_results=2)
    if test_results:
        logger.info(f"  Search OK: got {len(test_results)} results for test query")
    else:
        logger.warning("  Search returned no results")


def _get_sample_documents():
    """Return built-in sample documents as fallback when no files exist."""
    return [
        (
            "Kartu Tanda Penduduk Elektronik (KTP-el) adalah kartu tanda penduduk yang dilengkapi "
            "dengan chip elektronik. Chip ini menyimpan biodata lengkap penduduk termasuk pas foto, "
            "tanda tangan, dan sidik jari. NIK (Nomor Induk Kependudukan) bersifat unik, permanen, "
            "dan berlaku seumur hidup untuk setiap penduduk Indonesia. "
            "Setiap warga negara Indonesia yang telah berumur 17 tahun atau telah menikah wajib memiliki "
            "KTP elektronik. KTP-el berlaku sebagai identitas resmi dan bukti diri yang diterbitkan "
            "oleh Instansi Pelaksana di seluruh wilayah NKRI.",
            "ktp_elektronik_001",
            {"category": "administrasi_kependudukan", "doc_type": "Perpres", "source_file": "sample"}
        ),
        (
            "BPJS Kesehatan menyelenggarakan program Jaminan Kesehatan Nasional untuk seluruh penduduk "
            "Indonesia. Program ini memberikan perlindungan kesehatan agar peserta memperoleh manfaat "
            "pemeliharaan kesehatan dan perlindungan. Terdapat tiga kelas perawatan: Kelas I (biaya "
            "tertinggi), Kelas II (menengah), dan Kelas III (terendah). "
            "Peserta wajib membayar iuran bulanan sesuai dengan kelas perawatan yang dipilih. "
            "Pendaftaran BPJS Kesehatan dapat dilakukan secara online melalui website atau aplikasi "
            "mobile BPJS Kesehatan.",
            "bpjs_kesehatan_001",
            {"category": "kesehatan", "doc_type": "PP", "source_file": "sample"}
        ),
        (
            "Nomor Pokok Wajib Pajak (NPWP) adalah nomor identitas perpajakan untuk setiap wajib pajak. "
            "Mulai tahun 2023, NIK dapat digunakan sebagai NPWP untuk wajib pajak orang pribadi. "
            "NPWP diperlukan untuk berbagai keperluan administrasi seperti pelaporan SPT, "
            "pembukaan rekening bank, dan pengajuan kredit. "
            "Setiap wajib pajak yang memiliki penghasilan wajib melaporkan SPT Tahunan "
            "paling lambat 31 Maret setiap tahunnya.",
            "npwp_identitas_001",
            {"category": "perpajakan", "doc_type": "UU", "source_file": "sample"}
        ),
        (
            "Usaha Mikro Kecil dan Menengah (UMKM) dengan omzet di bawah Rp 4,8 miliar per tahun "
            "mendapat fasilitas pajak khusus. Tarif PPh final untuk UMKM adalah 0,5% dari omzet bruto. "
            "UMKM yang baru beroperasi dapat memanfaatkan insentif pajak dan kemudahan perizinan "
            "melalui sistem Online Single Submission (OSS). "
            "Pemerintah juga menyediakan program kredit usaha rakyat (KUR) untuk mendukung "
            "pengembangan UMKM di Indonesia.",
            "umkm_001",
            {"category": "ekonomi", "doc_type": "Perpres", "source_file": "sample"}
        ),
        (
            "Sistem pendidikan di Indonesia terdiri dari pendidikan formal, nonformal, dan informal. "
            "Pendidikan formal meliputi jenjang SD, SMP, SMA/SMK, dan Perguruan Tinggi. "
            "Pemerintah menyediakan program Kartu Indonesia Pintar (KIP) untuk membantu biaya pendidikan "
            "siswa dari keluarga kurang mampu. Selain itu, tersedia berbagai beasiswa seperti LPDP "
            "untuk pendidikan S2 dan S3 baik dalam maupun luar negeri.",
            "pendidikan_001",
            {"category": "pendidikan", "doc_type": "UU", "source_file": "sample"}
        ),
    ]


if __name__ == "__main__":
    main()
