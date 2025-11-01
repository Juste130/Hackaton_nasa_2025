"""
NASA Bioscience Publications Extractor
Extract data from 608 publications from NCBI/PubMed Central
and insert them directly into PostgreSQL
"""

import requests
import xml.etree.ElementTree as ET
import time
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import pandas as pd
from src.database.client import DatabaseClient
from src.data_pipeline.extractors.section_extractor import IntelligentSectionExtractorModule

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = "amrromuald234@gmail.com"  # NCBI requires an email for tracking

#api key from .env file
from core.config import NCBI_API_KEY
API_KEY = NCBI_API_KEY


@dataclass
class Author:
    firstname: str
    lastname: str
    affiliation: Optional[str] = None

@dataclass
class Publication:
    pmcid: str
    pmid: Optional[str]
    title: str
    abstract: str
    authors: List[Dict]
    publication_date: str
    journal: str
    doi: Optional[str]
    keywords: List[str]
    full_text_sections: Dict[str, str]  # {section_name: content}
    full_text_content: Optional[str]  # NEW - Added missing field
    mesh_terms: List[str]  # Medical Subject Headings
    references: List[str]  # Cited PMIDs

    def to_dict(self):
        return asdict(self)


class NCBIExtractor:
    def __init__(self, email: str, api_key: Optional[str] = None, db_client: Optional[DatabaseClient] = None):
        self.email = email
        self.api_key = api_key
        self.rate_limit = 0.34 if not api_key else 0.3  # seconds between requests
        self.db_client = db_client
        
        # Initialize DSPy section extraction module
        self.section_extractor_dspy = IntelligentSectionExtractorModule()

    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """Make a request to NCBI API with rate limiting"""
        params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key

        url = f"{NCBI_BASE_URL}{endpoint}"
        time.sleep(self.rate_limit)

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error {endpoint}: {e}")
            raise

    async def check_publication_exists(self, pmcid: str) -> bool:
        """Check if a publication already exists in database"""
        if not self.db_client:
            return False
        
        existing = await self.db_client.get_publication_by_pmcid(pmcid)
        return existing is not None

    def _clean_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Clean and validate text"""
        if not text:
            return ""
        
        # Clean control characters and multiple spaces
        cleaned = ' '.join(text.strip().split())
        
        # Limit length if specified
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned

    def _clean_and_deduplicate_keywords(self, keywords_list: List[str]) -> List[str]:
        """Clean and deduplicate keywords"""
        unique_keywords = set()
        
        for keyword in keywords_list:
            if keyword and isinstance(keyword, str):
                # Clean
                cleaned = self._clean_text(keyword.strip(), 255)
                if cleaned and len(cleaned) > 1:  # At least 2 characters
                    # Normalize for deduplication
                    normalized = cleaned.lower()
                    unique_keywords.add(normalized)
        
        return list(unique_keywords)

    def _extract_text_sections(self, body_element) -> Dict[str, str]:
        """
        Extract text sections with multiple strategies including DSPy
        """
        sections = {}
        
        if body_element is None:
            return sections
        
        # Strategy 1: Explicit sections with titles
        explicit_sections = body_element.findall('.//sec')
        
        if explicit_sections and len(explicit_sections) >= 2:
            logger.info("Using explicit sections")
            for i, sec in enumerate(explicit_sections):
                title_elem = sec.find('title')
                
                if title_elem is not None:
                    section_title = self._clean_text(''.join(title_elem.itertext()))
                else:
                    section_title = f"Section_{i+1}"
                
                section_content = self._clean_text(''.join(sec.itertext()))
                
                if section_content and len(section_content) > 50:
                    sections[section_title] = section_content
            
            if sections:
                return sections
        
        # Strategy 2: Intelligent extraction with DSPy
        logger.info("Attempting intelligent extraction with DSPy")
        try:
            # Convert body element to XML string
            body_xml = ET.tostring(body_element, encoding='unicode', method='xml')
            
            # Use DSPy module for intelligent extraction
            dspy_result = self.section_extractor_dspy.forward(body_xml)
            
            if dspy_result['sections'] and len(dspy_result['sections']) >= 2:
                logger.info(f" DSPy extracted {len(dspy_result['sections'])} sections with confidence {dspy_result.get('confidence', 0)}")
                return dspy_result['sections']
            else:
                logger.info("DSPy did not find enough sections, fallback")
                
        except Exception as e:
            logger.warning(f"DSPy extraction error: {e}, using fallback")
        
        # Strategy 3: Fallback - Full Text
        logger.info("Using Full Text fallback")
        full_text_content = self._extract_full_text_content(body_element)
        
        if full_text_content and len(full_text_content) > 100:
            sections["Full Text"] = full_text_content
        
        return sections

    def _extract_full_text_content(self, body_element) -> str:
        """
        Extract complete text content from body
        """
        if body_element is None:
            return ""
            
        # Extract all text from body
        full_text = self._clean_text(''.join(body_element.itertext()))
        
        # Clean and filter
        if len(full_text) < 100:
            return ""
        
        return full_text

    def fetch_publication_details(self, pmcid: str) -> Optional[Publication]:
        """
        Get complete details of a publication via PMC ID
        """
        logger.info(f"Extraction of {pmcid}...")

        try:
            # 1. Get complete XML from PMC
            params = {
                'db': 'pmc',
                'id': pmcid.replace('PMC', ''),
                'retmode': 'xml'
            }

            response = self._make_request('efetch.fcgi', params)
            root = ET.fromstring(response.content)

            # 2. Parse XML
            article = root.find('.//article')
            if article is None:
                logger.warning(f"Article not found for {pmcid}")
                return None

            # Extract metadata
            meta = article.find('.//article-meta')
            front = article.find('.//front')

            if not meta or not front:
                logger.warning(f"Missing metadata for {pmcid}")
                return None

            # Title
            title_elem = meta.find('.//article-title')
            title = self._clean_text(''.join(title_elem.itertext()) if title_elem is not None else "No title")
            
            if not title or title == "No title":
                logger.warning(f"Missing title for {pmcid}")
                return None

            # Abstract
            abstract_elem = meta.find('.//abstract')
            abstract = self._clean_text(''.join(abstract_elem.itertext()) if abstract_elem is not None else "")

            # Authors
            authors = []
            for contrib in meta.findall('.//contrib[@contrib-type="author"]'):
                name = contrib.find('.//name')
                if name is not None:
                    firstname = self._clean_text(name.findtext('given-names', ''), 255)
                    lastname = self._clean_text(name.findtext('surname', ''), 255)
                    
                    if lastname:  # At least family name is required
                        aff_elem = contrib.find('.//aff')
                        affiliation = self._clean_text(''.join(aff_elem.itertext()) if aff_elem is not None else '')
                        
                        authors.append({
                            'firstname': firstname if firstname else None,
                            'lastname': lastname,
                            'affiliation': affiliation if affiliation else None
                        })

            # Publication date
            pub_date = meta.find('.//pub-date[@pub-type="epub"]') or meta.find('.//pub-date')
            year = pub_date.findtext('year', '') if pub_date is not None else ''
            month = pub_date.findtext('month', '01') if pub_date is not None else '01'
            day = pub_date.findtext('day', '01') if pub_date is not None else '01'
            
            # Date validation and formatting
            publication_date = None
            try:
                if year and year.isdigit() and len(year) == 4:
                    month = month.zfill(2) if month.isdigit() and 1 <= int(month) <= 12 else '01'
                    day = day.zfill(2) if day.isdigit() and 1 <= int(day) <= 31 else '01'
                    publication_date = f"{year}-{month}-{day}"
            except:
                pass

            # Journal
            journal_title = self._clean_text(front.findtext('.//journal-title', 'Unknown Journal'), 500)

            # DOI
            doi_elem = meta.find('.//article-id[@pub-id-type="doi"]')
            doi = self._clean_text(doi_elem.text if doi_elem is not None else None, 255)

            # PMID
            pmid_elem = meta.find('.//article-id[@pub-id-type="pmid"]')
            pmid = self._clean_text(pmid_elem.text if pmid_elem is not None else None, 20)

            # Keywords
            raw_keywords = []
            for kwd in meta.findall('.//kwd'):
                if kwd.text:
                    raw_keywords.append(kwd.text)
            
            keywords = self._clean_and_deduplicate_keywords(raw_keywords)

            # MeSH terms (requires separate query to PubMed)
            mesh_terms = self._fetch_mesh_terms(pmid) if pmid else []

            # Text sections with new strategy including DSPy
            body = article.find('.//body')
            sections = self._extract_text_sections(body)
            
            # Extract full text for new column
            full_text = self._extract_full_text_content(body)
            
            # If no full text from body, try from entire article
            if not full_text or len(full_text) < 200:
                full_text = self._clean_text(''.join(article.itertext()))
                if len(full_text) > 10000:
                    full_text = full_text[:10000]  # Limit to 10k characters

            # Validation: ensure we have at least one section
            if not sections:
                logger.warning(f"No text sections extracted for {pmcid}")
                if full_text and len(full_text) > 200:
                    sections["Full Text"] = full_text[:5000]  # Limited section

            # References (cited PMIDs)
            references = []
            ref_list = article.find('.//ref-list')
            if ref_list is not None:
                for ref in ref_list.findall('.//ref'):
                    pub_id = ref.find('.//pub-id[@pub-id-type="pmid"]')
                    if pub_id is not None and pub_id.text:
                        references.append(pub_id.text.strip())

            # Final validation
            if not title or not pmcid:
                logger.warning(f"Essential data missing for {pmcid}")
                return None

            publication = Publication(
                pmcid=pmcid,
                pmid=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=publication_date,
                journal=journal_title,
                doi=doi,
                keywords=keywords,
                full_text_sections=sections,
                full_text_content=full_text,  # NOW DEFINED IN DATACLASS
                mesh_terms=mesh_terms,
                references=references
            )

            # Log sections and full text
            logger.info(f" {pmcid} extracted with {len(sections)} section(s) and {len(full_text) if full_text else 0} chars of full text")
            return publication

        except Exception as e:
            logger.error(f"Extraction error {pmcid}: {e}")
            return None

    def _fetch_mesh_terms(self, pmid: str) -> List[str]:
        """Get MeSH terms from PubMed"""
        try:
            params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'xml'
            }
            response = self._make_request('efetch.fcgi', params)
            root = ET.fromstring(response.content)

            mesh_terms = []
            for mesh in root.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    term = self._clean_text(mesh.text, 255)
                    if term:
                        mesh_terms.append(term)

            return mesh_terms
        except Exception as e:
            logger.warning(f"MeSH extraction error for PMID {pmid}: {e}")
            return []

    async def batch_extract_to_db(self, pmcid_list: List[str], skip_existing: bool = True):
        """
        Extract all publications and insert them directly into database
        """
        if not self.db_client:
            raise ValueError("DatabaseClient required for database insertion")

        results = []
        failed = []
        skipped = []
        
        total = len(pmcid_list)
        logger.info(f" Starting extraction of {total} publications to PostgreSQL")

        for i, pmcid in enumerate(pmcid_list, 1):
            logger.info(f"Progression: {i}/{total} - {pmcid}")

            try:
                # Check if publication already exists
                if skip_existing and await self.check_publication_exists(pmcid):
                    skipped.append(pmcid)
                    continue

                # Extract data
                pub = self.fetch_publication_details(pmcid)

                if pub:
                    # Check that we have at least one section
                    if not pub.full_text_sections:
                        logger.warning(f" {pmcid} without sections, attempting alternative extraction")
                        
                    # Insert into database
                    try:
                        pub_id = await self.db_client.create_publication(pub.to_dict())
                        results.append(pub_id)
                        logger.info(f" {pmcid} inserted in database with ID {pub_id}")
                    except Exception as db_error:
                        logger.error(f" Insertion error {pmcid}: {db_error}")
                        failed.append(pmcid)
                else:
                    failed.append(pmcid)

                # Checkpoint every 25 documents
                if i % 25 == 0:
                    logger.info(f" Checkpoint: {len(results)} success, {len(failed)} failures, {len(skipped)} skipped")

            except Exception as e:
                logger.error(f" General error {pmcid}: {e}")
                failed.append(pmcid)

        logger.info(f"\n Extraction completed:")
        logger.info(f"    Success: {len(results)}")
        logger.info(f"    Failures: {len(failed)}")
        logger.info(f"   ⏭  Skipped: {len(skipped)}")

        if failed:
            logger.warning(f" Failed publications: {failed}")

        return results, failed, skipped


async def main():
    """Main extraction function"""
    
    # 1. Load PMCID list from CSV
    logger.info(" Loading publications list...")
    df = pd.read_csv("https://raw.githubusercontent.com/jgalazka/SB_publications/refs/heads/main/SB_publication_PMC.csv")
    
    pmcids = []
    for i in range(len(df)):
        link = df["Link"][i]
        pmcid = link.split("/")[-2] if link.endswith('/') else link.split("/")[-1]
        pmcids.append(pmcid)
    
    # Test with subset
    # pmcids = pmcids[:10]  # Uncomment to test
    
    logger.info(f" {len(pmcids)} publications to extract")

    # 2. Initialize database client
    db_client = DatabaseClient()
    
    try:
        # Create tables if necessary
        await db_client.create_tables()
        
        # 3. Initialize extractor
        extractor = NCBIExtractor(
            email=EMAIL,
            api_key=API_KEY,
            db_client=db_client
        )

        # 4. Launch extraction with direct database insertion
        results, failed, skipped = await extractor.batch_extract_to_db(
            pmcids, 
            skip_existing=True
        )

        logger.info(f"\n Process completed!")
        logger.info(f"    Total processed: {len(pmcids)}")
        logger.info(f"    Successful insertions: {len(results)}")
        logger.info(f"    Failures: {len(failed)}")
        logger.info(f"   ⏭  Already existing: {len(skipped)}")

        # Final statistics
        total_in_db = len(results) + len(skipped)
        logger.info(f"     Total in database: {total_in_db}")

    except Exception as e:
        logger.error(f" Fatal error: {e}")
        raise
    finally:
        await db_client.close()


if __name__ == "__main__":
    asyncio.run(main())