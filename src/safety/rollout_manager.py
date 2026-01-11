"""
Rollout Safety Manager with Circuit Breaker
Manages gradual rollout and automatic rollback for optimizations

Part of Phase 1.5 BET-010
"""

import os
import time
import random
import hashlib
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, bypass optimization
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern for automatic rollback on failures
    
    States:
    - CLOSED: Normal operation, allow requests
    - OPEN: Too many failures, block requests
    - HALF_OPEN: Testing if system recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening
            timeout_seconds: Time before trying HALF_OPEN
            success_threshold: Successes needed to close from HALF_OPEN
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
        
        logger.info(f"CircuitBreaker initialized: threshold={failure_threshold}, timeout={timeout_seconds}s")
    
    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            logger.info(f"Circuit breaker success in HALF_OPEN state ({self.successes}/{self.success_threshold})")
            
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
                self.successes = 0
                logger.info("✅ Circuit breaker CLOSED (system recovered)")
        
        elif self.state == CircuitState.CLOSED:
            # Decay failures on success
            if self.failures > 0:
                self.failures = max(0, self.failures - 1)
    
    def record_failure(self, error: Optional[Exception] = None):
        """Record failed operation"""
        self.failures += 1
        self.last_failure_time = time.time()
        
        error_msg = str(error) if error else "Unknown error"
        logger.warning(f"Circuit breaker failure recorded ({self.failures}/{self.failure_threshold}): {error_msg}")
        
        if self.failures >= self.failure_threshold and self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            logger.critical(f"🚨 Circuit breaker OPENED after {self.failures} failures - ROLLING BACK TO BASELINE")
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests)"""
        if self.state == CircuitState.OPEN:
            # Check if timeout expired
            if self.last_failure_time and (time.time() - self.last_failure_time) >= self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
                logger.info(f"Circuit breaker → HALF_OPEN (testing recovery after {self.timeout_seconds}s)")
                return False
            return True
        return False
    
    def get_state(self) -> str:
        """Get current circuit state"""
        return self.state.value
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        logger.info("Circuit breaker manually reset to CLOSED")


class RolloutManager:
    """
    Manage safe rollout of optimizations with circuit breaker protection
    
    Features:
    - Percentage-based rollout (0% → 10% → 50% → 100%)
    - Consistent user assignment via hashing
    - Automatic rollback on failures
    """
    
    def __init__(self):
        """Initialize rollout manager"""
        # Get rollout percentage from environment
        self.rollout_percentage = int(os.getenv("ROLLOUT_PERCENTAGE", "0"))
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
            success_threshold=2
        )
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "optimization_used": 0,
            "optimization_bypassed": 0,
            "circuit_breaker_triggered": 0
        }
        
        logger.info(f"RolloutManager initialized: rollout={self.rollout_percentage}%")
    
    def should_use_optimization(self, user_id: Optional[str] = None) -> bool:
        """
        Determine if this request should use optimization
        
        Args:
            user_id: User identifier for consistent hashing
            
        Returns:
            True if optimization should be used
        """
        self.stats["total_requests"] += 1
        
        # Check circuit breaker first
        if self.circuit_breaker.is_open():
            self.stats["circuit_breaker_triggered"] += 1
            logger.warning("Circuit breaker OPEN - bypassing optimization")
            return False
        
        # Check rollout percentage
        if self.rollout_percentage == 0:
            self.stats["optimization_bypassed"] += 1
            return False
        
        if self.rollout_percentage == 100:
            self.stats["optimization_used"] += 1
            return True
        
        # Percentage-based with consistent hashing
        if user_id:
            # Consistent assignment for same user
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            use_optimization = (hash_val % 100) < self.rollout_percentage
        else:
            # Random for anonymous users
            use_optimization = random.random() * 100 < self.rollout_percentage
        
        if use_optimization:
            self.stats["optimization_used"] += 1
        else:
            self.stats["optimization_bypassed"] += 1
        
        return use_optimization
    
    def record_success(self):
        """Record successful optimization usage"""
        self.circuit_breaker.record_success()
    
    def record_failure(self, error: Exception):
        """Record optimization failure"""
        self.circuit_breaker.record_failure(error)
    
    def set_rollout_percentage(self, percentage: int):
        """
        Update rollout percentage
        
        Args:
            percentage: New rollout percentage (0-100)
        """
        if not 0 <= percentage <= 100:
            raise ValueError(f"Rollout percentage must be 0-100, got {percentage}")
        
        old_percentage = self.rollout_percentage
        self.rollout_percentage = percentage
        logger.info(f"Rollout percentage updated: {old_percentage}% → {percentage}%")
    
    def get_rollout_stats(self) -> dict:
        """Get rollout statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            usage_rate = 0.0
        else:
            usage_rate = (self.stats["optimization_used"] / total) * 100
        
        return {
            **self.stats,
            "rollout_percentage": self.rollout_percentage,
            "actual_usage_rate": usage_rate,
            "circuit_breaker_state": self.circuit_breaker.get_state(),
            "circuit_breaker_failures": self.circuit_breaker.failures,
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker.reset()


# Singleton instance
_rollout_manager = None


def get_rollout_manager() -> RolloutManager:
    """Get global RolloutManager instance (singleton)"""
    global _rollout_manager
    if _rollout_manager is None:
        _rollout_manager = RolloutManager()
    return _rollout_manager
