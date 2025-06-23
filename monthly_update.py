#!/usr/bin/env python3
"""
Calgary Analytica - Monthly Update Script
Simple workflow to update housing data when new CREB reports are available
"""

import argparse
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main monthly update workflow."""
    parser = argparse.ArgumentParser(description="Update Calgary housing data from CREB reports")
    parser.add_argument('--month', type=int, help='Month (1-12)')
    parser.add_argument('--year', type=int, help='Year (e.g., 2025)')
    parser.add_argument('--setup', action='store_true', help='Run initial setup')
    parser.add_argument('--import-data', dest='import_data', action='store_true', help='Import existing CSV data')
    
    # Phase 2 enhancements - modern pipeline integration
    parser.add_argument('--validate', action='store_true', help='Run validation workflow after extraction')
    parser.add_argument('--batch-months', help='Process multiple months (e.g., 2025-01:2025-06)')
    parser.add_argument('--source', choices=['creb', 'economic', 'crime', 'all'], default='creb',
                        help='Data source to process (default: creb)')
    parser.add_argument('--verbose', action='store_true', help='Detailed status reporting')
    parser.add_argument('--status', action='store_true', help='Show pipeline status without processing')
    
    args = parser.parse_args()
    
    # Paths
    base_dir = Path(__file__).parent
    data_engine_dir = base_dir / "data-engine"
    
    print("🏠 Calgary Analytica - Monthly Update")
    print("=" * 50)
    
    # Initialize data engine for modern pipeline features
    import sys
    sys.path.append(str(data_engine_dir))
    from core.data_engine import DataEngine
    
    engine = DataEngine(str(data_engine_dir))
    
    # Phase 2 enhancement: Pipeline status command
    if args.status:
        print("\n📊 Pipeline Status Report")
        print("-" * 40)
        
        status = engine.status()
        
        # Database status
        print(f"\n🗄️  Database Status:")
        if status['database']['database_exists']:
            print(f"  ✅ Database: {engine.database_path}")
            print(f"  📊 City records: {status['database']['city_records']}")
            print(f"  🏘️  District records: {status['database']['district_records']}")
        else:
            print(f"  ❌ Database not found: {engine.database_path}")
        
        # Pipeline status
        pipeline_status = engine.status()
        if pipeline_status:
            print(f"\n🔄 Pipeline Status:")
            print(f"  ⏳ Pending validations: {pipeline_status.get('pending_validations', 0)}")
            print(f"  🔧 Available extractors: {', '.join(pipeline_status.get('available_extractors', []))}")
        
        # Recent activity
        print(f"\n📈 Recent Activity:")
        print(f"  🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.verbose:
            print(f"\n🔧 Configuration:")
            try:
                # Use centralized config manager for path info
                import sys
                sys.path.insert(0, str(base_dir))
                from config.config_manager import get_config
                config = get_config()
                config_paths = config.get_all_paths()
                
                for name, path in config_paths.items():
                    exists = "✅" if Path(path).exists() else "❌"
                    print(f"  {exists} {name}: {path}")
            except Exception as e:
                print(f"  ❌ Config error: {e}")
        
        print(f"\n💡 Tip: Try the modern interface: /project:update status")
        return
    
    # Step 1: Setup (if needed)
    if args.setup:
        print("\n📊 Setting up database...")
        import subprocess
        import sys
        
        result = subprocess.run([sys.executable, str(data_engine_dir / "database/setup_database.py")])
        if result.returncode != 0:
            logger.error("Database setup failed!")
            return
    
    # Step 2: Import existing data (if needed)
    if args.import_data:
        print("\n📥 Importing existing data...")
        import subprocess
        import sys
        
        result = subprocess.run([sys.executable, str(data_engine_dir / "database/import_existing_data.py")])
        if result.returncode != 0:
            logger.error("Data import failed!")
            return
    
    # Step 3: Run extraction for specific month
    if args.month and args.year:
        print(f"\n🔄 Processing {args.month:02d}/{args.year} data...")
        
        # Check if PDF exists
        pdf_name = f"{args.month:02d}_{args.year}_Calgary_Monthly_Stats_Package.pdf"
        pdf_path = base_dir / "data-engine/data/raw/creb_pdfs" / pdf_name
        
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            print(f"\n❌ Please download {pdf_name} to data-engine/data/raw/creb_pdfs/ first")
            return
        
        # Use new data engine
        import sys
        sys.path.append(str(data_engine_dir))
        from core.data_engine import DataEngine
        
        engine = DataEngine(str(data_engine_dir))
        
        # Check database exists
        if not engine.database_path.exists():
            logger.error("Database not found. Run with --setup first!")
            return
        
        # Run extraction using data engine
        target_month = f"{args.year}-{args.month:02d}"
        
        # Phase 2 enhancement: Multi-source support
        sources_to_process = [args.source] if args.source != 'all' else ['creb', 'economic', 'crime']
        
        all_results = []
        for source in sources_to_process:
            if source == 'creb':
                results = engine.extract("creb", pdf_path=str(pdf_path), month=target_month)
            else:
                # For other sources, use standardized pipeline
                results = engine.run_etl_pipeline(source, month=target_month)
            
            all_results.append((source, results))
            
            if results['success']:
                print(f"\n✅ {source.upper()} Extraction complete!")
                print(f"  Method: {results.get('method', 'unknown')}")
                if 'records_found' in results:
                    print(f"  Records found: {results['records_found']}")
                if 'confidence' in results:
                    print(f"  Confidence: {results['confidence']:.2%}")
                if 'best_agent' in results:
                    print(f"  Best agent: {results['best_agent']}")
            else:
                print(f"\n❌ {source.upper()} Extraction failed!")
                if 'error' in results:
                    print(f"  Error: {results['error']}")
        
        # Phase 2 enhancement: Validation workflow
        if args.validate or any(r[1].get('confidence', 1.0) < 0.9 for r in all_results):
            print(f"\n🔍 Running validation workflow...")
            validation_results = engine.pipeline_manager.process_pending_validations(auto_approve=not args.validate)
            
            if validation_results:
                print(f"  ✅ Processed {validation_results.get('pending_processed', 0)} validations")
                print(f"  🤖 Auto-approved: {validation_results.get('auto_approved', 0)}")
                print(f"  👁️  Manual review required: {validation_results.get('manual_review_required', 0)}")
        
        # Summary
        successful_extractions = sum(1 for _, r in all_results if r['success'])
        if successful_extractions > 0:
            avg_confidence = sum(r[1].get('confidence', 1.0) for r in all_results if r[1]['success']) / successful_extractions
            if avg_confidence > 0.9:
                print(f"\n✨ Data looks good! Ready for dashboard.")
            else:
                print(f"\n⚠️  Please review extraction results (avg confidence: {avg_confidence:.2%})")
        else:
            print(f"\n❌ All extractions failed!")
        
        # Show engine status
        status = engine.status()
        print(f"\n📊 Database Status:")
        if status['database']['database_exists']:
            print(f"  City records: {status['database']['city_records']}")
            print(f"  District records: {status['database']['district_records']}")
        else:
            print("  Database not found")
    
    # Phase 2 enhancement: Batch processing
    elif args.batch_months:
        print(f"\n🔄 Batch Processing: {args.batch_months}")
        
        try:
            start_month, end_month = args.batch_months.split(':')
            start_year, start_mon = map(int, start_month.split('-'))
            end_year, end_mon = map(int, end_month.split('-'))
            
            months_to_process = []
            current_year, current_month = start_year, start_mon
            
            while (current_year, current_month) <= (end_year, end_mon):
                months_to_process.append((current_year, current_month))
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            
            print(f"Processing {len(months_to_process)} months...")
            
            for year, month in months_to_process:
                print(f"\n📅 Processing {month:02d}/{year}...")
                
                # Check for PDF
                pdf_name = f"{month:02d}_{year}_Calgary_Monthly_Stats_Package.pdf"
                pdf_path = base_dir / "data-engine/data/raw/creb_pdfs" / pdf_name
                
                if pdf_path.exists():
                    target_month = f"{year}-{month:02d}"
                    results = engine.extract("creb", pdf_path=str(pdf_path), month=target_month)
                    
                    if results['success']:
                        confidence = results.get('confidence', 1.0)
                        print(f"  ✅ Success (confidence: {confidence:.2%})")
                    else:
                        print(f"  ❌ Failed: {results.get('error', 'Unknown error')}")
                else:
                    print(f"  ⏭️  Skipped (PDF not found)")
            
            print(f"\n✨ Batch processing complete!")
            
        except ValueError:
            print(f"❌ Invalid batch format. Use: YYYY-MM:YYYY-MM (e.g., 2025-01:2025-06)")
    
    else:
        # Show help
        print("\nUsage examples:")
        print("  # First time setup:")
        print("  python monthly_update.py --setup --import-data")
        print()
        print("  # Monthly update (e.g., May 2025):")
        print("  python monthly_update.py --month 5 --year 2025")
        print()
        print("  # Phase 2 enhancements:")
        print("  python monthly_update.py --month 5 --year 2025 --validate")
        print("  python monthly_update.py --batch-months 2025-01:2025-06")
        print("  python monthly_update.py --source economic --month 5 --year 2025")
        print("  python monthly_update.py --status --verbose")
        print()
        print("Workflow:")
        print("  1. Download new CREB PDF to data-engine/data/raw/creb_pdfs/")
        print("  2. Run this script with --month and --year")
        print("  3. Check validation results")
        print("  4. Dashboard updates automatically")
        print()
        print("💡 Tip: Use /data:extract creb 2025-05 for modern slash command interface")

if __name__ == "__main__":
    main()