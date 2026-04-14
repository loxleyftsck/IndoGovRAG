"""
Configuration Manager for RAG Optimization Configs
Manages Config #8 (Beta) and Config #17 (Scale-out)

Part of Phase 1.5 BET-009
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for RAG optimizations"""
    name: str
    enable_compression: bool = False
    compression_ratio: float = 1.0
    enable_cache: bool = False
    cache_threshold: float = 0.95
    cache_ttl_days: int = 7
    target_latency: float = 15.0
    target_cost: float = 0.003
    target_faithfulness: float = 0.780
    description: str = ""


class ConfigManager:
    """Manage RAG optimization configurations for A/B testing"""
    
    # Predefined configurations from Phase 1.5 experiments
    CONFIGS = {
        "baseline": OptimizationConfig(
            name="Baseline",
            enable_compression=False,
            enable_cache=False,
            target_latency=15.3,
            target_cost=0.0029,
            target_faithfulness=0.780,
            description="No optimizations (control group)"
        ),
        "config_8_beta": OptimizationConfig(
            name="Config #8 - Beta Rollout",
            enable_compression=True,
            compression_ratio=0.7,
            enable_cache=True,
            cache_threshold=0.95,
            cache_ttl_days=7,
            target_latency=10.4,
            target_cost=0.0017,
            target_faithfulness=0.763,
            description="Compression 0.7 + Cache 0.95 (recommended for beta)"
        ),
        "config_17_scaleout": OptimizationConfig(
            name="Config #17 - Scale-out",
            enable_compression=True,
            compression_ratio=0.7,
            enable_cache=True,
            cache_threshold=0.95,
            cache_ttl_days=7,
            target_latency=8.2,
            target_cost=0.0013,
            target_faithfulness=0.845,
            description="Higher quality variant for production scale"
        ),
        "config_6_aggressive": OptimizationConfig(
            name="Config #6 - Aggressive Cost Reduction",
            enable_compression=True,
            compression_ratio=0.7,
            enable_cache=True,
            cache_threshold=0.9,
            cache_ttl_days=7,
            target_latency=6.4,
            target_cost=0.0010,
            target_faithfulness=0.768,
            description="Maximum cost savings (experimental)"
        ),
    }
    
    def __init__(self, default_config: str = "baseline"):
        """
        Initialize config manager
        
        Args:
            default_config: Default configuration name
        """
        # Check environment variable override
        env_config = os.getenv("RAG_CONFIG", default_config)
        
        if env_config not in self.CONFIGS:
            logger.warning(f"Unknown config '{env_config}', falling back to '{default_config}'")
            self.active_config_name = default_config
        else:
            self.active_config_name = env_config
        
        logger.info(f"ConfigManager initialized with: {self.active_config_name}")
    
    def get_config(self) -> OptimizationConfig:
        """Get currently active configuration"""
        return self.CONFIGS[self.active_config_name]
    
    def get_config_by_name(self, name: str) -> Optional[OptimizationConfig]:
        """Get configuration by name"""
        return self.CONFIGS.get(name)
    
    def switch_config(self, config_name: str) -> bool:
        """
        Switch to a different configuration
        
        Args:
            config_name: Name of target configuration
            
        Returns:
            True if successful, False if config not found
        """
        if config_name not in self.CONFIGS:
            logger.error(f"Cannot switch to unknown config: {config_name}")
            logger.info(f"Available configs: {list(self.CONFIGS.keys())}")
            return False
        
        old_config = self.active_config_name
        self.active_config_name = config_name
        logger.info(f"Switched config: {old_config} → {config_name}")
        return True
    
    def list_configs(self) -> Dict[str, str]:
        """List all available configurations with descriptions"""
        return {
            name: config.description 
            for name, config in self.CONFIGS.items()
        }
    
    def get_stats(self) -> Dict:
        """Get config manager statistics"""
        return {
            "active_config": self.active_config_name,
            "available_configs": list(self.CONFIGS.keys()),
            "config_details": {
                "name": self.get_config().name,
                "compression": self.get_config().enable_compression,
                "cache": self.get_config().enable_cache,
                "target_latency": self.get_config().target_latency,
                "target_cost": self.get_config().target_cost,
            }
        }


# Singleton instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global ConfigManager instance (singleton)"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
