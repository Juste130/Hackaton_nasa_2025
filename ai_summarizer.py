"""
AI-powered Scientific Article Summarizer using DSPy
Generates structured summaries with key findings, methodology, and implications
"""
import os
import dspy
from typing import Dict, List, Optional
from client import DatabaseClient, Publication
from sqlalchemy import select
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScientificSummary(dspy.Signature):
    """Generate structured summary of a scientific article"""
    
    title: str = dspy.InputField(desc="Article title")
    abstract: str = dspy.InputField(desc="Article abstract")
    full_text: str = dspy.InputField(desc="Full article text (truncated if too long)")
    
    # Outputs
    executive_summary: str = dspy.OutputField(
        desc="2-3 sentence executive summary in plain language"
    )
    key_findings: str = dspy.OutputField(
        desc="Bulleted list of 3-5 main findings with specific results"
    )
    methodology: str = dspy.OutputField(
        desc="Brief description of research methods and experimental design"
    )
    organisms_studied: str = dspy.OutputField(
        desc="List of organisms/models used in the study"
    )
    space_relevance: str = dspy.OutputField(
        desc="How this research relates to spaceflight/microgravity conditions"
    )
    future_directions: str = dspy.OutputField(
        desc="Suggested future research directions mentioned by authors"
    )


class ArticleSummarizer(dspy.Module):
    """DSPy module for generating comprehensive article summaries"""
    
    def __init__(self, llm: Optional[dspy.LM] = None):
        super().__init__()
        
        # Remove the configure call - use global configuration
        # if llm:
        #     dspy.settings.configure(lm=llm)
        
        # Use Chain of Thought for better reasoning
        self.summarize = dspy.ChainOfThought(ScientificSummary)
    
    def forward(self, title: str, abstract: str, full_text: str) -> dspy.Prediction:
        """Generate structured summary"""
        
        # Truncate full_text if too long (max 8000 chars for context window)
        if len(full_text) > 8000:
            full_text = full_text[:8000] + "... [truncated]"
        
        return self.summarize(
            title=title,
            abstract=abstract,
            full_text=full_text
        )


class SummaryService:
    """Service for summarizing publications from database"""
    
    def __init__(self, llm: Optional[dspy.LM] = None):
        self.db_client = DatabaseClient()
        self.summarizer = ArticleSummarizer(llm)
    
    async def summarize_by_pmcid(self, pmcid: str) -> Dict:
        """
        Generate summary for a publication by PMCID
        
        Returns:
            {
                'pmcid': str,
                'title': str,
                'summary': {
                    'executive_summary': str,
                    'key_findings': str,
                    'methodology': str,
                    ...
                },
                'generated_at': datetime
            }
        """
        async with self.db_client.async_session() as session:
            # Fetch publication
            result = await session.execute(
                select(Publication).where(Publication.pmcid == pmcid)
            )
            pub = result.scalar_one_or_none()
            
            if not pub:
                raise ValueError(f"Publication {pmcid} not found")
            
            # Get full text
            full_text = pub.full_text_content or ""
            if not full_text and pub.abstract:
                full_text = pub.abstract
            
            # Generate summary
            logger.info(f" Generating summary for {pmcid}...")
            summary = self.summarizer(
                title=pub.title,
                abstract=pub.abstract or "",
                full_text=full_text
            )
            
            return {
                'pmcid': pmcid,
                'title': pub.title,
                'summary': {
                    'executive_summary': summary.executive_summary,
                    'key_findings': summary.key_findings,
                    'methodology': summary.methodology,
                    'organisms_studied': summary.organisms_studied,
                    'space_relevance': summary.space_relevance,
                    'future_directions': summary.future_directions
                },
                'generated_at': datetime.now().isoformat()
            }
    
    async def batch_summarize(self, pmcids: List[str]) -> List[Dict]:
        """Summarize multiple publications"""
        summaries = []
        
        for pmcid in pmcids:
            try:
                summary = await self.summarize_by_pmcid(pmcid)
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to summarize {pmcid}: {e}")
                continue
        
        return summaries
    
    async def close(self):
        await self.db_client.close()


# CLI for testing
async def main():
    """Test summarizer"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_summarizer.py <PMCID>")
        return
    
    pmcid = sys.argv[1]

    # Configure DSPy with Mistral
    llm = dspy.LM(
            "openai/mistral-small-latest",
            api_key=os.environ.get("MISTRAL_API_KEY"),
            api_base="https://api.mistral.ai/v1",
            max_tokens=2000000
        )
    
    service = SummaryService(llm)
    
    try:
        summary = await service.summarize_by_pmcid(pmcid)
        
        print(f"\n{'='*70}")
        print(f" SUMMARY FOR: {summary['title']}")
        print(f"{'='*70}\n")
        
        print(f" Executive Summary:\n{summary['summary']['executive_summary']}\n")
        print(f" Key Findings:\n{summary['summary']['key_findings']}\n")
        print(f" Methodology:\n{summary['summary']['methodology']}\n")
        print(f"🧬 Organisms Studied:\n{summary['summary']['organisms_studied']}\n")
        print(f" Space Relevance:\n{summary['summary']['space_relevance']}\n")
        print(f" Future Directions:\n{summary['summary']['future_directions']}\n")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())