#!/usr/bin/env python3
"""
Calgary CREB Agent Crew System
Multi-agent extraction with confidence voting and pattern learning
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd

# Import existing extractor
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "sources" / "creb"))
from extractor import CalgaryDataUpdater

logger = logging.getLogger(__name__)

class ExtractionAgent:
    """Base class for extraction agents."""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.success_count = 0
        self.total_attempts = 0
    
    def extract(self, pdf_path: Path, target_month: str) -> Dict[str, Any]:
        """Extract data from PDF. Returns dict with confidence, data, and metadata."""
        raise NotImplementedError
    
    def get_success_rate(self) -> float:
        """Calculate success rate for this agent."""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts
    
    def update_stats(self, success: bool):
        """Update success statistics."""
        self.total_attempts += 1
        if success:
            self.success_count += 1

class PDFPlumberAgent(ExtractionAgent):
    """Enhanced pdfplumber agent with improved parsing."""
    
    def __init__(self):
        super().__init__("PDFPlumber", "2.0")
        self.extractor = None
    
    def extract(self, pdf_path: Path, target_month: str) -> Dict[str, Any]:
        """Extract using enhanced pdfplumber method."""
        
        try:
            # Initialize extractor
            if not self.extractor:
                csv_path = pdf_path.parent.parent.parent / "data/processed/Calgary_CREB_Data.csv"
                district_csv_path = pdf_path.parent.parent.parent / "data/processed/calgary_housing_master_dataset.csv"
                self.extractor = CalgaryDataUpdater(
                    str(csv_path),
                    str(pdf_path.parent),
                    str(district_csv_path)
                )
            
            # Extract district data
            district_df = self.extractor.extract_district_data_from_pdf(pdf_path, target_month)
            
            if district_df.empty:
                self.update_stats(False)
                return {
                    "agent": self.name,
                    "success": False,
                    "confidence": 0.0,
                    "data": None,
                    "error": "No district data extracted",
                    "records_found": 0
                }
            
            # Calculate confidence based on expected records
            expected_records = 32  # 8 districts × 4 property types
            confidence = min(len(district_df) / expected_records, 1.0)
            
            # Additional quality checks
            if confidence >= 0.8:  # At least 80% of expected records
                # Check price reasonableness
                avg_price = district_df['benchmark_price'].mean()
                if 200000 <= avg_price <= 1500000:  # Reasonable Calgary price range
                    confidence = min(confidence + 0.1, 1.0)
            
            success = confidence >= 0.7
            self.update_stats(success)
            
            return {
                "agent": self.name,
                "success": success,
                "confidence": confidence,
                "data": district_df,
                "records_found": len(district_df),
                "avg_price": district_df['benchmark_price'].mean(),
                "extraction_method": "enhanced_pdfplumber_v2"
            }
            
        except Exception as e:
            self.update_stats(False)
            logger.error(f"PDFPlumberAgent error: {e}")
            return {
                "agent": self.name,
                "success": False,
                "confidence": 0.0,
                "data": None,
                "error": str(e),
                "records_found": 0
            }

class FirecrawlAgent(ExtractionAgent):
    """Firecrawl structured extraction agent."""
    
    def __init__(self):
        super().__init__("Firecrawl", "1.0")
    
    def extract(self, pdf_path: Path, target_month: str) -> Dict[str, Any]:
        """Extract using Firecrawl structured extraction."""
        
        try:
            # TODO: Implement Firecrawl integration
            # For now, return placeholder result
            
            self.update_stats(False)
            return {
                "agent": self.name,
                "success": False,
                "confidence": 0.0,
                "data": None,
                "error": "Firecrawl agent not yet implemented",
                "records_found": 0,
                "extraction_method": "firecrawl_structured"
            }
            
        except Exception as e:
            self.update_stats(False)
            logger.error(f"FirecrawlAgent error: {e}")
            return {
                "agent": self.name,
                "success": False,
                "confidence": 0.0,
                "data": None,
                "error": str(e),
                "records_found": 0
            }

class OCRAgent(ExtractionAgent):
    """OCR fallback agent for difficult PDFs."""
    
    def __init__(self):
        super().__init__("OCR", "1.0")
    
    def extract(self, pdf_path: Path, target_month: str) -> Dict[str, Any]:
        """Extract using OCR methods."""
        
        try:
            # TODO: Implement OCR extraction (pytesseract + pdf2image)
            # For now, return placeholder result
            
            self.update_stats(False)
            return {
                "agent": self.name,
                "success": False,
                "confidence": 0.0,
                "data": None,
                "error": "OCR agent not yet implemented",
                "records_found": 0,
                "extraction_method": "ocr_tesseract"
            }
            
        except Exception as e:
            self.update_stats(False)
            logger.error(f"OCRAgent error: {e}")
            return {
                "agent": self.name,
                "success": False,
                "confidence": 0.0,
                "data": None,
                "error": str(e),
                "records_found": 0
            }

class AgentCrew:
    """Orchestrates multiple extraction agents."""
    
    def __init__(self, pattern_storage_path: str = None):
        self.agents = [
            PDFPlumberAgent(),
            FirecrawlAgent(),
            OCRAgent()
        ]
        
        self.pattern_storage_path = Path(pattern_storage_path) if pattern_storage_path else Path("patterns.json")
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load successful extraction patterns."""
        if self.pattern_storage_path.exists():
            try:
                with open(self.pattern_storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load patterns: {e}")
        
        return {"successful_extractions": [], "agent_stats": {}}
    
    def _save_patterns(self):
        """Save successful extraction patterns."""
        try:
            # Ensure directory exists
            self.pattern_storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.pattern_storage_path, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save patterns: {e}")
    
    def extract_with_crew(self, pdf_path: Path, target_month: str, 
                         confidence_threshold: float = 0.9) -> Dict[str, Any]:
        """Run extraction with multiple agents and return best result."""
        
        logger.info(f"🤖 Agent crew starting extraction for {pdf_path.name}")
        
        results = []
        
        # Run agents in parallel (for now, sequentially)
        for agent in self.agents:
            logger.info(f"🔄 Running {agent.name} agent...")
            result = agent.extract(pdf_path, target_month)
            results.append(result)
            
            logger.info(f"📊 {agent.name}: {result['confidence']:.2f} confidence, "
                       f"{result['records_found']} records")
            
            # Early exit if we have high confidence
            if result['success'] and result['confidence'] >= confidence_threshold:
                logger.info(f"✅ {agent.name} achieved high confidence, using result")
                break
        
        # Vote for best result
        best_result = self._vote_for_best_result(results)
        
        # Save successful pattern
        if best_result['success']:
            self._record_successful_extraction(pdf_path.name, target_month, best_result)
        
        # Update agent statistics
        self._update_agent_stats()
        
        return best_result
    
    def _vote_for_best_result(self, results: List[Dict]) -> Dict[str, Any]:
        """Vote for the best extraction result."""
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            # No successful extractions
            logger.warning("❌ No agent succeeded in extraction")
            return {
                "crew_result": "all_failed",
                "success": False,
                "best_agent": None,
                "confidence": 0.0,
                "data": None,
                "all_results": results
            }
        
        # Choose result with highest confidence
        best_result = max(successful_results, key=lambda x: x['confidence'])
        
        logger.info(f"🏆 Best result: {best_result['agent']} with "
                   f"{best_result['confidence']:.2f} confidence")
        
        return {
            "crew_result": "success",
            "success": True,
            "best_agent": best_result['agent'],
            "confidence": best_result['confidence'],
            "data": best_result['data'],
            "records_found": best_result['records_found'],
            "extraction_method": best_result.get('extraction_method', 'unknown'),
            "all_results": results
        }
    
    def _record_successful_extraction(self, filename: str, target_month: str, result: Dict):
        """Record successful extraction pattern."""
        
        pattern = {
            "filename": filename,
            "target_month": target_month,
            "agent": result['best_agent'],
            "confidence": result['confidence'],
            "records_found": result['records_found'],
            "extraction_method": result.get('extraction_method'),
            "timestamp": datetime.now().isoformat()
        }
        
        self.patterns["successful_extractions"].append(pattern)
        
        # Keep only last 50 successful extractions
        if len(self.patterns["successful_extractions"]) > 50:
            self.patterns["successful_extractions"] = self.patterns["successful_extractions"][-50:]
        
        self._save_patterns()
        logger.info(f"💾 Recorded successful pattern for {filename}")
    
    def _update_agent_stats(self):
        """Update agent statistics in patterns."""
        
        stats = {}
        for agent in self.agents:
            stats[agent.name] = {
                "success_rate": agent.get_success_rate(),
                "total_attempts": agent.total_attempts,
                "success_count": agent.success_count
            }
        
        self.patterns["agent_stats"] = stats
        self._save_patterns()
    
    def get_agent_performance(self) -> Dict[str, Dict]:
        """Get performance statistics for all agents."""
        return self.patterns.get("agent_stats", {})
    
    def recommend_agent(self, filename: str) -> Optional[str]:
        """Recommend best agent based on historical patterns."""
        
        # Look for similar files
        successful = self.patterns.get("successful_extractions", [])
        
        # Simple heuristic: prefer agent that worked for similar month/year
        month_year = filename[:7]  # e.g., "05_2025"
        
        matching_patterns = [p for p in successful if p["filename"].startswith(month_year)]
        
        if matching_patterns:
            # Return most successful agent for this pattern
            agent_counts = {}
            for pattern in matching_patterns:
                agent = pattern["agent"]
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            best_agent = max(agent_counts.items(), key=lambda x: x[1])
            return best_agent[0]
        
        # Fallback to best overall performer
        stats = self.get_agent_performance()
        if stats:
            best_overall = max(stats.items(), key=lambda x: x[1].get("success_rate", 0))
            return best_overall[0]
        
        return None

def main():
    """Test the agent crew system."""
    
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    crew = AgentCrew("../validation/patterns/patterns.json")
    
    pdf_path = Path("../data/raw/creb_pdfs/05_2025_Calgary_Monthly_Stats_Package.pdf")
    target_month = "2025-05"
    
    if pdf_path.exists():
        result = crew.extract_with_crew(pdf_path, target_month)
        
        print(f"\n🎯 Agent Crew Results:")
        print(f"Status: {result['crew_result']}")
        print(f"Best Agent: {result['best_agent']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Records Found: {result.get('records_found', 0)}")
        
        if result['data'] is not None:
            print(f"Sample data: {len(result['data'])} records")
            
        # Show agent performance
        print(f"\n📈 Agent Performance:")
        performance = crew.get_agent_performance()
        for agent_name, stats in performance.items():
            print(f"  {agent_name}: {stats['success_rate']:.2f} success rate "
                  f"({stats['success_count']}/{stats['total_attempts']})")
    else:
        print(f"❌ PDF not found: {pdf_path}")

if __name__ == "__main__":
    main()