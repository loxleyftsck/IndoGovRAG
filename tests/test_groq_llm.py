"""Tests for GroqLLM class (mock groq client)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm.groq_llm import GroqLLM, GroqModel, GroqResponse

@pytest.fixture
def mock_groq():
    mock_groq_module = MagicMock()
    mock_client = Mock()
    mock_groq_module.Groq.return_value = mock_client
    return mock_groq_module, mock_client

class TestGroqResponse:
    def test_successful_response(self):
        response = GroqResponse(success=True, text="Test", model_used="llama", tokens_used=100, latency_ms=500.0, finish_reason="stop")
        assert response.success is True
    def test_failed_response(self):
        response = GroqResponse(success=False, text="", model_used="llama", tokens_used=0, latency_ms=0, error="Rate limit", fallback_triggered=True)
        assert response.success is False
        assert response.fallback_triggered is True

class TestGroqModel:
    def test_model_values(self):
        assert GroqModel.LLAMA_3_3_70B.value == "llama-3.3-70b-versatile"
        assert GroqModel.MIXTRAL_8X7B.value == "mixtral-8x7b-32768"
        assert GroqModel.GEMMA2_9B.value == "gemma2-9b-it"
        assert GroqModel.LLAMA_3_1_8B.value == "llama-3.1-8b-instant"
    def test_model_is_string(self):
        assert isinstance(GroqModel.LLAMA_3_3_70B, str)
class TestGroqLLM:
    def test_init_with_api_key(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test-key")
                assert llm.api_key == "test-key"
                assert llm.primary_model == GroqModel.LLAMA_3_3_70B
    @patch("os.getenv", return_value=None)
    def test_init_without_api_key(self, mock_getenv):
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            GroqLLM(api_key=None)
    def test_stats_initialization(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                assert llm.stats["total_requests"] == 0
                assert llm.stats["primary_success"] == 0
    def test_make_request_success(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock(content="Test response")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock(prompt_tokens=50, completion_tokens=50, total_tokens=100)
        mock_client.chat.completions.create.return_value = mock_response
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm._make_request("prompt", "llama-3.3-70b-versatile")
                assert response.success is True
                assert response.text == "Test response"
    def test_make_request_rate_limit_error(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm._make_request("prompt", "llama")
                assert response.success is False
                assert response.fallback_triggered is True
    def test_make_request_other_error(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_client.chat.completions.create.side_effect = Exception("Invalid request")
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm._make_request("prompt", "llama")
                assert response.success is False
                assert response.fallback_triggered is False
    def test_generate_success_primary(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock(content="Success")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm.generate("prompt")
                assert response.success is True
                assert llm.stats["primary_success"] == 1
    def test_generate_fallback_on_rate_limit(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock(content="Fallback")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.side_effect = [Exception("Rate limit"), mock_response]
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm.generate("prompt")
                assert response.success is True
                assert response.model_used == "mixtral-8x7b-32768"
    def test_generate_all_fail(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_client.chat.completions.create.side_effect = Exception("error")
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                response = llm.generate("prompt")
                assert response.success is False
                assert response.error is not None
    def test_get_stats(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                llm.stats["total_requests"] = 10
                llm.stats["primary_success"] = 7
                llm.stats["fallback_1_success"] = 2
                llm.stats["total_tokens"] = 1000
                stats = llm.get_stats()
                assert stats["success_rate"] == 0.9
                assert stats["fallback_rate"] == 0.2
    def test_quota_tracker_called(self, mock_groq):
        mock_groq_module, mock_client = mock_groq
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock(content="Test")
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response
        with patch.dict("sys.modules", {"groq": mock_groq_module}):
            with patch("groq.Groq", mock_groq_module.Groq):
                llm = GroqLLM(api_key="test")
                mock_tracker = Mock()
                llm.quota_tracker = mock_tracker
                llm.generate("prompt")
                mock_tracker.track_request.assert_called_once()
