"""
Unit Tests for Vector Store
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from src.retrieval.vector_search import VectorStore, SearchResult


def clear_vector_store_caches():
    """Clear VectorStore class-level caches between tests."""
    VectorStore._search_cache.clear()
    VectorStore._search_cache_meta.clear()


@pytest.fixture(autouse=True)
def clear_caches():
    """Auto-run cache clear before each test."""
    clear_vector_store_caches()
    yield
    clear_vector_store_caches()

@pytest.fixture
def mock_chroma():
    mock_pc = MagicMock()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.name = "indonesian_gov_docs"
    mock_collection.count.return_value = 0
    mock_collection.get.return_value = {
        "ids": [], "documents": [], "metadatas": [], "distances": [],
    }
    mock_client.list_collections.return_value = []
    mock_client.get_collection.return_value = mock_collection
    mock_client.create_collection.return_value = mock_collection
    mock_emb_fn = MagicMock()
    mock_emb_fn.return_value = [np.random.rand(768).tolist()]
    mock_pc.return_value = mock_client
    with patch("src.retrieval.vector_search.chromadb.PersistentClient", mock_pc), patch("src.retrieval.vector_search.Settings", MagicMock()), patch("src.embeddings.custom_embeddings.CustomEmbeddingFunction", mock_emb_fn):
        yield {
            "pc": mock_pc,
            "client": mock_client,
            "collection": mock_collection,
            "emb_fn": mock_emb_fn,
        }

class TestVectorStoreInit:
    def test_init_creates_persist_directory(self, mock_chroma):
        clear_vector_store_caches()
        store = VectorStore(persist_directory="data/test_db")
        mock_chroma["pc"].assert_called_once()

    def test_init_loads_existing_collection(self, mock_chroma):
        clear_vector_store_caches()
        # Override: pretend collection already exists
        mock_chroma["client"].list_collections.return_value = [mock_chroma["collection"]]
        store = VectorStore()
        mock_chroma["client"].get_collection.assert_called_once_with(name="indonesian_gov_docs")

    def test_init_creates_new_collection_when_missing(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["client"].list_collections.return_value = []
        store = VectorStore()
        mock_chroma["client"].create_collection.assert_called_once()

class TestAddChunks:
    def test_add_chunks_returns_count(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["client"].list_collections.return_value = []
        store = VectorStore()
        with patch("tqdm.tqdm", MagicMock()):
            chunks = [
                {"id": "c1", "text": "Dokumen pertama", "metadata": {"doc_type": "Perpres"}},
                {"id": "c2", "text": "Dokumen kedua", "metadata": {"doc_type": "PP"}},
            ]
            count = store.add_chunks(chunks, show_progress=False)
        assert count == 2
        mock_chroma["collection"].add.assert_called()

    def test_add_chunks_batch_size(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["client"].list_collections.return_value = []
        store = VectorStore()
        with patch("tqdm.tqdm", MagicMock()):
            chunks = [
                {"id": f"c{i}", "text": f"Chunk {i}", "metadata": {"doc_type": "Perpres"}}
                for i in range(5)
            ]
            store.add_chunks(chunks, batch_size=2, show_progress=False)
        assert mock_chroma["collection"].add.call_count == 3

class TestSearch:
    def test_search_returns_list_of_search_results(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [["chunk_1", "chunk_2"]],
            "documents": [["Teks pertama", "Teks kedua"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"doc_type": "Perpres"}, {"doc_type": "PP"}]],
        }
        store = VectorStore()
        results = store.search("test query", n_results=2)
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score == pytest.approx(0.9)

    def test_search_empty_results(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [[]], "documents": [[]], "distances": [[]], "metadatas": [[]],
        }
        store = VectorStore()
        results = store.search("test", n_results=5)
        assert results == []

    def test_search_with_metadata_filter(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [["chunk_1"]], "documents": [["Teks"]], "distances": [[0.2]],
            "metadatas": [[{"doc_type": "Perpres"}]],
        }
        store = VectorStore()
        store.search("test", filter_metadata={"doc_type": "Perpres"})
        mock_chroma["collection"].query.assert_called_once()
        call_kwargs = mock_chroma["collection"].query.call_args[1]
        assert call_kwargs["where"] == {"doc_type": "Perpres"}

    def test_search_with_query_expansion(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [["chunk_1"]], "documents": [["Teks"]], "distances": [[0.1]],
            "metadatas": [[{"doc_type": "Perpres"}]],
        }
        store = VectorStore()
        with patch("src.retrieval.vector_search.QueryExpander", create=True) as mock_exp_cls:
            mock_exp = MagicMock()
            mock_exp.expanded = "expanded query"
            mock_exp_cls.return_value = mock_exp
            store.search("test", use_query_expansion=True)
        mock_exp_cls.assert_called_once()

class TestHybridSearch:
    def _setup_hybrid(self, mock_chroma, semantic_hits=2):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [[f"chunk_{i}" for i in range(semantic_hits)]],
            "documents": [[f"Dokumen {i}" for i in range(semantic_hits)]],
            "distances": [[0.1] * semantic_hits],
            "metadatas": [[{"doc_type": "Perpres"}] * semantic_hits],
        }
        mock_chroma["collection"].get.return_value = {
            "documents": ["Dokumen 1", "Dokumen 2"],
            "ids": ["chunk_1", "chunk_2"],
            "metadatas": [{"doc_type": "Perpres"}, {"doc_type": "PP"}],
        }
        store = VectorStore()
        return store

    def test_hybrid_search_alpha_0_bm25_only(self, mock_chroma):
        store = self._setup_hybrid(mock_chroma)
        with patch("src.retrieval.vector_search.BM25Search", create=True) as mock_bm25_cls:
            mock_bm25 = MagicMock()
            mock_bm25.search.return_value = [
                MagicMock(doc_id="chunk_1", score=0.8),
                MagicMock(doc_id="chunk_2", score=0.5),
            ]
            mock_bm25_cls.return_value = mock_bm25
            results = store.hybrid_search("test query", alpha=0.0)
        assert len(results) > 0
        for r in results:
            assert 0 <= r.score <= 1

    def test_hybrid_search_alpha_1_semantic_only(self, mock_chroma):
        store = self._setup_hybrid(mock_chroma)
        results = store.hybrid_search("test query", alpha=1.0)
        assert len(results) > 0

    def test_hybrid_search_alpha_0_5_fuses_scores(self, mock_chroma):
        store = self._setup_hybrid(mock_chroma)
        with patch("src.retrieval.vector_search.BM25Search", create=True) as mock_bm25_cls:
            mock_bm25 = MagicMock()
            mock_bm25.search.return_value = [
                MagicMock(doc_id="chunk_1", score=0.9),
                MagicMock(doc_id="chunk_2", score=0.4),
            ]
            mock_bm25_cls.return_value = mock_bm25
            results = store.hybrid_search("test", alpha=0.5, n_results=2)
        assert len(results) == 2
        assert results[0].score >= results[1].score

    def test_hybrid_search_empty_when_no_semantic(self, mock_chroma):
        clear_vector_store_caches()
        mock_chroma["collection"].query.return_value = {
            "ids": [[]], "documents": [[]], "distances": [[]], "metadatas": [[]],
        }
        store = VectorStore()
        results = store.hybrid_search("test", n_results=5)
        assert results == []

    def test_hybrid_search_calls_bm25_when_alpha_lt_1(self, mock_chroma):
        store = self._setup_hybrid(mock_chroma)
        with patch("src.retrieval.vector_search.BM25Search", create=True) as mock_bm25_cls:
            mock_bm25_cls.return_value = MagicMock(
                search=MagicMock(return_value=[MagicMock(doc_id="c1", score=0.7)])
            )
            store.hybrid_search("query test", alpha=0.5)
        mock_bm25_cls.assert_called_once()

class TestSearchResult:
    def test_search_result_fields(self):
        result = SearchResult(
            chunk_id="c1", text="Teks dokumen", score=0.95,
            metadata={"doc_type": "Perpres"}
        )
        assert result.chunk_id == "c1"
        assert result.text == "Teks dokumen"
        assert result.score == 0.95
        assert result.metadata["doc_type"] == "Perpres"

    def test_search_result_score_bounds(self):
        result = SearchResult(chunk_id="c1", text="text", score=0.0, metadata={})
        assert result.score == 0.0
        result2 = SearchResult(chunk_id="c2", text="text", score=1.0, metadata={})
        assert result2.score == 1.0

class TestDeleteAndReset:
    def test_delete_all_clears_collection(self, mock_chroma):
        clear_vector_store_caches()
        # Setup: put some data in the collection
        mock_chroma["collection"].count.return_value = 1
        mock_chroma["collection"].get.return_value = {
            "ids": [["chunk_1"]],
            "documents": [["Teks"]],
            "metadatas": [[{"doc_type": "Perpres"}]],
 "embeddings": [[0.1] * 768]
        }
        store = VectorStore()
        store.delete_all()
        mock_chroma["collection"].delete.assert_called_once()