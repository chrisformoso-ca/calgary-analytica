#!/usr/bin/env python3
"""
Calgary Analytica - Validation Helper
Interactive tool for reviewing and approving pending data extractions
"""

import argparse
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import shutil
from typing import List, Dict, Tuple

# Add project root for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config_manager import get_config

class ValidationHelper:
    """Interactive validation tool for pending data."""
    
    def __init__(self):
        self.config = get_config()
        self.pending_dir = self.config.get_pending_review_dir()
        self.approved_dir = self.config.get_approved_data_dir()
        self.rejected_dir = self.config.get_rejected_data_dir()
        
        # Ensure directories exist
        for dir_path in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def list_pending(self) -> List[Tuple[Path, Dict]]:
        """List all pending validation items with metadata."""
        pending_items = []
        
        # Check for directories (new format with validation reports)
        for item in self.pending_dir.iterdir():
            if item.is_dir():
                validation_report = item / "validation_report.json"
                if validation_report.exists():
                    with open(validation_report) as f:
                        report = json.load(f)
                    pending_items.append((item, report))
                else:
                    # Create basic report for directories without validation report
                    pending_items.append((item, {"confidence_score": None, "extracted_date": None}))
        
        # Check for standalone CSV files (legacy format)
        for csv_file in self.pending_dir.glob("*.csv"):
            pending_items.append((csv_file, {"type": "legacy_csv", "confidence_score": None}))
        
        return sorted(pending_items, key=lambda x: x[0].name)
    
    def preview_data(self, item_path: Path, rows: int = 5) -> pd.DataFrame:
        """Preview data from a pending item."""
        if item_path.is_dir():
            # Find CSV files in directory
            csv_files = list(item_path.glob("*.csv"))
            if csv_files:
                return pd.read_csv(csv_files[0]).head(rows)
        elif item_path.suffix == ".csv":
            return pd.read_csv(item_path).head(rows)
        return pd.DataFrame()
    
    def get_data_summary(self, item_path: Path) -> Dict:
        """Get summary statistics for pending data."""
        summary = {
            "file_count": 0,
            "total_records": 0,
            "data_types": [],
            "date_range": None
        }
        
        csv_files = []
        if item_path.is_dir():
            csv_files = list(item_path.glob("*.csv"))
        elif item_path.suffix == ".csv":
            csv_files = [item_path]
        
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            summary["file_count"] += 1
            summary["total_records"] += len(df)
            
            # Detect data type
            if 'property_type' in df.columns:
                if 'district' in df.columns:
                    summary["data_types"].append("housing_district")
                else:
                    summary["data_types"].append("housing_city")
            elif 'indicator_name' in df.columns:
                summary["data_types"].append("economic")
            elif 'crime_type' in df.columns:
                summary["data_types"].append("crime")
            
            # Get date range
            if 'date' in df.columns:
                dates = pd.to_datetime(df['date'])
                if summary["date_range"] is None:
                    summary["date_range"] = (dates.min(), dates.max())
                else:
                    summary["date_range"] = (
                        min(summary["date_range"][0], dates.min()),
                        max(summary["date_range"][1], dates.max())
                    )
        
        return summary
    
    def approve_item(self, item_path: Path, reason: str = None) -> bool:
        """Approve a pending item and move to approved directory."""
        try:
            dest = self.approved_dir / item_path.name
            shutil.move(str(item_path), str(dest))
            
            # Log approval
            log_entry = {
                "action": "approved",
                "item": item_path.name,
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            self._log_action(log_entry)
            
            return True
        except Exception as e:
            print(f"Error approving {item_path.name}: {e}")
            return False
    
    def reject_item(self, item_path: Path, reason: str) -> bool:
        """Reject a pending item and move to rejected directory."""
        try:
            dest = self.rejected_dir / item_path.name
            shutil.move(str(item_path), str(dest))
            
            # Log rejection
            log_entry = {
                "action": "rejected",
                "item": item_path.name,
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            self._log_action(log_entry)
            
            return True
        except Exception as e:
            print(f"Error rejecting {item_path.name}: {e}")
            return False
    
    def show_high_confidence(self, threshold: float = 0.90) -> List[Tuple[Path, float]]:
        """Show items with confidence above threshold (for manual review)."""
        high_confidence_items = []
        
        pending_items = self.list_pending()
        for item_path, report in pending_items:
            confidence = report.get("confidence_score")
            if confidence and confidence >= threshold:
                high_confidence_items.append((item_path, confidence))
        
        return sorted(high_confidence_items, key=lambda x: x[1], reverse=True)
    
    def _log_action(self, log_entry: Dict):
        """Log validation actions to audit log."""
        log_file = self.config.get_audit_logs_dir() / f"validation_{datetime.now().strftime('%Y%m%d')}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def interactive_review(self):
        """Interactive validation review process."""
        pending_items = self.list_pending()
        
        if not pending_items:
            print("✨ No pending validations!")
            return
        
        print(f"\n📋 Found {len(pending_items)} pending validation items")
        print("=" * 60)
        
        for i, (item_path, report) in enumerate(pending_items):
            print(f"\n[{i+1}/{len(pending_items)}] {item_path.name}")
            print("-" * 40)
            
            # Show metadata
            confidence = report.get("confidence_score")
            if confidence:
                print(f"Confidence: {confidence:.2%}")
            
            # Show data summary
            summary = self.get_data_summary(item_path)
            print(f"Records: {summary['total_records']}")
            print(f"Types: {', '.join(summary['data_types'])}")
            if summary["date_range"]:
                print(f"Date range: {summary['date_range'][0].strftime('%Y-%m-%d')} to {summary['date_range'][1].strftime('%Y-%m-%d')}")
            
            # Show preview
            print("\nData preview:")
            preview = self.preview_data(item_path, rows=3)
            if not preview.empty:
                print(preview.to_string())
            
            # Get user action
            while True:
                action = input("\nAction? [a]pprove / [r]eject / [s]kip / [q]uit: ").lower()
                
                if action == 'a':
                    if self.approve_item(item_path):
                        print("✅ Approved!")
                    break
                elif action == 'r':
                    reason = input("Rejection reason: ")
                    if self.reject_item(item_path, reason):
                        print("❌ Rejected!")
                    break
                elif action == 's':
                    print("⏭️  Skipped")
                    break
                elif action == 'q':
                    print("👋 Exiting...")
                    return
                else:
                    print("Invalid action. Please choose: a/r/s/q")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Calgary Analytica Validation Helper")
    parser.add_argument("--list", action="store_true", help="List pending validations")
    parser.add_argument("--high-confidence", action="store_true", help="Show high confidence items")
    parser.add_argument("--threshold", type=float, default=0.90, help="Confidence threshold")
    parser.add_argument("--interactive", action="store_true", help="Interactive review mode")
    parser.add_argument("--summary", action="store_true", help="Show validation summary")
    
    args = parser.parse_args()
    
    helper = ValidationHelper()
    
    if args.list:
        pending_items = helper.list_pending()
        print(f"\n📋 Pending Validations ({len(pending_items)} items):")
        print("=" * 60)
        for item_path, report in pending_items:
            confidence = report.get("confidence_score", "N/A")
            conf_str = f"{confidence:.2%}" if isinstance(confidence, float) else confidence
            print(f"  - {item_path.name} (confidence: {conf_str})")
    
    elif args.high_confidence:
        print(f"\n🎯 High Confidence Items (>= {args.threshold:.2%}):")
        high_conf_items = helper.show_high_confidence(args.threshold)
        if high_conf_items:
            for item_path, confidence in high_conf_items:
                print(f"  - {item_path.name} (confidence: {confidence:.2%})")
            print(f"\n💡 Use --interactive to review these items")
        else:
            print("  No high confidence items found")
    
    elif args.interactive:
        helper.interactive_review()
    
    elif args.summary:
        # Pipeline validation summary
        validation_status = helper.config.validate_data_pipeline()
        
        print("\n📊 Validation Pipeline Status")
        print("=" * 60)
        print(f"Database exists: {'✅' if validation_status['database_exists'] else '❌'}")
        print(f"Pending items: {validation_status['pending_count']}")
        print(f"Approved items: {validation_status['approved_count']}")
        
        print("\nValidation directories:")
        for name, exists in validation_status['validation_dirs'].items():
            print(f"  {name}: {'✅' if exists else '❌'}")
        
        print("\nExtractors:")
        for name, exists in validation_status['extractors'].items():
            print(f"  {name}: {'✅' if exists else '❌'}")
    
    else:
        # Default: show summary and suggest actions
        pending_count = len(helper.list_pending())
        print(f"\n📋 Validation Status: {pending_count} items pending")
        
        if pending_count > 0:
            print("\nSuggested actions:")
            print("  python validate_pending.py --list          # List all pending items")
            print("  python validate_pending.py --high-confidence  # Show high confidence items")
            print("  python validate_pending.py --interactive   # Manual review")
        else:
            print("✨ No pending validations!")


if __name__ == "__main__":
    main()