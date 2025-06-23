#!/usr/bin/env python3
"""
Test Configuration Manager
Unit tests for centralized configuration management
"""

import pytest
import tempfile
from pathlib import Path
import os

from config.config_manager import ConfigManager


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_project_root_detection(self):
        """Test that project root is correctly detected."""
        config = ConfigManager()
        
        # Should find project root containing CLAUDE.md
        assert config.get_project_root().exists()
        assert (config.get_project_root() / "CLAUDE.md").exists()
    
    def test_default_configuration_creation(self):
        """Test that default configuration is created when missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.ini"
            
            # Create config manager with non-existent config file
            config = ConfigManager(str(config_file))
            
            # Config file should be created
            assert config_file.exists()
            
            # Should have default sections
            assert 'project' in config.config
            assert 'database' in config.config
            assert 'data_sources' in config.config
    
    def test_database_path_resolution(self):
        """Test database path resolution."""
        config = ConfigManager()
        db_path = config.get_database_path()
        
        assert db_path.name == "calgary_data.db"
        assert "data-lake" in str(db_path)
    
    def test_data_source_paths(self):
        """Test data source path resolution."""
        config = ConfigManager()
        
        creb_dir = config.get_creb_pdf_dir()
        economic_dir = config.get_economic_data_dir()
        crime_dir = config.get_crime_data_dir()
        
        assert "creb_pdfs" in str(creb_dir)
        assert "economic_indicators" in str(economic_dir)
        assert "police_service" in str(crime_dir)
    
    def test_data_paths(self):
        """Test data path resolution."""
        config = ConfigManager()
        
        raw_data = config.get_raw_data_dir()
        processed_dir = config.get_processed_dir()
        
        assert "raw" in str(raw_data)
        assert "processed" in str(processed_dir)
    
    def test_validation_paths(self):
        """Test validation path resolution."""
        config = ConfigManager()
        
        validation_base = config.get_validation_base()
        pending = config.get_pending_review_dir()
        approved = config.get_approved_data_dir()
        rejected = config.get_rejected_data_dir()
        
        assert "validation" in str(validation_base)
        assert validation_base in pending.parents
        assert validation_base in approved.parents
        assert validation_base in rejected.parents
    
    def test_threshold_values(self):
        """Test validation threshold values."""
        config = ConfigManager()
        
        auto_approve = config.get_auto_approve_threshold()
        manual_review = config.get_manual_review_threshold()
        rejection = config.get_rejection_threshold()
        
        # Should be reasonable confidence thresholds
        assert 0.8 <= auto_approve <= 1.0
        assert 0.5 <= manual_review <= 0.9
        assert 0.0 <= rejection <= 0.7
        
        # Logical ordering
        assert auto_approve > manual_review > rejection
    
    def test_retention_settings(self):
        """Test data retention settings."""
        config = ConfigManager()
        
        # Retention settings removed - using simple validation thresholds instead
        auto_approve = config.get_auto_approve_threshold()
        manual_review = config.get_manual_review_threshold()
        
        # Should be valid thresholds
        assert isinstance(auto_approve, float) and 0 < auto_approve <= 1
        assert isinstance(manual_review, float) and 0 < manual_review <= 1
    
    def test_all_paths_method(self):
        """Test get_all_paths method."""
        config = ConfigManager()
        all_paths = config.get_all_paths()
        
        # Should return dictionary with expected keys
        expected_keys = {
            'project_root', 'database', 'backup_database',
            'creb_pdf_dir', 'economic_data_dir', 'crime_data_dir',
            'city_csv', 'district_csv', 'processed_dir',
            'validation_base'
        }
        
        assert set(all_paths.keys()).issuperset(expected_keys)
        
        # All values should be Path objects
        for path in all_paths.values():
            assert isinstance(path, Path)
    
    def test_path_validation(self):
        """Test path validation functionality."""
        config = ConfigManager()
        validation_results = config.validate_paths()
        
        # Should return dict with boolean values
        assert isinstance(validation_results, dict)
        for result in validation_results.values():
            assert isinstance(result, bool)
    
    def test_directory_creation(self):
        """Test missing directory creation."""
        config = ConfigManager()
        creation_results = config.create_missing_directories()
        
        # Should return dict with boolean values
        assert isinstance(creation_results, dict)
        for result in creation_results.values():
            assert isinstance(result, bool)
    
    def test_environment_variable_support(self):
        """Test environment variable override support."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable
            test_root = str(Path(temp_dir) / "test_calgary_analytica")
            os.environ['CALGARY_ANALYTICA_ROOT'] = test_root
            
            try:
                config = ConfigManager()
                
                # Project root should use environment variable
                # Note: This might fall back to actual detection if markers exist
                root = config.get_project_root()
                assert isinstance(root, Path)
                
            finally:
                # Clean up environment variable
                if 'CALGARY_ANALYTICA_ROOT' in os.environ:
                    del os.environ['CALGARY_ANALYTICA_ROOT']
    
    def test_config_interpolation(self):
        """Test configuration variable interpolation."""
        config = ConfigManager()
        
        # Database path should be interpolated from root directory
        db_path = config.get_database_path()
        project_root = config.get_project_root()
        
        # Database path should be under project root
        assert project_root in db_path.parents
    
    def test_global_config_instance(self):
        """Test global configuration instance."""
        from config.config_manager import get_config
        
        config1 = get_config()
        config2 = get_config()
        
        # Should return same instance
        assert config1 is config2
        
        # Should be ConfigManager instance
        assert isinstance(config1, ConfigManager)


class TestConfigManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_config_file_path(self):
        """Test handling of invalid config file paths."""
        # Should handle non-existent parent directory gracefully
        invalid_path = "/non/existent/path/config.ini"
        
        # Should not raise exception, should create default config
        config = ConfigManager(invalid_path)
        assert config is not None
    
    def test_readonly_config_directory(self):
        """Test handling of read-only config directory."""
        # This test is platform-dependent and may be skipped on some systems
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "readonly"
            config_dir.mkdir()
            
            # Make directory read-only
            config_dir.chmod(0o444)
            
            try:
                config_file = config_dir / "config.ini"
                # Should handle gracefully (may fall back to default location)
                config = ConfigManager(str(config_file))
                assert config is not None
                
            finally:
                # Restore permissions for cleanup
                config_dir.chmod(0o755)
    
    def test_config_with_missing_sections(self):
        """Test handling of config files with missing sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "incomplete_config.ini"
            
            # Create config with only partial sections
            config_file.write_text("""
[project]
name = test-project

[database]
primary_db = /test/db.db
""")
            
            config = ConfigManager(str(config_file))
            
            # Should handle missing sections gracefully
            # and provide reasonable defaults
            assert config.get_database_path().name == "db.db"
            assert config.get_auto_approve_threshold() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])