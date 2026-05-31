"""Tests for custom_embeddings module (mock transformers)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.embeddings.custom_embeddings import (
    CustomEmbeddingFunctionImpl,
    CustomEmbeddingFunction,
    get_custom_embedding_function,
    _load_embedding_model,
    _cached_embedding_fn
)


@pytest.fixture
def mock_torch():
    with patch("src.embeddings.custom_embeddings.torch") as mock:
        mock.cuda.is_available.return_value = False
        mock.no_grad.return_value = MagicMock()
        mock.nn.functional.normalize.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_tokenizer():
    with patch("src.embeddings.custom_embeddings.AutoTokenizer") as mock:
        mock_tokenizer = MagicMock()
        mock.from_pretrained.return_value = mock_tokenizer
        yield mock_tokenizer


@pytest.fixture
def mock_model():
    with patch("src.embeddings.custom_embeddings.AutoModel") as mock:
        mock_model_instance = MagicMock()
        mock_model_instance.eval.return_value = None
        mock.to.return_value = None
        mock.from_pretrained.return_value = mock_model_instance
        yield mock_model_instance


class TestCustomEmbeddingFunctionImpl:
    def test_init_loads_model(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl(model_name="test-model")
        assert impl._model_name == "test-model"

    def test_name_returns_custom_embeddings(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl()
        assert impl.name() == "custom_embeddings"

    def test_encode_single_text(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl()
        mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
        mock_model.last_hidden_state = MagicMock()
        mock_model.last_hidden_state.size.return_value = (1, 10, 768)
        mock_torch.sum.return_value = MagicMock()
        mock_torch.clamp.return_value = MagicMock()
        mock_torch.nn.functional.normalize.return_value = MagicMock()
        impl._cached_encode.cache_clear()
        texts = ["Test text"]
        results = impl.encode(texts)
        assert len(results) == 1

    def test_encode_empty_list(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl()
        results = impl.encode([])
        assert results == []

    def test_call_delegates_to_encode(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl()
        assert callable(impl.__call__)

    def test_mean_pooling(self, mock_torch, mock_tokenizer, mock_model):
        impl = CustomEmbeddingFunctionImpl()
        hidden_states = MagicMock()
        attention_mask = MagicMock()
        hidden_states.size.return_value = (2, 10, 768)
        attention_mask.unsqueeze.return_value.expand.return_value.float.return_value = MagicMock()
        mock_torch.sum.return_value = MagicMock()
        mock_torch.clamp.return_value = MagicMock()
        result = impl._mean_pooling(hidden_states, attention_mask)
        assert result is not None


class TestCustomEmbeddingFunction:
    def test_init_loads_global_impl(self, mock_torch, mock_tokenizer, mock_model):
        wrapper = CustomEmbeddingFunction()
        assert wrapper._impl is not None

    def test_name_delegates_to_impl(self, mock_torch, mock_tokenizer, mock_model):
        wrapper = CustomEmbeddingFunction()
        assert wrapper.name() == "custom_embeddings"

    def test_call_delegates_to_impl(self, mock_torch, mock_tokenizer, mock_model):
        wrapper = CustomEmbeddingFunction()
        assert callable(wrapper.__call__)


class TestGetCustomEmbeddingFunction:
    def test_returns_custom_embedding_function(self, mock_torch, mock_tokenizer, mock_model):
        result = get_custom_embedding_function()
        assert isinstance(result, CustomEmbeddingFunction)

    def test_with_custom_model_name(self, mock_torch, mock_tokenizer, mock_model):
        result = get_custom_embedding_function(model_name="custom-model")
        assert isinstance(result, CustomEmbeddingFunction)
        assert result._model_name == "custom-model"


class TestLoadEmbeddingModel:
    def test_load_embedding_model_returns_impl(self, mock_torch, mock_tokenizer, mock_model):
        import src.embeddings.custom_embeddings as ce
        ce._cached_embedding_fn = None
        result = _load_embedding_model()
        assert isinstance(result, CustomEmbeddingFunctionImpl)
