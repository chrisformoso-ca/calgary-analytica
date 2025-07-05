#!/usr/bin/env python3
"""
Generate All Dashboard Exports
Main runner script for monthly data export automation
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging
import json
from typing import Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('export_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DashboardExportRunner:
    """Orchestrate all dashboard data exports."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.data_dir = self.script_dir.parent / 'data'
        self.archive_dir = self.script_dir.parent / 'archive'
        
        # Define export scripts in order of execution
        self.export_scripts = [
            ('generate_market_overview.py', 'Market Overview'),
            ('generate_economic_indicators.py', 'Economic Indicators'),
            ('generate_district_data.py', 'District Data'),
            ('generate_rate_data.py', 'Rate Data'),
            ('generate_metadata.py', 'Metadata'),
            # Additional data exports (optional use)
            ('generate_service_requests.py', 'Service Requests (311)'),
            ('generate_rental_market.py', 'Rental Market'),
            ('generate_crime_statistics.py', 'Crime Statistics')
        ]
        
        self.results = []
    
    def run_script(self, script_name: str, description: str) -> Tuple[bool, str]:
        """Run a single export script."""
        script_path = self.script_dir / script_name
        
        if not script_path.exists():
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"🚀 Running {description}...")
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(self.script_dir)
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                return True, result.stdout
            else:
                error_msg = f"❌ {description} failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"❌ Error running {description}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if database exists
        db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        if not db_path.exists():
            logger.error(f"❌ Database not found: {db_path}")
            return False
        
        # Check if all scripts exist
        for script_name, _ in self.export_scripts:
            script_path = self.script_dir / script_name
            if not script_path.exists():
                logger.error(f"❌ Script not found: {script_path}")
                return False
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ All prerequisites met")
        return True
    
    def create_summary_report(self) -> Dict[str, any]:
        """Create a summary report of the export run."""
        successful = sum(1 for success, _ in self.results if success)
        failed = len(self.results) - successful
        
        summary = {
            'run_date': datetime.now().isoformat(),
            'total_exports': len(self.results),
            'successful': successful,
            'failed': failed,
            'details': []
        }
        
        for i, ((script, desc), (success, output)) in enumerate(zip(self.export_scripts, self.results)):
            summary['details'].append({
                'export': desc,
                'script': script,
                'success': success,
                'order': i + 1
            })
        
        # Check generated files
        generated_files = []
        for json_file in self.data_dir.glob('*.json'):
            stat = json_file.stat()
            generated_files.append({
                'file': json_file.name,
                'size_bytes': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        summary['generated_files'] = generated_files
        
        return summary
    
    def save_summary(self, summary: Dict[str, any]) -> None:
        """Save the summary report."""
        # Create monthly archive directory
        archive_month_dir = self.archive_dir / datetime.now().strftime('%Y-%m')
        archive_month_dir.mkdir(parents=True, exist_ok=True)
        
        # Save summary
        summary_path = archive_month_dir / f"export_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📄 Summary saved to: {summary_path}")
    
    def run_all_exports(self) -> bool:
        """Run all export scripts in sequence."""
        logger.info("="*70)
        logger.info("🎯 CALGARY HOUSING DASHBOARD - MONTHLY DATA EXPORT")
        logger.info("="*70)
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites check failed. Aborting.")
            return False
        
        # Run each export script
        for script_name, description in self.export_scripts:
            success, output = self.run_script(script_name, description)
            self.results.append((success, output))
            
            if not success and script_name != 'generate_metadata.py':
                # Don't stop for metadata failures
                logger.warning(f"⚠️  {description} failed, but continuing...")
        
        # Create and save summary
        summary = self.create_summary_report()
        self.save_summary(summary)
        
        # Print final summary
        logger.info("\n" + "="*70)
        logger.info("📊 EXPORT SUMMARY")
        logger.info("="*70)
        logger.info(f"Total exports: {summary['total_exports']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        
        if summary['generated_files']:
            logger.info("\n📁 Generated Files:")
            for file_info in summary['generated_files']:
                logger.info(f"  - {file_info['file']} ({file_info['size_bytes']:,} bytes)")
        
        logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        return summary['failed'] == 0
    
    def run_single_export(self, export_name: str) -> bool:
        """Run a single export by name."""
        # Find the matching script
        matching_script = None
        for script_name, description in self.export_scripts:
            if export_name in script_name or export_name.lower() in description.lower():
                matching_script = (script_name, description)
                break
        
        if not matching_script:
            logger.error(f"❌ No export found matching: {export_name}")
            logger.info("Available exports:")
            for script_name, description in self.export_scripts:
                logger.info(f"  - {script_name}: {description}")
            return False
        
        script_name, description = matching_script
        success, output = self.run_script(script_name, description)
        
        if success:
            logger.info(f"✅ {description} completed successfully")
        
        return success

def main():
    """Main entry point for export runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Calgary Housing Dashboard data exports')
    parser.add_argument(
        '--single', 
        type=str, 
        help='Run a single export (e.g., "market" or "economic")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be run without executing'
    )
    
    args = parser.parse_args()
    
    runner = DashboardExportRunner()
    
    if args.dry_run:
        print("🔍 DRY RUN - Exports that would be generated:")
        for script_name, description in runner.export_scripts:
            print(f"  - {description} ({script_name})")
        print(f"\n📂 Output directory: {runner.data_dir}")
        print(f"📦 Archive directory: {runner.archive_dir}")
        return
    
    if args.single:
        # Run single export
        success = runner.run_single_export(args.single)
        sys.exit(0 if success else 1)
    else:
        # Run all exports
        success = runner.run_all_exports()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()