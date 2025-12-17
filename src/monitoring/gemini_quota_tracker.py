"""
Gemini Pro Quota Tracker - 100% FREE Edition
Track token usage, daily limits, and get alerts WITHOUT any paid services.
Uses local JSON file for persistence.

Gemini Pro Free Tier Limits (as of Dec 2024):
- 15 requests per minute (RPM)
- 1 million tokens per minute (TPM)
- 1,500 requests per day (RPD)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import time


class GeminiQuotaTracker:
    """Local file-based quota tracking for Gemini API."""
    
    # Free tier limits
    FREE_TIER_LIMITS = {
        "rpm": 15,  # requests per minute
        "tpm": 1_000_000,  # tokens per minute
        "rpd": 1_500,  # requests per day
    }
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        "warning": 0.8,  # 80%
        "critical": 0.95,  # 95%
    }
    
    def __init__(self, storage_path: str = "data/quota_tracking.json"):
        """Initialize tracker with local JSON storage."""
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.data = self._load_data()
        self._reset_if_new_day()
    
    def _load_data(self) -> Dict:
        """Load tracking data from JSON file."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        else:
            return self._create_new_data()
    
    def _save_data(self):
        """Save tracking data to JSON file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _create_new_data(self) -> Dict:
        """Create fresh tracking data structure."""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "daily_requests": 0,
            "daily_tokens": 0,
            "minute_buckets": {},  # {timestamp: {requests: X, tokens: Y}}
            "history": [],  # Recent API calls
        }
    
    def _reset_if_new_day(self):
        """Reset daily counters if it's a new day."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if self.data["date"] != current_date:
            # Archive old data to history
            old_summary = {
                "date": self.data["date"],
                "requests": self.data["daily_requests"],
                "tokens": self.data["daily_tokens"],
            }
            
            # Create new day
            self.data = self._create_new_data()
            print(f"📅 New day started! Previous day: {old_summary}")
            self._save_data()
    
    def _get_current_minute_bucket(self) -> str:
        """Get current minute bucket key (YYYY-MM-DD HH:MM)."""
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _clean_old_minute_buckets(self):
        """Remove minute buckets older than 1 minute."""
        now = datetime.now()
        cutoff = (now - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
        
        # Remove old buckets
        old_buckets = [k for k in self.data["minute_buckets"].keys() if k < cutoff]
        for bucket in old_buckets:
            del self.data["minute_buckets"][bucket]
    
    def _get_minute_stats(self) -> Dict:
        """Get current minute statistics."""
        self._clean_old_minute_buckets()
        
        total_requests = sum(
            bucket["requests"] 
            for bucket in self.data["minute_buckets"].values()
        )
        total_tokens = sum(
            bucket["tokens"] 
            for bucket in self.data["minute_buckets"].values()
        )
        
        return {
            "requests": total_requests,
            "tokens": total_tokens,
        }
    
    def track_request(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        model: str = "gemini-pro",
        query_preview: Optional[str] = None
    ) -> Dict:
        """
        Track an API request.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (default: gemini-pro)
            query_preview: First 50 chars of query (for logging)
        
        Returns:
            Dict with tracking info and alerts
        """
        total_tokens = input_tokens + output_tokens
        current_minute = self._get_current_minute_bucket()
        
        # Update minute bucket
        if current_minute not in self.data["minute_buckets"]:
            self.data["minute_buckets"][current_minute] = {
                "requests": 0,
                "tokens": 0,
            }
        
        self.data["minute_buckets"][current_minute]["requests"] += 1
        self.data["minute_buckets"][current_minute]["tokens"] += total_tokens
        
        # Update daily counters
        self.data["daily_requests"] += 1
        self.data["daily_tokens"] += total_tokens
        
        # Add to history (keep last 100)
        self.data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "query_preview": query_preview[:50] if query_preview else None,
        })
        self.data["history"] = self.data["history"][-100:]  # Keep last 100
        
        # Save to disk
        self._save_data()
        
        # Get current stats
        minute_stats = self._get_minute_stats()
        
        # Check for alerts
        alerts = self._check_alerts(minute_stats)
        
        return {
            "success": True,
            "daily": {
                "requests": self.data["daily_requests"],
                "requests_limit": self.FREE_TIER_LIMITS["rpd"],
                "requests_remaining": self.FREE_TIER_LIMITS["rpd"] - self.data["daily_requests"],
                "tokens": self.data["daily_tokens"],
            },
            "minute": {
                "requests": minute_stats["requests"],
                "requests_limit": self.FREE_TIER_LIMITS["rpm"],
                "tokens": minute_stats["tokens"],
                "tokens_limit": self.FREE_TIER_LIMITS["tpm"],
            },
            "this_request": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
            "alerts": alerts,
        }
    
    def _check_alerts(self, minute_stats: Dict) -> list:
        """Check if any quota thresholds are exceeded."""
        alerts = []
        
        # Daily requests
        daily_usage = self.data["daily_requests"] / self.FREE_TIER_LIMITS["rpd"]
        if daily_usage >= self.ALERT_THRESHOLDS["critical"]:
            alerts.append({
                "level": "CRITICAL",
                "type": "daily_requests",
                "message": f"🚨 CRITICAL: {self.data['daily_requests']}/{self.FREE_TIER_LIMITS['rpd']} daily requests used ({daily_usage*100:.1f}%)",
            })
        elif daily_usage >= self.ALERT_THRESHOLDS["warning"]:
            alerts.append({
                "level": "WARNING",
                "type": "daily_requests",
                "message": f"⚠️  WARNING: {self.data['daily_requests']}/{self.FREE_TIER_LIMITS['rpd']} daily requests used ({daily_usage*100:.1f}%)",
            })
        
        # Minute requests
        minute_req_usage = minute_stats["requests"] / self.FREE_TIER_LIMITS["rpm"]
        if minute_req_usage >= self.ALERT_THRESHOLDS["critical"]:
            alerts.append({
                "level": "CRITICAL",
                "type": "minute_requests",
                "message": f"🚨 CRITICAL: {minute_stats['requests']}/{self.FREE_TIER_LIMITS['rpm']} requests/min ({minute_req_usage*100:.1f}%)",
            })
        elif minute_req_usage >= self.ALERT_THRESHOLDS["warning"]:
            alerts.append({
                "level": "WARNING",
                "type": "minute_requests",
                "message": f"⚠️  WARNING: {minute_stats['requests']}/{self.FREE_TIER_LIMITS['rpm']} requests/min ({minute_req_usage*100:.1f}%)",
            })
        
        # Minute tokens
        minute_tok_usage = minute_stats["tokens"] / self.FREE_TIER_LIMITS["tpm"]
        if minute_tok_usage >= self.ALERT_THRESHOLDS["critical"]:
            alerts.append({
                "level": "CRITICAL",
                "type": "minute_tokens",
                "message": f"🚨 CRITICAL: {minute_tok_usage['tokens']:,}/{self.FREE_TIER_LIMITS['tpm']:,} tokens/min ({minute_tok_usage*100:.1f}%)",
            })
        elif minute_tok_usage >= self.ALERT_THRESHOLDS["warning"]:
            alerts.append({
                "level": "WARNING",
                "type": "minute_tokens",
                "message": f"⚠️  WARNING: {minute_stats['tokens']:,}/{self.FREE_TIER_LIMITS['tpm']:,} tokens/min ({minute_tok_usage*100:.1f}%)",
            })
        
        return alerts
    
    def get_status(self) -> Dict:
        """Get current quota status."""
        minute_stats = self._get_minute_stats()
        
        return {
            "date": self.data["date"],
            "daily": {
                "requests": self.data["daily_requests"],
                "requests_limit": self.FREE_TIER_LIMITS["rpd"],
                "requests_percent": (self.data["daily_requests"] / self.FREE_TIER_LIMITS["rpd"]) * 100,
                "tokens": self.data["daily_tokens"],
            },
            "minute": {
                "requests": minute_stats["requests"],
                "requests_limit": self.FREE_TIER_LIMITS["rpm"],
                "requests_percent": (minute_stats["requests"] / self.FREE_TIER_LIMITS["rpm"]) * 100,
                "tokens": minute_stats["tokens"],
                "tokens_limit": self.FREE_TIER_LIMITS["tpm"],
                "tokens_percent": (minute_stats["tokens"] / self.FREE_TIER_LIMITS["tpm"]) * 100,
            },
        }
    
    def print_status(self):
        """Print human-readable status."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("📊 GEMINI PRO QUOTA STATUS (FREE TIER)")
        print("="*60)
        print(f"📅 Date: {status['date']}")
        print(f"\n🗓️  DAILY USAGE:")
        print(f"   Requests: {status['daily']['requests']:,}/{status['daily']['requests_limit']:,} ({status['daily']['requests_percent']:.1f}%)")
        print(f"   Tokens:   {status['daily']['tokens']:,}")
        print(f"\n⏱️  CURRENT MINUTE:")
        print(f"   Requests: {status['minute']['requests']}/{status['minute']['requests_limit']} ({status['minute']['requests_percent']:.1f}%)")
        print(f"   Tokens:   {status['minute']['tokens']:,}/{status['minute']['tokens_limit']:,} ({status['minute']['tokens_percent']:.1f}%)")
        print("="*60 + "\n")
    
    def should_throttle(self) -> tuple[bool, Optional[str]]:
        """
        Check if we should throttle requests.
        
        Returns:
            (should_throttle: bool, reason: str)
        """
        minute_stats = self._get_minute_stats()
        
        # Check daily limit
        if self.data["daily_requests"] >= self.FREE_TIER_LIMITS["rpd"] * 0.99:
            return True, f"Daily limit reached ({self.data['daily_requests']}/{self.FREE_TIER_LIMITS['rpd']})"
        
        # Check minute request limit
        if minute_stats["requests"] >= self.FREE_TIER_LIMITS["rpm"] * 0.95:
            return True, f"Minute request limit reached ({minute_stats['requests']}/{self.FREE_TIER_LIMITS['rpm']})"
        
        # Check minute token limit
        if minute_stats["tokens"] >= self.FREE_TIER_LIMITS["tpm"] * 0.95:
            return True, f"Minute token limit reached ({minute_stats['tokens']:,}/{self.FREE_TIER_LIMITS['tpm']:,})"
        
        return False, None


# =============================================================================
# HELPER FUNCTIONS FOR EASY INTEGRATION
# =============================================================================

# Global tracker instance
_tracker = None

def get_tracker() -> GeminiQuotaTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = GeminiQuotaTracker()
    return _tracker


def track_gemini_request(input_tokens: int, output_tokens: int, query_preview: str = None) -> Dict:
    """
    Quick function to track a Gemini request.
    
    Usage:
        result = track_gemini_request(500, 200, "What is RAG?")
        if result["alerts"]:
            for alert in result["alerts"]:
                print(alert["message"])
    """
    tracker = get_tracker()
    return tracker.track_request(input_tokens, output_tokens, query_preview=query_preview)


def print_quota_status():
    """Quick function to print current quota status."""
    tracker = get_tracker()
    tracker.print_status()


def check_throttle() -> bool:
    """
    Quick function to check if we should throttle requests.
    
    Usage:
        if check_throttle():
            print("⏸️  Rate limit reached, waiting...")
            time.sleep(60)
    """
    tracker = get_tracker()
    should_throttle, reason = tracker.should_throttle()
    if should_throttle:
        print(f"⏸️  THROTTLE: {reason}")
    return should_throttle


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Gemini Quota Tracker\n")
    
    # Initialize tracker
    tracker = GeminiQuotaTracker()
    
    # Show initial status
    tracker.print_status()
    
    # Simulate some API calls
    print("📝 Simulating API calls...\n")
    
    for i in range(5):
        result = tracker.track_request(
            input_tokens=500 + i*100,
            output_tokens=200 + i*50,
            query_preview=f"Test query {i+1}"
        )
        
        print(f"Request {i+1}:")
        print(f"  Tokens: {result['this_request']['total_tokens']}")
        print(f"  Daily total: {result['daily']['requests']}/{result['daily']['requests_limit']}")
        
        # Print alerts
        if result["alerts"]:
            for alert in result["alerts"]:
                print(f"  {alert['message']}")
        
        print()
        time.sleep(0.5)
    
    # Show final status
    tracker.print_status()
    
    # Test throttle check
    print("🔍 Testing throttle check...")
    should_throttle, reason = tracker.should_throttle()
    if should_throttle:
        print(f"⏸️  {reason}")
    else:
        print("✅ All good, no throttling needed")
