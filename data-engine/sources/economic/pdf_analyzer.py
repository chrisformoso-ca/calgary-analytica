#!/usr/bin/env python3
"""
Calgary Economic Analysis PDF Processor
Processes PDF economic analysis reports (2009-2015) and extracts key insights
"""

import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import re
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalgaryEconomicPDFAnalyzer:
    """Analyzes Calgary economic analysis PDF reports."""
    
    def __init__(self, raw_data_path: str = None):
        self.raw_data_path = Path(raw_data_path) if raw_data_path else Path(__file__).parent.parent.parent / "data/raw/calgary_economic_indicators"
        
        # Key economic themes to extract
        self.economic_themes = {
            'employment': {
                'keywords': ['employment', 'unemployment', 'job', 'labour', 'labor', 'workforce'],
                'sentiment_words': ['increase', 'decrease', 'growth', 'decline', 'stable', 'volatile']
            },
            'housing': {
                'keywords': ['housing', 'residential', 'home', 'real estate', 'construction', 'building'],
                'sentiment_words': ['boom', 'bust', 'stable', 'growth', 'decline', 'recovery']
            },
            'population': {
                'keywords': ['population', 'migration', 'demographic', 'residents'],
                'sentiment_words': ['growth', 'decline', 'influx', 'outflow', 'stable']
            },
            'economy': {
                'keywords': ['economy', 'economic', 'gdp', 'recession', 'recovery', 'expansion'],
                'sentiment_words': ['growth', 'contraction', 'stable', 'volatile', 'strong', 'weak']
            },
            'inflation': {
                'keywords': ['inflation', 'price', 'cost', 'cpi', 'consumer price'],
                'sentiment_words': ['rising', 'falling', 'stable', 'high', 'low', 'moderate']
            }
        }
    
    def find_pdf_files(self) -> List[Path]:
        """Find all PDF economic analysis files."""
        pdf_files = []
        
        # Look for PDF files with economic analysis patterns
        patterns = [
            "*economic-analysis*.pdf",
            "*Economic-Analysis*.pdf",
            "*current-economic-analysis*.pdf"
        ]
        
        for pattern in patterns:
            pdf_files.extend(self.raw_data_path.glob(pattern))
        
        # Sort by filename to process chronologically
        pdf_files.sort()
        
        logger.info(f"Found {len(pdf_files)} PDF economic analysis files")
        return pdf_files
    
    def extract_date_from_filename(self, filename: str) -> Optional[Tuple[int, int]]:
        """Extract year and month from PDF filename."""
        
        # Pattern: current-economic-analysis-YYYY-MM.pdf
        match = re.search(r'(\d{4})-(\d{1,2})', filename)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            return year, month
        
        # Alternative patterns for different naming conventions
        patterns = [
            r'(\d{4})[-_](\d{1,2})',  # 2015-07 or 2015_07
            r'(\d{1,2})[-_](\d{4})',  # 07-2015 or 07_2015 (month first)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.group(1)) == 4:  # Year first
                    year, month = int(match.group(1)), int(match.group(2))
                else:  # Month first
                    month, year = int(match.group(1)), int(match.group(2))
                
                if 1 <= month <= 12 and 2000 <= year <= 2030:
                    return year, month
        
        logger.warning(f"Could not extract date from filename: {filename}")
        return None
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract all text from a PDF file."""
        
        try:
            full_text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += f"\n--- Page {page_num + 1} ---\n"
                            full_text += page_text
                    except Exception as e:
                        logger.debug(f"Error extracting page {page_num + 1}: {e}")
                        continue
            
            if full_text.strip():
                return full_text
            else:
                logger.warning(f"No text extracted from {pdf_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return None
    
    def analyze_economic_text(self, text: str, filename: str) -> Dict[str, Any]:
        """Analyze extracted text for economic insights."""
        
        if not text:
            return {}
        
        analysis = {
            'filename': filename,
            'text_length': len(text),
            'themes': {},
            'key_insights': [],
            'economic_outlook': '',
            'housing_correlation': '',
            'confidence_score': 0.0
        }
        
        # Analyze each economic theme
        for theme, config in self.economic_themes.items():
            theme_analysis = self._analyze_theme(text, theme, config)
            analysis['themes'][theme] = theme_analysis
        
        # Extract key insights using pattern matching
        analysis['key_insights'] = self._extract_key_insights(text)
        
        # Extract economic outlook
        analysis['economic_outlook'] = self._extract_outlook(text)
        
        # Extract housing market correlations
        analysis['housing_correlation'] = self._extract_housing_correlation(text)
        
        # Calculate overall confidence score
        analysis['confidence_score'] = self._calculate_confidence_score(analysis)
        
        return analysis
    
    def _analyze_theme(self, text: str, theme: str, config: Dict) -> Dict[str, Any]:
        """Analyze a specific economic theme in the text."""
        
        theme_data = {
            'mentions': 0,
            'sentiment': 'neutral',
            'key_sentences': [],
            'relevance_score': 0.0
        }
        
        text_lower = text.lower()
        sentences = re.split(r'[.!?]+', text)
        
        # Count keyword mentions and find relevant sentences
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains theme keywords
            keyword_matches = sum(1 for keyword in config['keywords'] if keyword in sentence_lower)
            
            if keyword_matches > 0:
                theme_data['mentions'] += keyword_matches
                
                # Store relevant sentences (up to 3 most relevant)
                if len(theme_data['key_sentences']) < 3:
                    theme_data['key_sentences'].append(sentence.strip())
                
                # Analyze sentiment in this sentence
                sentiment_scores = []
                for sentiment_word in config['sentiment_words']:
                    if sentiment_word in sentence_lower:
                        # Simple sentiment scoring
                        if sentiment_word in ['growth', 'increase', 'boom', 'strong', 'recovery']:
                            sentiment_scores.append(1)
                        elif sentiment_word in ['decline', 'decrease', 'bust', 'weak', 'contraction']:
                            sentiment_scores.append(-1)
                        else:
                            sentiment_scores.append(0)
                
                # Determine overall sentiment for this theme
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    if avg_sentiment > 0.3:
                        theme_data['sentiment'] = 'positive'
                    elif avg_sentiment < -0.3:
                        theme_data['sentiment'] = 'negative'
        
        # Calculate relevance score
        theme_data['relevance_score'] = min(theme_data['mentions'] / 10.0, 1.0)
        
        return theme_data
    
    def _extract_key_insights(self, text: str) -> List[str]:
        """Extract key economic insights from the text."""
        
        insights = []
        
        # Look for summary or conclusion sections
        sections = re.split(r'\n\s*(?:summary|conclusion|outlook|highlights)\s*\n', text, flags=re.IGNORECASE)
        
        if len(sections) > 1:
            # Take the last section (likely conclusion/summary)
            summary_section = sections[-1]
            
            # Extract bullet points or numbered items
            bullet_pattern = r'[\n\r]\s*[•\-\*\d+\.]\s*([^•\-\*\d\n\r]+)'
            bullets = re.findall(bullet_pattern, summary_section)
            
            for bullet in bullets[:5]:  # Take up to 5 key points
                cleaned = bullet.strip()
                if len(cleaned) > 20 and len(cleaned) < 200:  # Reasonable length
                    insights.append(cleaned)
        
        # If no structured insights found, extract key sentences
        if not insights:
            sentences = re.split(r'[.!?]+', text)
            
            # Look for sentences with economic indicators
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['economy', 'economic', 'employment', 'housing', 'growth']):
                    if 50 < len(sentence) < 150:  # Good length for insight
                        insights.append(sentence.strip())
                        if len(insights) >= 3:
                            break
        
        return insights
    
    def _extract_outlook(self, text: str) -> str:
        """Extract economic outlook from the text."""
        
        # Look for outlook sections
        outlook_patterns = [
            r'outlook[:\s]*([^\.]+\.)',
            r'forecast[:\s]*([^\.]+\.)',
            r'expect[^\.]*([^\.]+\.)',
            r'going forward[^\.]*([^\.]+\.)'
        ]
        
        for pattern in outlook_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        # Fallback: look for future-oriented sentences
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['will', 'expect', 'forecast', 'outlook', 'future']):
                if 30 < len(sentence) < 200:
                    return sentence.strip()
        
        return ""
    
    def _extract_housing_correlation(self, text: str) -> str:
        """Extract housing market correlations from economic text."""
        
        # Look for sentences that mention both housing and economic factors
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            has_housing = any(word in sentence_lower for word in ['housing', 'residential', 'home', 'real estate'])
            has_economic = any(word in sentence_lower for word in ['economy', 'employment', 'interest', 'inflation'])
            
            if has_housing and has_economic and len(sentence) > 40:
                return sentence.strip()
        
        return ""
    
    def _calculate_confidence_score(self, analysis: Dict) -> float:
        """Calculate confidence score for the analysis."""
        
        score = 0.0
        
        # Base score from text length
        if analysis['text_length'] > 1000:
            score += 0.3
        elif analysis['text_length'] > 500:
            score += 0.2
        else:
            score += 0.1
        
        # Score from theme coverage
        themes_with_data = sum(1 for theme in analysis['themes'].values() if theme['mentions'] > 0)
        score += (themes_with_data / len(self.economic_themes)) * 0.4
        
        # Score from insights found
        if analysis['key_insights']:
            score += min(len(analysis['key_insights']) / 5.0, 0.2)
        
        # Score from outlook and correlations
        if analysis['economic_outlook']:
            score += 0.05
        if analysis['housing_correlation']:
            score += 0.05
        
        return min(score, 1.0)
    
    def process_pdf_file(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """Process a single PDF file and extract economic analysis."""
        
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        # Extract date from filename
        date_info = self.extract_date_from_filename(pdf_path.name)
        if not date_info:
            logger.error(f"Could not extract date from {pdf_path.name}")
            return None
        
        year, month = date_info
        quarter = f"Q{(month - 1) // 3 + 1}"
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.error(f"No text extracted from {pdf_path.name}")
            return None
        
        # Analyze the text
        analysis = self.analyze_economic_text(text, pdf_path.name)
        
        # Create record for database
        record = {
            'quarter': quarter,
            'year': year,
            'key_insights': json.dumps(analysis['key_insights']),
            'economic_outlook': analysis['economic_outlook'],
            'housing_correlation': analysis['housing_correlation'],
            'employment_trends': json.dumps(analysis['themes'].get('employment', {})),
            'population_trends': json.dumps(analysis['themes'].get('population', {})),
            'source_pdf': pdf_path.name,
            'confidence_score': analysis['confidence_score'],
            'validation_status': 'pending'
        }
        
        logger.info(f"✅ Processed {pdf_path.name}: confidence {analysis['confidence_score']:.2f}")
        return record
    
    def process_all_pdfs(self, year_range: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """Process all PDF economic analysis files."""
        
        logger.info("📄 Starting PDF economic analysis extraction")
        
        # Find all PDF files
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            return {
                'success': False,
                'error': 'No PDF files found',
                'files_processed': 0
            }
        
        # Filter by year range if specified
        if year_range:
            filtered_files = []
            for file_path in pdf_files:
                date_info = self.extract_date_from_filename(file_path.name)
                if date_info and year_range[0] <= date_info[0] <= year_range[1]:
                    filtered_files.append(file_path)
            pdf_files = filtered_files
        
        # Process files
        records = []
        processed_files = 0
        failed_files = []
        
        for pdf_path in pdf_files:
            try:
                record = self.process_pdf_file(pdf_path)
                
                if record:
                    records.append(record)
                    processed_files += 1
                else:
                    failed_files.append(str(pdf_path))
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
                failed_files.append(str(pdf_path))
        
        logger.info(f"📊 PDF analysis complete:")
        logger.info(f"  Files processed: {processed_files}/{len(pdf_files)}")
        logger.info(f"  Analysis records: {len(records)}")
        logger.info(f"  Failed files: {len(failed_files)}")
        
        return {
            'success': True,
            'records': records,
            'files_processed': processed_files,
            'total_files': len(pdf_files),
            'failed_files': failed_files
        }
    
    def save_to_database(self, records: List[Dict], db_path: str) -> bool:
        """Save analysis records to SQLite database."""
        
        if not records:
            logger.warning("No records to save")
            return True
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert records
            inserted = 0
            for record in records:
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO economic_analysis_quarterly 
                    (quarter, year, key_insights, economic_outlook, housing_correlation,
                     employment_trends, population_trends, source_pdf, confidence_score, validation_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['quarter'],
                        record['year'],
                        record['key_insights'],
                        record['economic_outlook'],
                        record['housing_correlation'],
                        record['employment_trends'],
                        record['population_trends'],
                        record['source_pdf'],
                        record['confidence_score'],
                        record['validation_status']
                    ))
                    inserted += 1
                    
                except sqlite3.Error as e:
                    logger.error(f"Error inserting record: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Saved {inserted} economic analysis records to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            return False


def main():
    """Test the PDF analyzer."""
    
    analyzer = CalgaryEconomicPDFAnalyzer()
    
    # Process all PDF files
    result = analyzer.process_all_pdfs()
    
    if result['success']:
        print(f"✅ PDF analysis completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Analysis records: {len(result['records'])}")
        
        # Show sample records
        if result['records']:
            print(f"\nSample analysis:")
            for record in result['records'][:3]:
                print(f"  {record['year']} {record['quarter']} - Confidence: {record['confidence_score']:.2f}")
                if record['economic_outlook']:
                    print(f"    Outlook: {record['economic_outlook'][:100]}...")
    else:
        print(f"❌ PDF analysis failed: {result.get('error')}")


if __name__ == "__main__":
    main()