"""
Tests for Config Manager (BET-009)
"""

import pytest
import os
from config.config_manager import ConfigManager, OptimizationConfig, get_config_manager


def test_config_manager_initialization():
    """Test config manager initializes with correct defaults"""
    # Clear env var for clean test
    if "RAG_CONFIG" in os.environ:
        del os.environ["RAG_CONFIG"]
    
    manager = ConfigManager()
    
    assert manager.active_config_name == "baseline"
    config = manager.get_config()
    assert isinstance(config, OptimizationConfig)
    assert config.enable_compression == False


def test_get_config_by_name():
    """Test retrieving specific configs by name"""
    manager = ConfigManager()
    
    config_8 = manager.get_config_by_name("config_8_beta")
    assert config_8 is not None
    assert config_8.enable_compression == True
    assert config_8.compression_ratio == 0.7
    assert config_8.cache_threshold == 0.95


def test_switch_config_valid():
    """Test switching to valid config"""
    manager = ConfigManager()
    
    success = manager.switch_config("config_8_beta")
    assert success == True
    assert manager.active_config_name == "config_8_beta"
    
    config = manager.get_config()
    assert config.name == "Config #8 - Beta Rollout"


def test_switch_config_invalid():
    """Test switching to invalid config"""
    # Clear env var for clean test
    if "RAG_CONFIG" in os.environ:
        del os.environ["RAG_CONFIG"]
    
    manager = ConfigManager()
    
    success = manager.switch_config("invalid_config")
    assert success == False
    assert manager.active_config_name == "baseline"  # Should stay on current


def test_list_configs():
    """Test listing all available configs"""
    manager = ConfigManager()
    
    configs = manager.list_configs()
    assert isinstance(configs, dict)
    assert "baseline" in configs
    assert "config_8_beta" in configs
    assert "config_17_scaleout" in configs


def test_get_stats():
    """Test getting config manager statistics"""
    manager = ConfigManager()
    manager.switch_config("config_17_scaleout")
    
    stats = manager.get_stats()
    assert stats["active_config"] == "config_17_scaleout"
    assert "baseline" in stats["available_configs"]
    assert stats["config_details"]["compression"] == True


def test_env_variable_override():
    """Test environment variable override"""
    os.environ["RAG_CONFIG"] = "config_8_beta"
    
    manager = ConfigManager()
    assert manager.active_config_name == "config_8_beta"
    
    # Cleanup
    del os.environ["RAG_CONFIG"]


def test_env_variable_invalid():
    """Test invalid environment variable falls back to default"""
    os.environ["RAG_CONFIG"] = "invalid"
    
    manager = ConfigManager(default_config="baseline")
    assert manager.active_config_name == "baseline"
    
    # Cleanup
    del os.environ["RAG_CONFIG"]


def test_singleton_pattern():
    """Test global singleton instance"""
    manager1 = get_config_manager()
    manager2 = get_config_manager()
    
    assert manager1 is manager2  # Same instance


def test_config_8_targets():
    """Test Config #8 has correct targets"""
    manager = ConfigManager()
    config = manager.get_config_by_name("config_8_beta")
    
    assert config.target_latency == 10.4
    assert config.target_cost == 0.0017
    assert config.target_faithfulness == 0.763


def test_config_17_targets():
    """Test Config #17 has correct targets"""
    manager = ConfigManager()
    config = manager.get_config_by_name("config_17_scaleout")
    
    assert config.target_latency == 8.2
    assert config.target_cost == 0.0013
    assert config.target_faithfulness == 0.845


@pytest.mark.parametrize("config_name", ["baseline", "config_8_beta", "config_17_scaleout", "config_6_aggressive"])
def test_all_configs_valid(config_name):
    """Test all predefined configs are valid"""
    manager = ConfigManager()
    config = manager.get_config_by_name(config_name)
    
    assert config is not None
    assert isinstance(config, OptimizationConfig)
    assert config.name is not None
    assert config.target_latency > 0
    assert config.target_cost > 0
    assert 0 < config.target_faithfulness <= 1.0
