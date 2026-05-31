"""
Unit Tests for API Endpoints (api/main.py)
Covers: root, health, query, upload, files, stats, analytics
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Import app via the module path to ensure lifespan runs once
from api.main import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient with app lifespan triggered."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ─── Root & Health ─────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_service_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
        assert "endpoints" in data

    def test_health_check_returns_status(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "rag_initialized" in data


# ─── Query Endpoint ─────────────────────────────────────────────────────────────

class TestQueryEndpoint:
    def test_query_endpoint_success_with_mock(self, client):
        """Valid query returns 200 with answer, sources, confidence."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_result = {
                "answer": "KTP diterbitkan oleh Kabupaten/Kota.",
                "retrieved_chunks": [
                    {"text": "KTP diterbitkan...", "metadata": {"doc_id": "Perpres_26_2009"}}
                ],
                "sources": [{"doc_id": "Perpres_26_2009", "doc_type": "Perpres", "year": "2009"}],
                "confidence": 0.88,
                "model_used": "gemini-2.0-flash",
                "tokens_used": 120,
            }
            mock_rag.query.return_value = mock_result
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post("/query", json={"query": "Apa itu KTP?"})

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "confidence" in data
        assert "latency_ms" in data
        assert "metadata" in data

    def test_query_endpoint_validation_empty_query(self, client):
        """Empty query string is rejected with 422."""
        response = client.post("/query", json={"query": ""})
        assert response.status_code == 422

    def test_query_endpoint_validation_missing_query(self, client):
        """Missing query field is rejected with 422."""
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_query_endpoint_query_too_long(self, client):
        """Query exceeding max_length is rejected with 422."""
        long_query = "a" * 501  # max_length is 500
        response = client.post("/query", json={"query": long_query})
        assert response.status_code == 422

    def test_query_endpoint_with_cache_hit(self, client):
        """Cache-hit query returns cached response without calling LLM."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = MagicMock()
            mock_rag.query_cache.get.return_value = {
                "answer": "Jawaban dari cache",
                "sources": ["Perpres_26_2009"],
                "confidence": 0.85,
                "retrieved_chunks": [],
            }

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post("/query", json={"query": "Apa itu KTP?"})

        assert response.status_code == 200
        data = response.json()
        assert "[Cached]" in data["answer"]

    def test_query_endpoint_reranking_option(self, client):
        """Query with reranking option is passed to pipeline config."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None
            mock_rag.query.return_value = {
                "answer": "Jawaban.",
                "retrieved_chunks": [],
                "sources": [],
                "confidence": 0.8,
                "model_used": "gemini-2.0-flash",
                "tokens_used": 50,
            }

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post(
                    "/query",
                    json={
                        "query": "Syarat pembuatanSIM?",
                        "options": {"use_reranking": True, "top_k": 3},
                    },
                )

        assert response.status_code == 200
        # verify reranking was requested
        mock_rag.configure.assert_called_once()
        call_args = mock_rag.configure.call_args[0][0]
        assert call_args.get("use_reranking") is True
        assert call_args.get("top_k") == 3

    def test_query_endpoint_hybrid_option(self, client):
        """Query with hybrid search option."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None
            mock_rag.query.return_value = {
                "answer": "Jawaban hybrid.",
                "retrieved_chunks": [],
                "sources": [],
                "confidence": 0.9,
                "model_used": "gemini-2.0-flash",
                "tokens_used": 60,
            }

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post(
                    "/query",
                    json={"query": "BPJS Kesehatan", "options": {"use_hybrid": True}},
                )

        assert response.status_code == 200

    def test_query_endpoint_init_failure_fallback(self, client):
        """RAG init failure returns graceful fallback, not 500."""
        with patch("api.main.rag_pipeline", None):
            with patch("api.main.RAGPipeline", side_effect=RuntimeError("DB not found")):
                response = client.post("/query", json={"query": "Apa itu KTP?"})

        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == 0.0
        assert "metadata" in data

    def test_query_endpoint_retrieval_error_bm25_fallback(self, client):
        """Retrieval error triggers BM25 fallback."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None
            mock_rag.query.side_effect = RuntimeError("Retrieval failed")
            mock_rag.vector_store = MagicMock()

            # Mock hybrid_search returning valid chunks
            mock_chunk = MagicMock()
            mock_chunk.text = "Dokumen terkait..."
            mock_rag.vector_store.hybrid_search.return_value = [mock_chunk]

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post("/query", json={"query": "Apa itu KTP?"})

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["status"] == "bm25_fallback"

    def test_query_endpoint_error_schema_response(self, client):
        """Retrieval error with no BM25 returns error schema response."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None
            mock_rag.query.side_effect = RuntimeError("Retrieval failed")
            mock_rag.vector_store = None  # No fallback possible

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post("/query", json={"query": "Apa itu KTP?"})

        assert response.status_code == 200
        data = response.json()
        assert "error_code" in data["metadata"]

    def test_query_endpoint_with_user_header(self, client):
        """User ID header is accepted and passed to analytics."""
        with patch("api.main.rag_pipeline") as mock_rag:
            mock_rag.configure = MagicMock()
            mock_rag.query_cache = None
            mock_rag.query.return_value = {
                "answer": "Jawaban.",
                "retrieved_chunks": [],
                "sources": [],
                "confidence": 0.8,
                "model_used": "gemini-2.0-flash",
                "tokens_used": 50,
            }

            with patch("src.utils.topic_classifier.classify_query") as mock_topic:
                mock_topic.return_value = MagicMock(
                    primary_topic=MagicMock(value="umum"),
                    is_high_stakes=False,
                )
                response = client.post(
                    "/query",
                    json={"query": "Test query"},
                    headers={"X-User-ID": "user_123"},
                )

        assert response.status_code == 200


# ─── Metrics & Stats ────────────────────────────────────────────────────────────

class TestMetricsAndStats:
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "avg_latency_ms" in data
        assert "success_rate" in data

    def test_stats_endpoint_returns_chunks_info(self, client):
        """Vector stats returns chunk counts and categories."""
        with patch("api.main.VectorStore") as mock_vs_class:
            mock_store = MagicMock()
            mock_store.collection.count.return_value = 42
            mock_store.collection.get.return_value = {
                "metadatas": [
                    {"file_id": "f1", "doc_type": "Perpres", "category": "civil"},
                    {"file_id": "f1", "doc_type": "Perpres", "category": "civil"},
                ]
            }
            mock_store.collection.name = "indonesian_gov_docs"
            mock_vs_class.return_value = mock_store

            response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_chunks" in data
        assert "unique_files" in data

    def test_stats_endpoint_handles_error(self, client):
        """Stats endpoint returns error dict on exception."""
        with patch("api.main.VectorStore", side_effect=Exception("DB error")):
            response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data


# ─── Analytics ─────────────────────────────────────────────────────────────────

class TestAnalytics:
    def test_analytics_summary_empty_log(self, client):
        with patch("api.main._get_log_path") as mock_path:
            mock_path.return_value = Path("nonexistent_log.jsonl")
            response = client.get("/api/analytics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 0
        assert data["avg_confidence"] == 0.0

    def test_analytics_summary_with_events(self, client):
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                '{"query":"test","user_id":"u1","results_count":5,'
                '"confidence_score":0.9,"response_time_ms":150.0,"had_answer":true,"timestamp":"2026-01-01T00:00:00Z"}\n'
            )
            f.write(
                '{"query":"test","user_id":"u2","results_count":3,'
                '"confidence_score":0.7,"response_time_ms":200.0,"had_answer":true,"timestamp":"2026-01-01T00:01:00Z"}\n'
            )
            tmp_path = f.name

        try:
            with patch("api.main._get_log_path", return_value=Path(tmp_path)):
                response = client.get("/api/analytics/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total_queries"] == 2
            assert data["unique_users"] == 2
            assert data["avg_confidence"] > 0
            assert data["p50_ms"] > 0
        finally:
            Path(tmp_path).unlink()


# ─── Upload Endpoints ──────────────────────────────────────────────────────────

class TestUploadEndpoints:
    def test_upload_file_unsupported_type(self, client):
        """Unsupported file extension returns failure response."""
        from io import BytesIO

        response = client.post(
            "/upload/file",
            files={"file": ("test.exe", BytesIO(b"binary"), "application/octet-stream")},
            data={"category": "test"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Unsupported" in data["message"]

    def test_upload_file_success(self, client):
        """Valid text file upload returns success."""
        from io import BytesIO

        with patch("api.main.BackgroundTasks"):
            response = client.post(
                "/upload/file",
                files={"file": ("doc.txt", BytesIO(b"Contoh dokumen"), "text/plain")},
                data={"category": "test_cat"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "doc.txt"
        assert data["file_type"] == ".txt"

    def test_upload_folder_empty(self, client):
        """Empty file list in folder upload is handled."""
        from io import BytesIO

        response = client.post(
            "/upload/folder",
            files=[],
            data={"category": "general"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 0

    def test_upload_folder_partial_success(self, client):
        """Mixed valid/invalid files are reported correctly."""
        from io import BytesIO

        with patch("api.main.BackgroundTasks"):
            response = client.post(
                "/upload/folder",
                files=[
                    ("files", ("good.txt", BytesIO(b"isi"), "text/plain")),
                    ("files", ("bad.exe", BytesIO(b"bin"), "application/octet-stream")),
                ],
                data={"category": "general"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 2

    def test_list_files_endpoint(self, client):
        """GET /files returns file list."""
        with patch("api.main.VectorStore") as mock_vs_class:
            mock_store = MagicMock()
            mock_store.collection.get.return_value = {"metadatas": []}
            mock_vs_class.return_value = mock_store

            response = client.get("/files")

        assert response.status_code == 200
        data = response.json()
        assert "total_files" in data
        assert "files" in data

    def test_clear_all_files(self, client):
        """DELETE /files/clear removes all uploads."""
        with patch("api.main.VectorStore") as mock_vs_class:
            mock_store = MagicMock()
            mock_store.collection.count.return_value = 5
            mock_store.collection.get.return_value = {"ids": ["c1", "c2"]}
            mock_vs_class.return_value = mock_store

            response = client.delete("/files/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_uploaded_file_not_found(self, client):
        """Deleting unknown file returns not_found."""
        with patch("api.main.UPLOAD_DIR", Path("/tmp/fake")):
            response = client.delete("/upload/delete/unknown_id_999999")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_upload_status_not_found(self, client):
        """Status of unknown file returns not_found."""
        with patch("api.main.UPLOAD_DIR", Path("/tmp/fake")):
            response = client.get("/upload/status/unknown_id_999999")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"