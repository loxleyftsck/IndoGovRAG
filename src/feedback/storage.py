"""
Feedback API Models and Storage
Collects user feedback for continuous improvement
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
import json
import uuid
from pathlib import Path


class FeedbackType(str, Enum):
    """Types of feedback users can provide"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    REPORT = "report"
    RATING = "rating"
    COMMENT = "comment"


class FeedbackRequest(BaseModel):
    """User feedback request"""
    request_id: str = Field(..., description="Request ID from query response")
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    feedback_type: FeedbackType
    comment: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "rating": 5,
                "feedback_type": "thumbs_up",
                "comment": "Perfect answer!"
            }
        }


class FeedbackResponse(BaseModel):
    """Feedback submission response"""
    feedback_id: str
    status: str
    message: str
    timestamp: str


class FeedbackStorage:
    """
    Stores feedback to JSONL file
    In production, use proper database
    """
    
    def __init__(self, storage_path: str = "data/feedback.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if not exists
        if not self.storage_path.exists():
            self.storage_path.touch()
    
    def save(
        self,
        request_id: str,
        rating: int,
        feedback_type: str,
        comment: Optional[str] = None,
        user_session: str = "anonymous",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Save feedback entry
        
        Returns:
            feedback_id: UUID of feedback entry
        """
        feedback_id = str(uuid.uuid4())
        
        entry = {
            "feedback_id": feedback_id,
            "request_id": request_id,
            "rating": rating,
            "feedback_type": feedback_type,
            "comment": comment,
            "user_session": user_session,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Append to file
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return feedback_id
    
    def get_recent(self, limit: int = 100):
        """Get recent feedback entries"""
        if not self.storage_path.exists():
            return []
        
        with open(self.storage_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Return last N entries
        return [json.loads(line) for line in lines[-limit:]]
    
    def get_low_rated(self, threshold: int = 2, limit: int = 50):
        """Get low-rated queries for improvement"""
        entries = self.get_recent(limit=1000)  # Check last 1000
        low_rated = [e for e in entries if e.get('rating', 5) <= threshold]
        return low_rated[:limit]
    
    def get_stats(self):
        """Get feedback statistics"""
        entries = self.get_recent(limit=1000)
        
        if not entries:
            return {
                "total": 0,
                "avg_rating": 0.0,
                "thumbs_up": 0,
                "thumbs_down": 0,
                "reports": 0
            }
        
        ratings = [e.get('rating', 0) for e in entries]
        types = [e.get('feedback_type') for e in entries]
        
        return {
            "total": len(entries),
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "thumbs_up": types.count("thumbs_up"),
            "thumbs_down": types.count("thumbs_down"),
            "reports": types.count("report")
        }
