"""
NASA Publications Abstract Generator
DSPy module to generate missing abstracts from scientific publications
in NASA space bioscience domain
"""

from contextlib import redirect_stdout
import io
import dspy
import asyncio
import re
from typing import List, Dict, Literal, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from src.database.client import DatabaseClient
from src.data_pipeline.extractors.ncbi_extractor import NCBIExtractor
import logging
from src.database.client import Publication, TextSection
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ArticleType(Enum):
    CORRECTION = "correction"
    ERRATUM = "erratum" 
    RETRACTION = "retraction"
    ORIGINAL = "original"

@dataclass
class MissingAbstractArticle:
    """Scientific article without abstract requiring automatic generation"""
    id: str
    pmcid: str
    pmid: Optional[str]
    title: str
    abstract: str  # Empty or None
    full_text_sections: Dict[str, str]
    article_type: ArticleType
    original_pmcid: Optional[str] = None  # For corrections

# === DSPy Signatures ===

class ArticleClassifier(dspy.Signature):
    """
    Scientific article classifier to identify publication type.
    
    Context: In the NASA bioscience database, some articles are corrections,
    erratas or retractions of other articles. It is crucial to identify them as their
    processing differs from original research articles.
    
    Instructions:
    - Analyze title to detect keywords like "correction", "erratum", "retraction"
    - Examine content to identify corrective nature
    - Corrections often mention the original corrected article
    - Original articles present new research
    """
    title = dspy.InputField(desc="Complete title of scientific article to analyze")
    content_preview = dspy.InputField(desc="Excerpt from beginning of article content (first 500 characters)")

    article_type: Literal["correction", "erratum", "retraction", "original"] = dspy.OutputField(
        desc="Precise article type: 'correction' for article corrections, 'erratum' for factual errors, 'retraction' for withdrawals, 'original' for new research"
    )
    confidence = dspy.OutputField(desc="Confidence score from 0.0 to 1.0 on classification")
    reasoning = dspy.OutputField(desc="Detailed justification of classification based on title and content clues")

class OriginalArticleFinder(dspy.Signature):
    """
    Specialized research agent to identify the original article referenced by a correction.
    
    Context: NASA scientific article corrections reference an original article
    that they correct. We need to find this article to contextualize the correction.
    
    Instructions:
    - Search for explicit PMCID mentions in correction text
    - Identify key terms of original article from correction title
    - Use NCBI search tools to validate candidates
    - Prioritize explicitly mentioned PMCIDs
    
    Available tools:
    - search_ncbi_for_pmcid: Search by terms in NCBI database
    - validate_pmcid_exists: Verify PMCID existence
    """
    correction_title = dspy.InputField(desc="Complete title of correction article to analyze")
    correction_content = dspy.InputField(desc="Textual content of correction (first 2000 characters)")
    
    original_title = dspy.OutputField(desc="Probable reconstructed title of original corrected article")
    search_terms : List[str] = dspy.OutputField(desc="Optimized search terms to find original article in NCBI")
    pmcid_candidates:List[str] = dspy.OutputField(desc="List of candidate PMCIDs found (ex: PMC123456, PMC789012)")

class AbstractGenerator(dspy.Signature):
    """
    Scientific abstract generator for NASA space bioscience publications.
    
    Context: Generate missing abstracts for bioscience research articles
    spatial. Abstracts must follow scientific standards with introduction,
    methodology, results and conclusions.
    
    CRITICAL Instructions:
    - MANDATORY: Generate abstract in ENGLISH only, unless source content is in another language
    - MANDATORY: Produce ONE CONTINUOUS PARAGRAPH without formatting (no bold, italic, bullets, etc.)
    - Standard scientific format: objective/context, methodology, main results, conclusions/implications
    - Use precise scientific vocabulary and appropriate technical terms
    - Length: 150-250 words strictly
    - Academic and objective tone, typical style of scientific publications
    - Avoid marketing or sensationalist phrases
    """
    title = dspy.InputField(desc="Complete title of scientific research article")
    content = dspy.InputField(desc="Structured textual content or available article sections")
    content_source = dspy.InputField(desc="Content source: 'structured_sections' if classic sections found, 'fallback_sections' if generic sections used")
    
    abstract = dspy.OutputField(desc="Scientific abstract in ONE CONTINUOUS PARAGRAPH of 150-250 words, IN ENGLISH, without formatting, standard academic style")
    key_findings = dspy.OutputField(desc="Main discoveries and significant study results (in English)")
    methodology = dspy.OutputField(desc="Main methodological approach used in the study (in English)")

class CorrectionSummarizer(dspy.Signature):
    """
    Specialized in synthesis of scientific article corrections.
    
    Context: Article corrections modify or clarify elements of the original
    article. We need to create a summary that clearly explains the changes made.
    
    CRITICAL Instructions:
    - MANDATORY: Generate summary in ENGLISH
    - MANDATORY: Produce ONE CONTINUOUS PARAGRAPH without formatting
    - Identify precisely the corrected elements
    - Explain the nature of each correction
    - Evaluate impact on original conclusions
    - Maintain objective and factual tone
    - Professional academic style
    """
    correction_content = dspy.InputField(desc="Complete correction text describing the changes made")
    original_abstract = dspy.InputField(desc="Abstract of original article being corrected")
    
    correction_summary = dspy.OutputField(desc="Correction summary in ONE CONTINUOUS PARAGRAPH of 100-200 words, IN ENGLISH, without formatting")
    corrected_elements = dspy.OutputField(desc="Specific list of corrected elements (data, figures, conclusions, etc.)")
    impact_level = dspy.OutputField(desc="Impact level: 'minor' for minor corrections, 'major' for significant changes, 'critical' for major corrections")

# === Tools for DSPy ReAct ===

def search_ncbi_for_pmcid(search_terms: str, email: str = "amrromuald234@gmail.com") -> str:
    """
    Search for a PMCID via NCBI API using search terms.
    
    Args:
        search_terms: Search terms to find the article
        email: Email for NCBI API (required)
    
    Returns:
        Found PMCID or error message
    """
    import requests
    import xml.etree.ElementTree as ET
    import time
    
    try:
        # Search via ESearch
        params = {
            'db': 'pmc',
            'term': search_terms,
            'retmax': 5,
            'retmode': 'xml',
            'email': email
        }
        
        time.sleep(0.5)  # Rate limiting
        response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            id_list = root.find('.//IdList')
            
            if id_list is not None:
                ids = [id_elem.text for id_elem in id_list.findall('Id')]
                if ids:
                    # Return first ID found in PMC format
                    return f"Found PMCID: PMC{ids}"
        
        return "No results found for search terms"
        
    except Exception as e:
        return f"Search error: {str(e)}"

def validate_pmcid_exists(pmcid: str, email: str = "amrromuald234@gmail.com") -> str:
    """
    Validate that a PMCID exists in NCBI database.
    
    Args:
        pmcid: PMCID to validate (format PMC123456)
        email: Email for NCBI API
    
    Returns:
        Validation message or error
    """
    import requests
    import time
    
    try:
        pmc_id = pmcid.replace('PMC', '')
        params = {
            'db': 'pmc',
            'id': pmc_id,
            'retmode': 'xml',
            'email': email
        }
        
        time.sleep(0.5)  # Rate limiting
        response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params=params)
        
        if response.status_code == 200 and 'article' in response.text.lower():
            return f"Valid: {pmcid} exists in NCBI database"
        else:
            return f"Invalid: {pmcid} not found in NCBI database"
            
    except Exception as e:
        return f"Validation error for {pmcid}: {str(e)}"

# === DSPy Modules ===

class AbstractGeneratorModule(dspy.Module):
    """
    Main module for automatic generation of missing abstracts.
    """
    
    def __init__(self, db_client: DatabaseClient, ncbi_extractor: NCBIExtractor):
        super().__init__()
        self.db_client = db_client
        self.ncbi_extractor = ncbi_extractor
        
        # DSPy modules with specialized configuration
        self.classifier = dspy.ChainOfThought(ArticleClassifier)
        self.original_finder = dspy.ReAct(OriginalArticleFinder, tools=[search_ncbi_for_pmcid, validate_pmcid_exists])
        self.abstract_generator = dspy.ChainOfThought(AbstractGenerator)
        self.correction_summarizer = dspy.ChainOfThought(CorrectionSummarizer)
    
    async def forward_async(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """
        Main asynchronous abstract generation process.
        
        Args:
            article: Article requiring an abstract
            
        Returns:
            Dictionary with generated abstract and metadata
        """
        
        # 1. Article classification
        article_type = self._classify_article(article)
        
        if article_type in [ArticleType.CORRECTION, ArticleType.ERRATUM]:
            return await self._handle_correction_async(article)
        else:
            return await self._generate_original_abstract(article)
    
    # Keep forward method synchronous for DSPy compatibility
    def forward(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Synchronous version that wraps async"""
        return asyncio.run(self.forward_async(article))
    
    async def _handle_correction_async(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Handle specifically an article correction asynchronously"""
        
        # 1. Find original article with DSPy ReAct
        original_pmcid = self._find_original_article_with_react(article)
        
        if original_pmcid:
            # 2. Retrieve original abstract (with extraction if necessary)
            original_abstract = await self._get_or_extract_original_abstract(original_pmcid)
            
            if original_abstract:
                # 3. Generate correction summary
                correction_content = self._get_full_content(article.full_text_sections)
                
                summary = self.correction_summarizer(
                    correction_content=correction_content[:3000],
                    original_abstract=original_abstract
                )
                
                return {
                    'abstract_generated': summary.correction_summary,
                    'generation_type': 'correction_summary',
                    'original_pmcid': original_pmcid,
                    'corrected_elements': summary.corrected_elements,
                    'impact_level': summary.impact_level
                }
        
        # Fallback: treat as original article
        logger.warning(f"Unable to process {article.pmcid} as correction, fallback to generation")
        return await self._generate_original_abstract(article)

    async def _get_or_extract_original_abstract(self, pmcid: str) -> Optional[str]:
        """
        Get abstract of original article from DB, 
        or extract and add to DB if not found
        """
        try:
            # 1. Try to retrieve from DB
            original_abstract = await self._get_original_abstract(pmcid)
            
            if original_abstract:
                logger.info(f"Original abstract found in DB for {pmcid}")
                return original_abstract
            
            # 2. If not found in DB, check if article exists
            pub_exists = await self._check_publication_exists_in_db(pmcid)
            
            if pub_exists:
                logger.warning(f"Article {pmcid} exists in DB but without abstract")
                return None
            
            # 3. Article not in DB, extract from NCBI
            logger.info(f"Article {pmcid} not found in DB, extracting from NCBI...")
            
            extracted_pub = self.ncbi_extractor.fetch_publication_details(pmcid)
            
            if extracted_pub:
                # 4. Add extracted article to DB
                try:
                    pub_id = await self.db_client.create_publication(extracted_pub.to_dict())
                    logger.info(f" Original article {pmcid} extracted and added to DB with ID {pub_id}")
                    return extracted_pub.abstract if extracted_pub.abstract else None
                except Exception as db_error:
                    logger.error(f" Error inserting original article {pmcid}: {db_error}")
                    # Return abstract even if insertion fails
                    return extracted_pub.abstract if extracted_pub.abstract else None
            else:
                logger.error(f" Unable to extract original article {pmcid} from NCBI")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving/extracting abstract for {pmcid}: {e}")
            return None

    async def _check_publication_exists_in_db(self, pmcid: str) -> bool:
        """Check if a publication exists in DB"""
        try:
            async with self.db_client.async_session() as session:
                result = await session.execute(
                    select(Publication.id)
                    .where(Publication.pmcid == pmcid)
                )
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking existence {pmcid}: {e}")
            return False

    async def _generate_original_abstract(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Generate abstract for original article with fallback from DB"""
        
        # 1. Try to find structured sections from DB
        content, content_source = await self._extract_structured_content_from_db(article.id)
        
        # 2. If no structured content, use available sections
        if not content:
            content, content_source = await self._extract_fallback_content_from_db(article.id)
        
        if not content:
            logger.warning(f"No usable content found for {article.pmcid}")
            return {'error': 'No suitable content for abstract generation'}
        
        # Generate abstract
        try:
            generated = self.abstract_generator(
                title=article.title,
                content=content,
                content_source=content_source
            )
            
            return {
                'abstract_generated': generated.abstract,
                'generation_type': 'full_abstract',
                'key_findings': generated.key_findings,
                'methodology': generated.methodology
            }
        except Exception as e:
            logger.error(f"Error generating abstract for {article.pmcid}: {e}")
            return {'error': f'Generation failed: {str(e)}'}
    
    async def _extract_structured_content_from_db(self, publication_id: str) -> Tuple[str, str]:
        """Extract content from classic structured sections from DB"""
        
        # Searched sections with priority
        section_keywords = [
            ['introduction', 'background'],
            ['methods', 'methodology', 'materials', 'experimental', 'procedure'],
            ['results', 'findings', 'observations'],
            ['conclusion', 'discussion', 'summary', 'implications']
        ]
        
        async with self.db_client.async_session() as session:
            structured_content = []
            found_sections = []
            
            for keywords in section_keywords:
                # Build OR condition for each keyword group
                conditions = [
                    TextSection.section_name.ilike(f'%{keyword}%') 
                    for keyword in keywords
                ]
                
                result = await session.execute(
                    select(TextSection)
                    .where(
                        and_(
                            TextSection.publication_id == uuid.UUID(publication_id),
                            or_(*conditions)
                        )
                    )
                    .order_by(TextSection.section_order)
                    .limit(1)  # Take first matching section
                )
                
                section = result.scalar_one_or_none()
                if section:
                    # Limit each section to 800 characters and remove formatting
                    truncated_content = section.content[:800]
                    section_type = self._categorize_section(section.section_name)
                    # Simple format without markdown
                    structured_content.append(f"{section_type}: {truncated_content}")
                    found_sections.append(section_type)
                    logger.debug(f"Section found: {section.section_name} -> {section_type}")
            
            if structured_content:
                content = " ".join(structured_content)  # Join with spaces
                source = f"structured_sections_db ({', '.join(found_sections)})"
                logger.info(f"Structured content found in DB: {found_sections}")
                return content, source
        
        return "", ""
    
    async def _extract_fallback_content_from_db(self, publication_id: str, max_chars: int = 2500) -> Tuple[str, str]:
        """Extract content from first available sections from DB as fallback"""
        
        async with self.db_client.async_session() as session:
            # Retrieve first 5 sections by order
            result = await session.execute(
                select(TextSection)
                .where(TextSection.publication_id == uuid.UUID(publication_id))
                .order_by(TextSection.section_order)
                .limit(5)
            )
            
            sections = result.scalars().all()
            
            if not sections:
                return "", ""
            
            fallback_content = []
            section_names = []
            current_chars = 0
            
            for section in sections:
                if current_chars >= max_chars:
                    break
                    
                # Calculate how many characters we can still take
                remaining_chars = max_chars - current_chars
                section_char_limit = min(remaining_chars, 800)  # Max 800 per section
                
                if section_char_limit > 100:  # At least 100 useful characters
                    truncated_content = section.content[:section_char_limit]
                    # Simple format without markdown
                    fallback_content.append(f"{section.section_name}: {truncated_content}")
                    section_names.append(section.section_name)
                    current_chars += len(truncated_content)
            
            if fallback_content:
                content = " ".join(fallback_content)  # Join with spaces
                source = f"fallback_sections_db ({', '.join(section_names)})"
                logger.info(f"Fallback content used from DB: {section_names}")
                return content, source
        
        return "", ""
    
    def _categorize_section(self, section_name: str) -> str:
        """Categorize a section according to its name"""
        name_lower = section_name.lower()
        
        if any(keyword in name_lower for keyword in ['introduction', 'background']):
            return 'Introduction'
        elif any(keyword in name_lower for keyword in ['method', 'material', 'experimental', 'procedure']):
            return 'Methods'
        elif any(keyword in name_lower for keyword in ['result', 'finding', 'observation']):
            return 'Results'
        elif any(keyword in name_lower for keyword in ['conclusion', 'discussion', 'summary', 'implication']):
            return 'Conclusion'
        else:
            return section_name.title()
    
    # === Utility methods ===
    
    def _get_content_preview(self, sections: Dict[str, str], max_chars: int = 500) -> str:
        """Get content preview for classification"""
        content = ""
        for section_name, section_content in sections.items():
            content += f"{section_name}: {section_content[:200]}\n"
            if len(content) > max_chars:
                break
        return content[:max_chars]
    
    def _get_full_content(self, sections: Dict[str, str]) -> str:
        """Get complete formatted content without markdown"""
        return " ".join([f"{name}: {content}" for name, content in sections.items()])
    
    async def _get_original_abstract(self, pmcid: str) -> Optional[str]:
        """Retrieve original article abstract from DB"""
        try:
            async with self.db_client.async_session() as session:
                result = await session.execute(
                    select(Publication.abstract)
                    .where(Publication.pmcid == pmcid)
                )
                abstract = result.scalar_one_or_none()
                return abstract if abstract else None
        except Exception as e:
            logger.error(f"Error retrieving abstract for {pmcid}: {e}")
            return None


# === Main orchestrator ===

class AbstractGenerationOrchestrator:
    """
    Orchestrator for complete abstract generation process.
    
    Coordinates the entire pipeline: identifying missing articles,
    generating abstracts, and saving to database.
    """
    
    def __init__(self, db_client: DatabaseClient, llm_model: str = "gpt-4"):
        self.db_client = db_client
        
        # Configure DSPy with specialized model
        lm = dspy.LM(
            model="openrouter/x-ai/grok-4-fast:free",
            api_base="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        dspy.settings.configure(lm=lm)
        
        # Initialize modules
        self.ncbi_extractor = NCBIExtractor(
            email="amrromuald234@gmail.com",
            api_key=os.getenv("NCBI_API_KEY")
        )
        self.generator = AbstractGeneratorModule(db_client, self.ncbi_extractor)
    
    async def find_missing_abstracts(self) -> List[MissingAbstractArticle]:
        """Identify all articles without abstract having usable content"""
        
        # Query for articles without abstract (NULL or empty)
        async with self.db_client.async_session() as session:
            result = await session.execute(
                select(Publication, TextSection)
                .outerjoin(TextSection)
                .where(
                    or_(
                        Publication.abstract.is_(None),
                        Publication.abstract == '',
                        and_(Publication.abstract.is_not(None), Publication.abstract.like(''))
                    )
                )
            )
            
            # Group by publication and build objects
            publications_data = {}
            for pub, section in result.all():
                if pub.id not in publications_data:
                    publications_data[pub.id] = {
                        'publication': pub,
                        'sections': {}
                    }
                
                if section:
                    publications_data[pub.id]['sections'][section.section_name] = section.content
            
            # Convert to MissingAbstractArticle
            missing_articles = []
            for pub_data in publications_data.values():
                pub = pub_data['publication']
                
                # Only process articles that have text sections
                if pub_data['sections']:
                    article = MissingAbstractArticle(
                        id=str(pub.id),
                        pmcid=pub.pmcid,
                        pmid=pub.pmid,
                        title=pub.title,
                        abstract=pub.abstract or "",
                        full_text_sections=pub_data['sections'],
                        article_type=ArticleType.ORIGINAL  # Will be reclassified
                    )
                    missing_articles.append(article)
                else:
                    logger.warning(f"Article {pub.pmcid} ignored: no text sections")
            
            logger.info(f"Found {len(missing_articles)} articles without abstract with content")
            return missing_articles
    
    async def generate_missing_abstracts(self, batch_size: int = 5):
        """Generate all missing abstracts with batch processing"""
        
        missing_articles = await self.find_missing_abstracts()
        
        if not missing_articles:
            logger.info("No missing abstract found")
            return
        
        logger.info(f"Starting generation for {len(missing_articles)} articles")
        
        results = {
            'generated': [],
            'corrections': [],
            'failed': []
        }
        
        # Batch processing for performance optimization
        for i in range(0, len(missing_articles), batch_size):
            batch = missing_articles[i:i+batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(missing_articles) + batch_size - 1) // batch_size}: {len(batch)} articles")
            
            for article in batch:
                try:
                    logger.info(f" Generating abstract for {article.pmcid} ({article.title[:50]}...)")
                    
                    # Use async version
                    result = await self.generator.forward_async(article)
                    
                    if 'error' in result:
                        logger.error(f" Content error {article.pmcid}: {result['error']}")
                        results['failed'].append(article.pmcid)
                        continue
                    
                    # Save to database
                    await self._save_generated_abstract(article, result)
                    
                    if result.get('generation_type') == 'correction_summary':
                        results['corrections'].append(article.pmcid)
                        logger.info(f" Correction summary generated for {article.pmcid}")
                    else:
                        results['generated'].append(article.pmcid)
                        logger.info(f" Abstract generated for {article.pmcid}")
                    
                except Exception as e:
                    logger.error(f" Generation error {article.pmcid}: {e}")
                    results['failed'].append(article.pmcid)
        
        # Detailed final report
        logger.info(f"""
 Abstract generation completed:
    Generated abstracts: {len(results['generated'])}
    Correction summaries: {len(results['corrections'])}
    Failures: {len(results['failed'])}
    Success rate: {((len(results['generated']) + len(results['corrections'])) / len(missing_articles) * 100):.1f}%
        """)
        
        if results['failed']:
            logger.warning(f" Failed articles: {results['failed'][:10]}{'...' if len(results['failed']) > 10 else ''}")
        
        return results
    
    async def _save_generated_abstract(self, article: MissingAbstractArticle, result: Dict[str, str]):
        """Save generated abstract with metadata to database"""
        
        update_data = {
            'abstract_generated': result.get('abstract_generated'),
            'generation_type': result.get('generation_type'),
        }
        
        # Add additional metadata if available
        if 'key_findings' in result:
            update_data['key_findings'] = result['key_findings']
        if 'methodology' in result:
            update_data['methodology'] = result['methodology']
        if 'original_pmcid' in result:
            update_data['original_pmcid'] = result['original_pmcid']
        if 'impact_level' in result:
            update_data['impact_level'] = result['impact_level']
        
        success = await self.db_client.update_publication(
            uuid.UUID(article.id), 
            update_data
        )
        
        if not success:
            logger.error(f" Save failure for {article.pmcid}")


# === Main script ===

async def main():
    """Main script to generate missing abstracts"""
    
    # Configuration
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    db_client = DatabaseClient()
    orchestrator = AbstractGenerationOrchestrator(db_client)
    
    try:
        # Generate missing abstracts
        results = await orchestrator.generate_missing_abstracts(batch_size=2)  # Optimized batch
        
        print(" Process completed successfully!")
    
    except Exception as e:
        logger.error(f" Fatal error: {e}")
        raise
    finally:
        await db_client.close()
    
    # Write DSPy history for analysis
    f = io.StringIO()
    with redirect_stdout(f):
        dspy.inspect_history()
    output = f.getvalue()
    try:
        with open("dspy_inspect.txt", "w", encoding='utf-8') as f:
            f.write("=== DSPY HISTORY ABSTRACT GENERATION ===\n\n")
            f.write(output)
    except Exception as e:
        logger.warning(f"Error saving DSPy history: {e}")


if __name__ == "__main__":
    asyncio.run(main())