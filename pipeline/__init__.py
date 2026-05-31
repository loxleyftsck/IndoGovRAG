"""
IndoGovRAG Pipeline Module

Document processing pipeline components:
  - Chunker: PDF download + text extraction + chunking
  - Embedder: Vector embeddings + BM25 index
  - Scheduler: Cron-based pipeline orchestration
"""

from .chunker import PipelineChunker

__all__ = ['PipelineChunker']
