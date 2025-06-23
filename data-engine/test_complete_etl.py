#!/usr/bin/env python3
"""
Complete ETL Pipeline Test
Test end-to-end workflows for all standardized extractors
"""

import logging
from pathlib import Path
import sys
from datetime import datetime

# Add data-engine to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.data_engine import DataEngine

logger = logging.getLogger(__name__)

def test_complete_etl_pipeline():
    """Test the complete ETL pipeline with all extractors."""
    
    print("🧪 Calgary Analytica - Complete ETL Pipeline Test")
    print("=" * 60)
    
    # Initialize data engine (registers all extractors)
    engine = DataEngine()
    
    # Get pipeline status
    status = engine.get_pipeline_status()
    
    print(f"\n📊 Pipeline Overview:")
    print(f"   • Database: {status['database']['path']}")
    print(f"   • Database exists: {status['database']['exists']}")
    print(f"   • Registered extractors: {status['extractors']['available']}")
    
    # Test results summary
    test_results = {}
    
    # Test 1: Economic Extractor
    print(f"\n🧪 Test 1: Economic Extractor")
    print("-" * 30)
    try:
        result = engine.run_etl_pipeline('economic', year_range=(2025, 2025))
        test_results['economic'] = {
            'success': result['success'],
            'stage': result.get('stage_result', 'unknown'),
            'records': result.get('extraction_result', {}).get('records_extracted', 0),
            'confidence': result.get('extraction_result', {}).get('confidence_score', 0.0)
        }
        print(f"   ✅ Success: {result['success']}")
        print(f"   📊 Stage: {result.get('stage_result', 'unknown')}")
        if result.get('extraction_result'):
            extraction = result['extraction_result']
            print(f"   📈 Records: {extraction.get('records_extracted', 0)}")
            print(f"   🎯 Confidence: {extraction.get('confidence_score', 0.0):.2f}")
    except Exception as e:
        test_results['economic'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Failed: {e}")
    
    # Test 2: CREB Extractor
    print(f"\n🧪 Test 2: CREB Extractor")
    print("-" * 30)
    try:
        result = engine.run_etl_pipeline('creb')
        test_results['creb'] = {
            'success': result['success'],
            'stage': result.get('stage_result', 'unknown'),
            'records': result.get('extraction_result', {}).get('records_extracted', 0),
            'confidence': result.get('extraction_result', {}).get('confidence_score', 0.0)
        }
        print(f"   ✅ Success: {result['success']}")
        print(f"   📊 Stage: {result.get('stage_result', 'unknown')}")
        if result.get('extraction_result'):
            extraction = result['extraction_result']
            print(f"   📈 Records: {extraction.get('records_extracted', 0)}")
            print(f"   🎯 Confidence: {extraction.get('confidence_score', 0.0):.2f}")
    except Exception as e:
        test_results['creb'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Crime Extractor
    print(f"\n🧪 Test 3: Crime Extractor")
    print("-" * 30)
    try:
        result = engine.run_etl_pipeline('crime')
        test_results['crime'] = {
            'success': result['success'],
            'stage': result.get('stage_result', 'unknown'),
            'records': result.get('extraction_result', {}).get('records_extracted', 0),
            'confidence': result.get('extraction_result', {}).get('confidence_score', 0.0)
        }
        print(f"   ✅ Success: {result['success']}")
        print(f"   📊 Stage: {result.get('stage_result', 'unknown')}")
        if result.get('extraction_result'):
            extraction = result['extraction_result']
            print(f"   📈 Records: {extraction.get('records_extracted', 0)}")
            print(f"   🎯 Confidence: {extraction.get('confidence_score', 0.0):.2f}")
    except Exception as e:
        test_results['crime'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Failed: {e}")
    
    # Test 4: Validation Processing
    print(f"\n🧪 Test 4: Validation Processing")
    print("-" * 30)
    try:
        validation_result = engine.process_validations(auto_approve=True)
        print(f"   📋 Pending processed: {validation_result.get('pending_count', 0)}")
        if validation_result.get('results'):
            auto_approved = sum(1 for r in validation_result['results'] if r.get('action') == 'auto_approved')
            manual_required = sum(1 for r in validation_result['results'] if r.get('action') == 'manual_review_required')
            print(f"   ✅ Auto-approved: {auto_approved}")
            print(f"   📋 Manual review required: {manual_required}")
    except Exception as e:
        print(f"   ❌ Validation processing failed: {e}")
    
    # Test 5: Pipeline Status Update
    print(f"\n🧪 Test 5: Final Pipeline Status")
    print("-" * 30)
    final_status = engine.get_pipeline_status()
    
    print(f"   📋 Database Status:")
    print(f"      • Database exists: {final_status['database']['exists']}")
    print(f"      • Database path: {final_status['database']['path']}")
    print(f"   📂 Extractors:")
    print(f"      • Available: {final_status['extractors']['available']}")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    successful_tests = sum(1 for result in test_results.values() if result.get('success', False))
    total_tests = len(test_results)
    
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    for extractor, result in test_results.items():
        status_icon = "✅" if result.get('success') else "❌"
        print(f"{status_icon} {extractor.upper()}: {result.get('stage', result.get('error', 'unknown'))}")
    
    # Final status
    if successful_tests == total_tests:
        print(f"\n🎉 All ETL workflows completed successfully!")
        print(f"🚀 Calgary Analytica standardized pipeline is ready for production!")
    else:
        print(f"\n⚠️  {total_tests - successful_tests} tests had issues - see details above")
    
    return test_results

def main():
    """Run the complete ETL pipeline test."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise for clean test output
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    # Run test
    test_results = test_complete_etl_pipeline()
    
    return test_results

if __name__ == "__main__":
    main()