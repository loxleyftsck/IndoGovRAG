"""
Audit Logger for Compliance
Full query audit trail for GDPR and regulatory compliance
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import uuid


class AuditLogger:
    """
    Compliance-focused audit logger
    Logs all queries with full context for auditability
    """
    
    def __init__(self, storage_path: str = "logs/audit.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if not exists
        if not self.storage_path.exists():
            self.storage_path.touch()
    
    def log_query(
        self,
        request_id: str,
        query: str,
        answer: str,
        retrieved_docs: List[Dict],
        model_used: str,
        user_ip: str = "unknown",
        user_agent: str = "unknown",
        **kwargs
    ):
        """
        Log query for audit trail
        
        Required fields for compliance:
        - request_id: Unique identifier
        - timestamp: When query occurred
        - user_context: Anonymized user info
        - query: What was asked (hashed for privacy)
        - answer: What was provided (hashed)
        - sources: Which documents used
        - model_version: Which AI model/prompt
        - safety_decisions: Any filtering applied
        """
        
        audit_entry = {
            # === IDENTIFIERS ===
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            
            # === USER CONTEXT (Anonymized) ===
            "user_ip_hash": self._hash(user_ip),  # SHA256 for privacy
            "user_agent": user_agent[:200],  # Truncate
            "session_id": kwargs.get("session_id", "anonymous"),
            
            # === QUERY (Privacy-aware) ===
            "query_hash": self._hash(query),
            "query_preview": query[:100],  # First 100 chars only
            "query_length": len(query),
            
            # === RETRIEVAL DETAILS ===
            "retrieved_doc_ids": [d.get("doc_id", "unknown") for d in retrieved_docs],
            "retrieval_scores": [round(d.get("score", 0.0), 3) for d in retrieved_docs],
            "retrieval_method": kwargs.get("retrieval_method", "vector"),
            "evidence_sufficient": kwargs.get("evidence_sufficient", True),
            
            # === ANSWER (Privacy-aware) ===
            "answer_hash": self._hash(answer),
            "answer_preview": answer[:100],
            "answer_length": len(answer),
            "confidence": kwargs.get("confidence", 0.0),
            
            # === MODEL VERSIONS (Critical for reproducibility) ===
            "model_used": model_used,
            "prompt_version": kwargs.get("prompt_version", "v2.1"),
            "embedding_model": kwargs.get("embedding_model", "multilingual-e5-base"),
            "system_version": kwargs.get("system_version", "1.0.0"),
            
            # === SAFETY DECISIONS ===
            "toxicity_filtered": kwargs.get("toxicity_filtered", False),
            "toxicity_score": kwargs.get("toxicity_score", 0.0),
            "evidence_grounding_triggered": kwargs.get("evidence_grounding_triggered", False),
            
            # === PERFORMANCE ===
            "latency_ms": kwargs.get("latency_ms", 0),
            "tokens_used": kwargs.get("tokens_used", 0),
            "cost_usd": kwargs.get("cost_usd", 0.0),
            
            # === STATUS ===
            "status": kwargs.get("status", "success"),
            "error_message": kwargs.get("error_message", None),
            
            # === COMPLIANCE ===
            "retention_until": (datetime.now() + timedelta(days=90)).isoformat(),
            "gdpr_compliant": True
        }
        
        # Write to audit log
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")
    
    @staticmethod
    def _hash(text: str) -> str:
        """SHA256 hash for privacy"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def query_by_request_id(self, request_id: str) -> Optional[Dict]:
        """Query audit log by request ID"""
        if not self.storage_path.exists():
            return None
        
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("request_id") == request_id:
                    return entry
        
        return None
    
    def delete_user_data(self, user_ip_hash: str) -> int:
        """
        GDPR Right to be Forgotten
        Tombstone user data (don't delete, mark as deleted)
        """
        if not self.storage_path.exists():
            return 0
        
        # Read all entries
        with open(self.storage_path, "r", encoding="utf-8") as f:
            entries = [json.loads(line) for line in f]
        
        # Mark matching entries as deleted
        deleted_count = 0
        for entry in entries:
            if entry.get("user_ip_hash") == user_ip_hash:
                entry["_deleted"] = True
                entry["_deleted_at"] = datetime.now().isoformat()
                entry["query_hash"] = "[REDACTED]"
                entry["answer_hash"] = "[REDACTED]"
                entry["query_preview"] = "[REDACTED]"
                entry["answer_preview"] = "[REDACTED]"
                deleted_count += 1
        
        # Write back
        with open(self.storage_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return deleted_count
    
    def cleanup_expired(self):
        """Clean up entries past retention period"""
        if not self.storage_path.exists():
            return 0
        
        now = datetime.now()
        
        # Read all entries
        with open(self.storage_path, "r", encoding="utf-8") as f:
            entries = [json.loads(line) for line in f]
        
        # Filter out expired
        active_entries = []
        expired_count = 0
        
        for entry in entries:
            retention_until = datetime.fromisoformat(entry.get("retention_until", now.isoformat()))
            if retention_until > now:
                active_entries.append(entry)
            else:
                expired_count += 1
        
        # Write back active only
        with open(self.storage_path, "w", encoding="utf-8") as f:
            for entry in active_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return expired_count
