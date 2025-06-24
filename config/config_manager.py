#!/usr/bin/env python3
"""
Calgary Analytica Configuration Manager
Centralized configuration management for all paths and settings
"""

import os
import configparser
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Centralized configuration manager for Calgary Analytica project."""
    
    def __init__(self, config_file: str = None):
        self.project_root = self._find_project_root()
        self.config_file = config_file or self.project_root / "config" / "calgary_analytica.ini"
        self.config = self._load_config()
        
    def _find_project_root(self) -> Path:
        """Auto-detect project root by looking for markers."""
        current = Path(__file__).parent.parent  # Start from config directory
        markers = ['CLAUDE.md', '.git', 'requirements.txt', 'data-lake']
        
        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        # Fallback to environment variable or default
        return Path(os.environ.get('CALGARY_ANALYTICA_ROOT', '/home/chris/calgary-analytica'))
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration with interpolation support."""
        config = configparser.ConfigParser()
        
        if self.config_file.exists():
            config.read(self.config_file)
        else:
            # Create default configuration
            self._create_default_config()
            config.read(self.config_file)
            
        return config
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = f"""[project]
name = calgary-analytica
version = 1.0.0

[database]
primary_db = {self.project_root}/data-lake/calgary_data.db
backup_db = {self.project_root}/data-lake/backups/calgary_data_backup.db

[data_sources]
creb_pdf_dir = {self.project_root}/data-engine/creb/raw
economic_data_dir = {self.project_root}/data-engine/economic/raw
crime_data_dir = {self.project_root}/data-engine/police/raw
raw_data = {self.project_root}/data-engine

[validation]
validation_base = {self.project_root}/data-engine/validation
pending_review = {self.project_root}/data-engine/validation/pending
approved_data = {self.project_root}/data-engine/validation/approved
rejected_data = {self.project_root}/data-engine/validation/rejected
audit_logs = {self.project_root}/data-engine/validation/logs

[thresholds]
auto_approve_confidence = 0.90
manual_review_confidence = 0.70
rejection_confidence = 0.50
"""
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            f.write(default_config.strip())
    
    # Database paths
    def get_database_path(self) -> Path:
        """Get primary database path."""
        return Path(self.config['database']['primary_db'])
    
    def get_backup_database_path(self) -> Path:
        """Get backup database path."""
        return Path(self.config['database']['backup_db'])
    
    # Data source paths
    def get_creb_pdf_dir(self) -> Path:
        """Get CREB PDF directory."""
        return Path(self.config['data_sources']['creb_pdf_dir'])
    
    def get_economic_data_dir(self) -> Path:
        """Get economic data directory."""
        return Path(self.config['data_sources']['economic_data_dir'])
    
    def get_crime_data_dir(self) -> Path:
        """Get crime data directory."""
        return Path(self.config['data_sources']['crime_data_dir'])
    
    # Raw data path
    def get_raw_data_dir(self) -> Path:
        """Get raw data directory."""
        return Path(self.config['data_sources']['raw_data'])
    
    # Processed data path
    def get_processed_dir(self) -> Path:
        """Get processed data directory."""
        return self.project_root / "data-engine" / "data" / "processed"
    
    # Validation paths
    def get_validation_base(self) -> Path:
        """Get validation base directory."""
        return Path(self.config['validation']['validation_base'])
    
    def get_pending_review_dir(self) -> Path:
        """Get pending review directory."""
        return Path(self.config['validation']['pending_review'])
    
    def get_approved_data_dir(self) -> Path:
        """Get approved data directory."""
        return Path(self.config['validation']['approved_data'])
    
    def get_rejected_data_dir(self) -> Path:
        """Get rejected data directory."""
        return Path(self.config['validation']['rejected_data'])
    
    def get_audit_logs_dir(self) -> Path:
        """Get audit logs directory."""
        return Path(self.config['validation']['audit_logs'])
    
    # Thresholds
    def get_auto_approve_threshold(self) -> float:
        """Get auto-approve confidence threshold."""
        return float(self.config['thresholds']['auto_approve_confidence'])
    
    def get_manual_review_threshold(self) -> float:
        """Get manual review confidence threshold."""
        return float(self.config['thresholds']['manual_review_confidence'])
    
    def get_rejection_threshold(self) -> float:
        """Get rejection confidence threshold."""
        return float(self.config['thresholds']['rejection_confidence'])
    
    
    # Utility methods
    def get_project_root(self) -> Path:
        """Get project root directory."""
        return self.project_root
    
    def get_all_paths(self) -> Dict[str, Path]:
        """Get all configured paths as a dictionary."""
        return {
            'project_root': self.get_project_root(),
            'database': self.get_database_path(),
            'backup_database': self.get_backup_database_path(),
            'creb_pdf_dir': self.get_creb_pdf_dir(),
            'economic_data_dir': self.get_economic_data_dir(),
            'crime_data_dir': self.get_crime_data_dir(),
            'raw_data': self.get_raw_data_dir(),
            'validation_base': self.get_validation_base(),
            'pending_review': self.get_pending_review_dir(),
            'approved_data': self.get_approved_data_dir(),
            'rejected_data': self.get_rejected_data_dir(),
            'audit_logs': self.get_audit_logs_dir(),
        }
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that all configured paths exist or can be created."""
        paths = self.get_all_paths()
        results = {}
        
        for name, path in paths.items():
            try:
                # For directories, check if they exist
                results[name] = path.exists()
            except Exception as e:
                results[name] = False
                
        return results
    
    def create_missing_directories(self) -> Dict[str, bool]:
        """Create any missing directories."""
        paths = self.get_all_paths()
        results = {}
        
        for name, path in paths.items():
            try:
                # For directories, create them
                path.mkdir(parents=True, exist_ok=True)
                results[name] = True
            except Exception as e:
                results[name] = False
                
        return results
    
    # Data Engine specific validation methods
    def validate_extractors(self) -> Dict[str, bool]:
        """Validate that all required extractor scripts exist."""
        extractors = {
            'creb': self.project_root / 'data-engine' / 'sources' / 'creb' / 'extractor.py',
            'economic': self.project_root / 'data-engine' / 'sources' / 'economic' / 'extractor.py',
            'crime': self.project_root / 'data-engine' / 'sources' / 'police' / 'crime_extractor.py',
        }
        
        results = {}
        for name, path in extractors.items():
            results[f'extractor_{name}'] = path.exists()
            
        return results
    
    def validate_data_pipeline(self) -> Dict[str, Any]:
        """Comprehensive validation of data pipeline components."""
        results = {
            'database_exists': self.get_database_path().exists(),
            'validation_dirs': {},
            'extractors': self.validate_extractors(),
            'pending_count': 0,
            'approved_count': 0,
        }
        
        # Check validation directories
        validation_dirs = {
            'pending': self.get_pending_review_dir(),
            'approved': self.get_approved_data_dir(),
            'rejected': self.get_rejected_data_dir(),
            'processed': self.get_approved_data_dir().parent / 'processed',
            'logs': self.get_audit_logs_dir(),
        }
        
        for name, path in validation_dirs.items():
            results['validation_dirs'][name] = path.exists()
            
        # Count pending and approved files
        try:
            if self.get_pending_review_dir().exists():
                results['pending_count'] = len(list(self.get_pending_review_dir().glob('*.csv')))
            if self.get_approved_data_dir().exists():
                results['approved_count'] = len(list(self.get_approved_data_dir().iterdir()))
        except Exception:
            pass
            
        return results
    
    def get_extraction_script(self, source: str) -> Optional[Path]:
        """Get the path to an extraction script by source name."""
        script_map = {
            'creb': self.project_root / 'data-engine' / 'sources' / 'creb' / 'extractor.py',
            'economic': self.project_root / 'data-engine' / 'sources' / 'economic' / 'extractor.py',
            'crime': self.project_root / 'data-engine' / 'sources' / 'police' / 'crime_extractor.py',
        }
        
        return script_map.get(source)
    
    def log_config_usage(self, component: str, action: str):
        """Log configuration usage for tracking which components use the config."""
        import logging
        logger = logging.getLogger('config_manager')
        logger.info(f"Config used by {component} for {action}")


# Global instance for easy access
_config_manager = None

def get_config() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # Configuration testing and validation
    config = ConfigManager()
    
    print("=== Calgary Analytica Configuration Manager ===")
    print(f"Project Root: {config.get_project_root()}")
    print(f"Database: {config.get_database_path()}")
    print(f"Config File: {config.config_file}")
    
    print("\n=== Path Validation ===")
    validation_results = config.validate_paths()
    for name, exists in validation_results.items():
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {config.get_all_paths()[name]}")
    
    print("\n=== Creating Missing Directories ===")
    creation_results = config.create_missing_directories()
    created_count = sum(creation_results.values())
    print(f"Created/verified {created_count}/{len(creation_results)} directories")