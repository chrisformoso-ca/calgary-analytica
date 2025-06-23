#!/usr/bin/env python3
"""
Test Pipeline Manager
Unit and integration tests for data pipeline orchestration
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

sys.path.append(str(Path(__file__).parent.parent / "data-engine" / "core"))
from pipeline_manager import DataPipelineManager


class TestPipelineManagerInitialization:
    """Test pipeline manager initialization and configuration."""
    
    def test_pipeline_manager_init(self, test_config):
        """Test pipeline manager initialization."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            # Mock the path resolution
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            assert pipeline is not None
            assert hasattr(pipeline, 'config')
            assert hasattr(pipeline, 'extractors')
    
    def test_extractor_registration(self, test_config):
        """Test extractor registration functionality."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Create mock extractor
            mock_extractor = Mock()
            mock_extractor.name = "test_extractor"
            
            # Register extractor
            pipeline.register_extractor(mock_extractor)
            
            assert "test_extractor" in pipeline.extractors
            assert pipeline.extractors["test_extractor"] is mock_extractor
    
    def test_config_loading(self, test_config):
        """Test configuration loading and path setup."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Should have loaded configuration
            assert pipeline.config is not None
            assert pipeline.auto_approve_threshold > 0
            assert pipeline.manual_review_threshold > 0


class TestValidationProcessing:
    """Test validation processing functionality."""
    
    def test_process_pending_validations_empty(self, test_config):
        """Test processing when no pending validations exist."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Mock empty pending directory
            with patch.object(pipeline, 'pending_path') as mock_pending:
                mock_pending.exists.return_value = False
                
                result = pipeline.process_pending_validations()
                
                assert "message" in result
                assert "No pending validations directory" in result["message"]
    
    def test_process_pending_validations_with_items(self, test_config, temp_files):
        """Test processing pending validation items."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Create mock validation directory with report
            validation_report = {
                "confidence_score": 0.95,
                "validation_errors": [],
                "validation_warnings": [],
                "requires_manual_review": False,
                "recommendation": "approve"
            }
            
            report_file = temp_files(json.dumps(validation_report), '.json')
            validation_dir = report_file.parent
            
            # Mock pending directory
            with patch.object(pipeline, 'pending_path') as mock_pending:
                mock_pending.exists.return_value = True
                mock_pending.iterdir.return_value = [validation_dir]
                
                # Mock validation report file
                with patch.object(pipeline, '_process_single_validation') as mock_process:
                    mock_process.return_value = {
                        "validation": "test_validation",
                        "action": "auto_approved",
                        "confidence": 0.95
                    }
                    
                    result = pipeline.process_pending_validations()
                    
                    assert result["pending_processed"] == 1
                    assert result["auto_approved"] == 1
                    assert result["errors"] == 0
    
    def test_process_single_validation_auto_approve(self, test_config, temp_files):
        """Test single validation processing with auto-approval."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            pipeline.auto_approve_threshold = 0.9
            
            # Create validation report with high confidence
            validation_report = {
                "confidence_score": 0.95,
                "validation_errors": [],
                "validation_warnings": [],
                "requires_manual_review": False
            }
            
            report_file = temp_files(json.dumps(validation_report), '.json')
            validation_dir = report_file.parent
            validation_dir.name = "test_validation"
            
            # Mock the validation report file path
            with patch.object(validation_dir, '__truediv__') as mock_div:
                mock_div.return_value = report_file
                
                # Mock approved path
                with patch.object(pipeline, 'approved_path') as mock_approved:
                    mock_approved.mkdir = Mock()
                    
                    with patch('shutil.move') as mock_move:
                        result = pipeline._process_single_validation(validation_dir, auto_approve=True)
                        
                        assert result["action"] == "auto_approved"
                        assert result["confidence"] == 0.95
    
    def test_process_single_validation_manual_review(self, test_config, temp_files):
        """Test single validation processing requiring manual review."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            pipeline.auto_approve_threshold = 0.9
            
            # Create validation report with low confidence
            validation_report = {
                "confidence_score": 0.75,
                "validation_errors": [],
                "validation_warnings": ["Low confidence warning"],
                "requires_manual_review": True
            }
            
            report_file = temp_files(json.dumps(validation_report), '.json')
            validation_dir = report_file.parent
            validation_dir.name = "test_validation"
            
            # Mock the validation report file path
            with patch.object(validation_dir, '__truediv__') as mock_div:
                mock_div.return_value = report_file
                
                result = pipeline._process_single_validation(validation_dir, auto_approve=True)
                
                assert result["action"] == "manual_review_required"
                assert result["confidence"] == 0.75
    
    def test_process_single_validation_missing_report(self, test_config):
        """Test single validation processing with missing report."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Create mock validation directory without report
            validation_dir = Mock()
            validation_dir.name = "test_validation"
            
            # Mock missing validation report
            mock_report_file = Mock()
            mock_report_file.exists.return_value = False
            validation_dir.__truediv__.return_value = mock_report_file
            
            result = pipeline._process_single_validation(validation_dir, auto_approve=True)
            
            assert result["action"] == "error"
            assert "No validation report found" in result["error"]


class TestBatchExtraction:
    """Test batch extraction functionality."""
    
    def test_run_batch_extraction_empty(self, test_config):
        """Test batch extraction with no extractors."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            result = pipeline.run_batch_extraction()
            
            assert result["extractors_run"] == 0
            assert result["successful_extractions"] == 0
            assert result["success"] is True  # No extractors = no failures
    
    def test_run_batch_extraction_with_extractors(self, test_config, mock_extractor):
        """Test batch extraction with registered extractors."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Register mock extractors
            mock_extractor1 = Mock()
            mock_extractor1.name = "extractor1"
            mock_extractor1.extract_and_validate.return_value = {"success": True}
            
            mock_extractor2 = Mock()
            mock_extractor2.name = "extractor2"
            mock_extractor2.extract_and_validate.return_value = {"success": False, "error": "Test error"}
            
            pipeline.register_extractor(mock_extractor1)
            pipeline.register_extractor(mock_extractor2)
            
            result = pipeline.run_batch_extraction()
            
            assert result["extractors_run"] == 2
            assert result["successful_extractions"] == 1
            assert result["failed_extractions"] == 1
            assert result["success"] is False  # Had failures
    
    def test_run_batch_extraction_with_exception(self, test_config):
        """Test batch extraction with extractor exceptions."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Register mock extractor that raises exception
            mock_extractor = Mock()
            mock_extractor.name = "failing_extractor"
            mock_extractor.extract_and_validate.side_effect = ExtractionError("Test extraction error", "test_op")
            
            pipeline.register_extractor(mock_extractor)
            
            result = pipeline.run_batch_extraction()
            
            assert result["extractors_run"] == 1
            assert result["successful_extractions"] == 0
            assert result["failed_extractions"] == 1


class TestDataLoading:
    """Test data loading functionality."""
    
    def test_load_validated_data_no_directory(self, test_config):
        """Test loading when validated directory doesn't exist."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Mock non-existent validated path
            with patch.object(pipeline, 'validated_path') as mock_validated:
                mock_validated.exists.return_value = False
                
                result = pipeline.load_validated_data()
                
                assert "message" in result
                assert "No validated data directory" in result["message"]
    
    def test_load_validated_data_no_files(self, test_config):
        """Test loading when no CSV files exist."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Mock empty validated directory
            with patch.object(pipeline, 'validated_path') as mock_validated:
                mock_validated.exists.return_value = True
                mock_validated.glob.return_value = []
                
                result = pipeline.load_validated_data()
                
                assert "message" in result
                assert "No validated CSV files found" in result["message"]
    
    def test_load_single_csv_success(self, test_config, sample_city_data, temp_files):
        """Test successful loading of single CSV file."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Create temporary CSV file
            csv_content = sample_city_data.to_csv(index=False)
            csv_file = temp_files(csv_content, '.csv')
            
            # Mock database connection
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = Mock()
                mock_connect.return_value = mock_conn
                
                with patch('pandas.read_csv') as mock_read_csv:
                    mock_read_csv.return_value = sample_city_data
                    
                    result = pipeline._load_single_csv(csv_file)
                    
                    assert result["success"] is True
                    assert result["records_loaded"] == len(sample_city_data)


class TestErrorHandling:
    """Test error handling in pipeline operations."""
    
    def test_validation_processing_with_errors(self, test_config):
        """Test validation processing handles errors gracefully."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Mock validation directory that causes exception
            validation_dir = Mock()
            validation_dir.name = "error_validation"
            
            with patch.object(pipeline, 'pending_path') as mock_pending:
                mock_pending.exists.return_value = True
                mock_pending.iterdir.return_value = [validation_dir]
                
                # Mock _process_single_validation to raise exception
                with patch.object(pipeline, '_process_single_validation') as mock_process:
                    mock_process.side_effect = Exception("Test processing error")
                    
                    # Should not raise exception, should handle gracefully
                    result = pipeline.process_pending_validations()
                    
                    assert "pending_processed" in result
    
    def test_batch_extraction_exception_handling(self, test_config):
        """Test batch extraction handles extractor exceptions."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Register extractor that raises unexpected exception
            mock_extractor = Mock()
            mock_extractor.name = "exception_extractor"
            mock_extractor.extract_and_validate.side_effect = ValueError("Unexpected error")
            
            pipeline.register_extractor(mock_extractor)
            
            # Should handle exception gracefully
            result = pipeline.run_batch_extraction()
            
            assert result["failed_extractions"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["success"] is False


class TestIntegrationScenarios:
    """Integration tests for complete pipeline scenarios."""
    
    def test_complete_validation_workflow(self, test_config, sample_city_data, temp_files):
        """Test complete validation workflow from pending to approved."""
        with patch('data_engine.core.pipeline_manager.Path') as mock_path:
            mock_path.return_value.parent.parent = test_config.get_project_root()
            
            pipeline = DataPipelineManager()
            
            # Create mock validation setup
            validation_report = {
                "confidence_score": 0.95,
                "validation_errors": [],
                "validation_warnings": [],
                "requires_manual_review": False
            }
            
            report_file = temp_files(json.dumps(validation_report), '.json')
            validation_dir = report_file.parent
            validation_dir.name = "integration_test_validation"
            
            # Mock all necessary paths and operations
            with patch.object(pipeline, 'pending_path') as mock_pending, \
                 patch.object(pipeline, 'approved_path') as mock_approved, \
                 patch.object(validation_dir, '__truediv__') as mock_div, \
                 patch('shutil.move') as mock_move:
                
                mock_pending.exists.return_value = True
                mock_pending.iterdir.return_value = [validation_dir]
                mock_approved.mkdir = Mock()
                mock_div.return_value = report_file
                
                result = pipeline.process_pending_validations(auto_approve=True)
                
                # Should auto-approve high confidence item
                assert result["auto_approved"] == 1
                assert result["errors"] == 0
                
                # Should have moved to approved directory
                mock_move.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])