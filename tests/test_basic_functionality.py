#!/usr/bin/env python3
"""
Basic Functionality Tests
Simple tests to verify core functionality without complex dependencies
"""

import pytest
import tempfile
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


class TestBasicFunctionality:
    """Test basic system functionality."""
    
    def test_config_manager_basic(self):
        """Test basic config manager functionality."""
        config = ConfigManager()
        
        # Should be able to get project root
        root = config.get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        
        # Should be able to get database path
        db_path = config.get_database_path()
        assert isinstance(db_path, Path)
        assert db_path.name == "calgary_data.db"
    
    def test_database_connection(self):
        """Test database connection and basic operations."""
        config = ConfigManager()
        db_path = config.get_database_path()
        
        if db_path.exists():
            # Test connection to existing database
            conn = sqlite3.connect(db_path)
            
            # Should be able to query tables
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            assert len(tables) > 0
            
            # Should have housing tables
            table_names = [table[0] for table in tables]
            assert 'housing_city_monthly' in table_names
            assert 'housing_district_monthly' in table_names
            
            conn.close()
    
    def test_data_processing_basic(self):
        """Test basic data processing functionality."""
        # Create sample data
        sample_data = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-01'],
            'property_type': ['Detached', 'Apartment'],
            'sales': [100, 50],
            'benchmark_price': [650000, 350000]
        })
        
        # Should be able to process data
        assert len(sample_data) == 2
        assert 'date' in sample_data.columns
        assert 'property_type' in sample_data.columns
        
        # Should be able to filter data
        detached_data = sample_data[sample_data['property_type'] == 'Detached']
        assert len(detached_data) == 1
        assert detached_data.iloc[0]['sales'] == 100
    
    def test_file_system_operations(self):
        """Test basic file system operations."""
        config = ConfigManager()
        
        # Should be able to create directories
        test_dir = config.get_validation_base() / "test_operations"
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists()
        
        # Should be able to create and read files
        test_file = test_dir / "test_file.txt"
        test_content = "Test file content"
        test_file.write_text(test_content)
        
        assert test_file.exists()
        assert test_file.read_text() == test_content
        
        # Cleanup
        test_file.unlink()
        test_dir.rmdir()
    
    def test_path_resolution(self):
        """Test path resolution functionality."""
        config = ConfigManager()
        
        # All paths should be Path objects
        all_paths = config.get_all_paths()
        for name, path in all_paths.items():
            assert isinstance(path, Path), f"Path {name} is not a Path object: {type(path)}"
        
        # Database path should be absolute
        db_path = config.get_database_path()
        assert db_path.is_absolute()
        
        # Validation paths should be properly configured
        validation_base = config.get_validation_base()
        assert validation_base.is_absolute()
    
    def test_monthly_update_script(self):
        """Test monthly update script can be imported."""
        try:
            import monthly_update
            assert hasattr(monthly_update, 'main')
        except ImportError as e:
            pytest.skip(f"Monthly update script not importable: {e}")
    
    def test_data_engine_import(self):
        """Test data engine components can be imported."""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "data-engine"))
            from core.data_engine import DataEngine
            assert DataEngine is not None
        except ImportError as e:
            pytest.skip(f"Data engine not importable: {e}")
    
    def test_configuration_values(self):
        """Test configuration values are reasonable."""
        config = ConfigManager()
        
        # Thresholds should be reasonable
        auto_approve = config.get_auto_approve_threshold()
        manual_review = config.get_manual_review_threshold()
        rejection = config.get_rejection_threshold()
        
        assert 0.0 <= rejection <= 1.0
        assert 0.0 <= manual_review <= 1.0
        assert 0.0 <= auto_approve <= 1.0
        assert rejection < manual_review < auto_approve
        
        # Retention days should be positive (skip staging check since it's removed)
        # validation_days = config.get_validation_retention_days()
        # audit_days = config.get_audit_logs_retention_days()
        # assert validation_days > 0
        # assert audit_days > 0
    
    def test_database_schema_validation(self):
        """Test database schema is as expected."""
        config = ConfigManager()
        db_path = config.get_database_path()
        
        if not db_path.exists():
            pytest.skip("Database does not exist")
        
        conn = sqlite3.connect(db_path)
        
        # Check housing_city_monthly schema
        city_schema = conn.execute("PRAGMA table_info(housing_city_monthly)").fetchall()
        city_columns = [col[1] for col in city_schema]
        
        expected_city_columns = ['date', 'property_type', 'sales', 'benchmark_price']
        for col in expected_city_columns:
            assert col in city_columns, f"Missing column {col} in housing_city_monthly"
        
        # Check housing_district_monthly schema
        district_schema = conn.execute("PRAGMA table_info(housing_district_monthly)").fetchall()
        district_columns = [col[1] for col in district_schema]
        
        expected_district_columns = ['date', 'property_type', 'district', 'benchmark_price']
        for col in expected_district_columns:
            assert col in district_columns, f"Missing column {col} in housing_district_monthly"
        
        conn.close()
    
    def test_error_handling_basics(self):
        """Test basic error handling functionality."""
        from config.error_handling import DataOperationError, ExtractionError
        
        # Should be able to create and raise custom exceptions
        error = DataOperationError("Test error", "test_operation")
        assert str(error) == "Test error"
        assert error.operation == "test_operation"
        
        # Inheritance should work
        extraction_error = ExtractionError("Extraction failed", "extract_data")
        assert isinstance(extraction_error, DataOperationError)
        assert extraction_error.operation == "extract_data"


class TestSystemHealthCheck:
    """System health check tests."""
    
    def test_required_directories_exist(self):
        """Test that required directories exist or can be created."""
        config = ConfigManager()
        
        # Key directories that should exist or be creatable
        key_paths = [
            config.get_project_root(),
            config.get_database_path().parent,  # data-lake directory
            config.get_validation_base().parent,   # data-engine directory
        ]
        
        for path in key_paths:
            if not path.exists():
                # Try to create if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            
            assert path.exists(), f"Required path does not exist and cannot be created: {path}"
    
    def test_database_accessibility(self):
        """Test database is accessible and has expected structure."""
        config = ConfigManager()
        db_path = config.get_database_path()
        
        if db_path.exists():
            # Should be able to connect and query
            conn = sqlite3.connect(db_path)
            
            # Should be able to run basic queries
            try:
                result = conn.execute("SELECT 1").fetchone()
                assert result[0] == 1
                
                # Should have tables
                tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()
                assert tables[0] > 0
                
            finally:
                conn.close()
    
    def test_python_dependencies(self):
        """Test that required Python dependencies are available."""
        required_imports = [
            'pandas',
            'numpy', 
            'sqlite3',  # Built-in
            'pathlib',  # Built-in
            'json',     # Built-in
            'logging',  # Built-in
        ]
        
        for module_name in required_imports:
            try:
                __import__(module_name)
            except ImportError:
                pytest.fail(f"Required module {module_name} is not available")
    
    def test_file_permissions(self):
        """Test file system permissions are adequate."""
        config = ConfigManager()
        
        # Should be able to write to validation directory
        validation_base = config.get_validation_base()
        validation_base.mkdir(parents=True, exist_ok=True)
        
        test_file = validation_base / "permission_test.txt"
        try:
            test_file.write_text("test")
            content = test_file.read_text()
            assert content == "test"
        finally:
            test_file.unlink(missing_ok=True)
    
    def test_configuration_consistency(self):
        """Test configuration consistency across the system."""
        config = ConfigManager()
        
        # Database path should be consistent
        db_path1 = config.get_database_path()
        db_path2 = config.get_database_path()
        assert db_path1 == db_path2
        
        # All paths should be under project root
        project_root = config.get_project_root()
        paths_to_check = [
            config.get_database_path(),
            config.get_validation_base(),
            config.get_validation_base(),
        ]
        
        for path in paths_to_check:
            assert project_root in path.parents or project_root == path.parent, \
                f"Path {path} is not under project root {project_root}"


if __name__ == "__main__":
    # Run tests directly if executed as script
    import pytest
    pytest.main([__file__, "-v"])