"""
Batch extraction using optimized weak LLM
Cost savings: ~5-10x compared to strong LLM
"""
import asyncio
import json
import os
from typing import List
from client import DatabaseClient, Publication, PublicationKeyword, PublicationMeshTerm
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import dspy
from config import OPENROUTER_API_KEY
from dspy_extractors import BiologicalEntityExtractorModule
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizedBatchExtractor:
    """Batch extraction with compiled DSPy model"""
    
    def __init__(self, compiled_model_path: str = "compiled_extractor.json"):
        self.db_client = DatabaseClient()
        
        # Load compiled model
        self.compiled_module = BiologicalEntityExtractorModule()
        self.compiled_module.load(compiled_model_path)
        
        # Configure LLM
        lm = dspy.LM(
            "openai/mistral-small-latest",
            api_key=os.environ.get("MISTRAL_API_KEY"),
            api_base="https://api.mistral.ai/v1",
            max_tokens=2000000
        )
        dspy.settings.configure(lm=lm)
        
        logger.info(f" Loaded compiled model from {compiled_model_path}")
    
    async def extract_all_publications(self, batch_size: int = 10):
        """Extract entities from all 608 publications"""
        
        # Get all publications WITH eager loading
        async with self.db_client.async_session() as session:
            result = await session.execute(
                select(Publication)
                .options(
                    selectinload(Publication.keywords).selectinload(PublicationKeyword.keyword),
                    selectinload(Publication.mesh_terms).selectinload(PublicationMeshTerm.mesh_term)
                )
                .limit(608)
            )
            all_pubs = result.scalars().all()
            
            # Convert to dicts INSIDE session to avoid lazy loading
            publications_dict = []
            for pub in all_pubs:
                try:
                    pub_dict = {
                        'pmcid': pub.pmcid,
                        'title': pub.title,
                        'abstract': pub.abstract or '',
                        'keywords': [kw.keyword.keyword for kw in pub.keywords] if pub.keywords else [],
                        'mesh_terms': [mt.mesh_term.term for mt in pub.mesh_terms] if pub.mesh_terms else []
                    }
                    publications_dict.append(pub_dict)
                except Exception as e:
                    logger.warning(f" Skipping {pub.pmcid}: {e}")
                    continue
        
        logger.info(f" Processing {len(publications_dict)} publications")
        
        results = []
        
        for i in range(0, len(publications_dict), batch_size):
            batch = publications_dict[i:i+batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(publications_dict) + batch_size - 1)//batch_size
            logger.info(f" Batch {batch_num}/{total_batches}")
            
            for pub_data in batch:
                try:
                    # Extract with weak LLM + optimized prompts
                    extracted = self.compiled_module.forward(publication_data=pub_data)
                    
                    results.append({
                        'pmcid': pub_data['pmcid'],
                        'entities': extracted
                    })
                    
                    logger.info(f" {pub_data['pmcid']}: {len(extracted['organisms'])} org, {len(extracted['phenomena'])} phen")
                    
                except Exception as e:
                    logger.error(f" Error {pub_data['pmcid']}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Save results
        output_file = 'extracted_entities_all.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f" Extracted entities from {len(results)} publications")
        logger.info(f" Saved to {output_file}")
        
        # Print statistics
        self._print_extraction_stats(results)
        
        return results
    
    def _print_extraction_stats(self, results: List[dict]):
        """Print extraction statistics"""
        total_organisms = sum(len(r['entities']['organisms']) for r in results)
        total_phenomena = sum(len(r['entities']['phenomena']) for r in results)
        
        avg_organisms = total_organisms / len(results) if results else 0
        avg_phenomena = total_phenomena / len(results) if results else 0
        
        contexts = {}
        for r in results:
            ctx = r['entities']['experimental_context']
            contexts[ctx] = contexts.get(ctx, 0) + 1
        
        platforms = {}
        for r in results:
            plat = r['entities'].get('platform')
            if plat:
                platforms[plat] = platforms.get(plat, 0) + 1
        
        logger.info(f"""
 Extraction Statistics:
   Total publications processed: {len(results)}
   Total organisms extracted: {total_organisms} (avg: {avg_organisms:.1f}/pub)
   Total phenomena extracted: {total_phenomena} (avg: {avg_phenomena:.1f}/pub)
   
   Experimental contexts:
   {chr(10).join(f'   - {ctx}: {count}' for ctx, count in sorted(contexts.items(), key=lambda x: -x[1]))}
   
   Top platforms:
   {chr(10).join(f'   - {plat}: {count}' for plat, count in sorted(platforms.items(), key=lambda x: -x[1])[:5])}
        """)


async def main():
    extractor = OptimizedBatchExtractor()
    await extractor.extract_all_publications(batch_size=10)


if __name__ == "__main__":
    asyncio.run(main())