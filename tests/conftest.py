#!/usr/bin/env python3
"""
Pytest Configuration and Fixtures
Shared test configuration and fixtures for Calgary Analytica test suite
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager


@pytest.fixture(scope="session")
def test_config():
    """Create test configuration with temporary directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test config manager with temp directories
        config_manager = ConfigManager()
        
        # Override paths to use temp directory
        test_paths = {
            'database': temp_path / "test_calgary_data.db",
            'validation_base': temp_path / "validation",
            'raw_data': temp_path / "raw",
            'processed_dir': temp_path / "processed"
        }
        
        # Create test directories
        for path in test_paths.values():
            if path.suffix != '.db':  # Don't create directories for database files
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
        
        # Patch config manager paths
        config_manager._test_paths = test_paths
        config_manager.get_database_path = lambda: test_paths['database']
        config_manager.get_validation_base = lambda: test_paths['validation_base']
        config_manager.get_processed_dir = lambda: test_paths['processed_dir']
        
        yield config_manager


@pytest.fixture
def test_database(test_config):
    """Create test database with sample schema."""
    db_path = test_config.get_database_path()
    
    conn = sqlite3.connect(db_path)
    
    # Create test tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS housing_city_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            property_type TEXT NOT NULL,
            sales INTEGER,
            new_listings INTEGER,
            inventory INTEGER,
            days_on_market INTEGER,
            benchmark_price INTEGER,
            median_price INTEGER,
            average_price INTEGER,
            source_pdf TEXT,
            extracted_date TEXT,
            confidence_score REAL,
            validation_status TEXT,
            UNIQUE(date, property_type)
        );
        
        CREATE TABLE IF NOT EXISTS housing_district_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            property_type TEXT NOT NULL,
            district TEXT NOT NULL,
            new_sales INTEGER,
            new_listings INTEGER,
            sales_to_listings_ratio TEXT,
            inventory INTEGER,
            months_supply REAL,
            benchmark_price INTEGER,
            yoy_price_change REAL,
            mom_price_change REAL,
            source_pdf TEXT,
            extracted_date TEXT,
            confidence_score REAL,
            validation_status TEXT,
            UNIQUE(date, property_type, district)
        );
        
        CREATE TABLE IF NOT EXISTS economic_indicators_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            indicator_type TEXT NOT NULL,
            indicator_name TEXT NOT NULL,
            value REAL,
            unit TEXT,
            yoy_change REAL,
            mom_change REAL,
            category TEXT,
            source_file TEXT,
            extracted_date TEXT,
            confidence_score REAL,
            validation_status TEXT,
            UNIQUE(date, indicator_type, indicator_name)
        );
    """)
    
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def sample_city_data():
    """Sample city housing data for testing."""
    return pd.DataFrame([
        {
            'date': '2025-01-01',
            'property_type': 'Detached',
            'sales': 150,
            'new_listings': 200,
            'inventory': 500,
            'days_on_market': 30,
            'benchmark_price': 650000,
            'median_price': 675000,
            'average_price': 700000,
            'source_pdf': 'test_data',
            'extracted_date': datetime.now().isoformat(),
            'confidence_score': 0.95,
            'validation_status': 'approved'
        },
        {
            'date': '2025-01-01',
            'property_type': 'Apartment',
            'sales': 75,
            'new_listings': 100,
            'inventory': 250,
            'days_on_market': 25,
            'benchmark_price': 350000,
            'median_price': 360000,
            'average_price': 375000,
            'source_pdf': 'test_data',
            'extracted_date': datetime.now().isoformat(),
            'confidence_score': 0.92,
            'validation_status': 'approved'
        }
    ])


@pytest.fixture
def sample_district_data():
    """Sample district housing data for testing."""
    return pd.DataFrame([
        {
            'date': '2025-01-01',
            'property_type': 'Detached',
            'district': 'Northwest',
            'new_sales': 25,
            'new_listings': 30,
            'sales_to_listings_ratio': '83%',
            'inventory': 80,
            'months_supply': 2.5,
            'benchmark_price': 750000,
            'yoy_price_change': 5.2,
            'mom_price_change': 1.1,
            'source_pdf': 'test_data',
            'extracted_date': datetime.now().isoformat(),
            'confidence_score': 0.88,
            'validation_status': 'approved'
        }
    ])


@pytest.fixture
def sample_economic_data():
    """Sample economic indicators data for testing."""
    return pd.DataFrame([
        {
            'date': '2025-01-01',
            'indicator_type': 'employment',
            'indicator_name': 'unemployment_rate',
            'value': 6.5,
            'unit': 'percent',
            'yoy_change': -0.8,
            'mom_change': -0.1,
            'category': 'labour_market',
            'source_file': 'test_economic_data',
            'extracted_date': datetime.now().isoformat(),
            'confidence_score': 0.98,
            'validation_status': 'approved'
        }
    ])


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for extraction testing."""
    return {
        'text': """
        Calgary Real Estate Board Monthly Statistics
        January 2025
        
        City-wide Sales Summary:
        Total Sales: 350
        New Listings: 450
        Average Price: $525,000
        
        District Breakdown:
        Northwest - Detached: 25 sales, $750,000 benchmark
        Southeast - Apartment: 15 sales, $320,000 benchmark
        """,
        'tables': [
            {
                'headers': ['Property Type', 'Sales', 'New Listings', 'Benchmark Price'],
                'rows': [
                    ['Detached', '150', '200', '$650,000'],
                    ['Apartment', '75', '100', '$350,000'],
                    ['Townhouse', '50', '75', '$450,000']
                ]
            }
        ]
    }


@pytest.fixture
def mock_validation_result():
    """Mock validation result for testing."""
    return {
        'confidence_score': 0.92,
        'data_quality_score': 0.95,
        'record_count': 5,
        'validation_errors': [],
        'validation_warnings': ['Low benchmark price confidence'],
        'requires_manual_review': False,
        'recommendation': 'approve'
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_files():
    """Create temporary files for testing."""
    temp_files = []
    
    def create_temp_file(content: str, suffix: str = '.txt') -> Path:
        temp_file = Path(tempfile.mktemp(suffix=suffix))
        temp_file.write_text(content)
        temp_files.append(temp_file)
        return temp_file
    
    yield create_temp_file
    
    # Cleanup
    for temp_file in temp_files:
        temp_file.unlink(missing_ok=True)


@pytest.fixture
def mock_extractor():
    """Mock extractor for testing."""
    class MockExtractor:
        def __init__(self, name="test_extractor"):
            self.name = name
            
        def extract(self, **kwargs):
            return {
                'success': True,
                'records_found': 5,
                'confidence': 0.95,
                'method': 'mock_extraction',
                'data': kwargs.get('mock_data', [])
            }
            
        def validate(self, data):
            return {
                'confidence_score': 0.95,
                'validation_errors': [],
                'validation_warnings': [],
                'requires_manual_review': False
            }
    
    return MockExtractor()


# Test utilities
def assert_database_record_count(conn, table, expected_count):
    """Assert database table has expected record count."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    actual_count = cursor.fetchone()[0]
    assert actual_count == expected_count, f"Expected {expected_count} records in {table}, got {actual_count}"


def create_test_csv(data: pd.DataFrame, temp_dir: Path, filename: str) -> Path:
    """Create a test CSV file."""
    csv_path = temp_dir / filename
    data.to_csv(csv_path, index=False)
    return csv_path