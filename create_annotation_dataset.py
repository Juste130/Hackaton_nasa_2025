"""
Create gold-standard annotation dataset using strong LLM
"""
import asyncio
import json
import random
from typing import List, Dict
from client import DatabaseClient, Publication, PublicationKeyword, PublicationMeshTerm, Keyword, MeshTerm
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from dspy_extractors import BiologicalEntityExtractorModule
import dspy
from config import OPENROUTER_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnnotationDatasetCreator:
    """Create high-quality annotations for DSPy optimization"""
    
    def __init__(self, num_examples: int = 20):
        self.num_examples = num_examples
        self.db_client = DatabaseClient()
        
        # Use STRONG model for annotations
        self.strong_lm = dspy.LM(
            model="openrouter/x-ai/grok-4-fast",  # Strong model
            api_base="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        
    async def select_diverse_publications(self) -> List[Dict]:
        """
        Select diverse publications for annotation and convert to dicts
        - Different years
        - Different organisms (if keywords available)
        - Different journals
        - Mix of long/short abstracts
        """
        async with self.db_client.async_session() as session:
            # Get all publications WITH eager loading of ALL relations
            result = await session.execute(
                select(Publication)
                .options(
                    selectinload(Publication.keywords).selectinload(PublicationKeyword.keyword),
                    selectinload(Publication.mesh_terms).selectinload(PublicationMeshTerm.mesh_term)
                )
                .limit(608)
            )
            all_pubs = result.scalars().all()
            
            # Convert to dicts INSIDE the session
            all_pubs_dict = []
            for pub in all_pubs:
                try:
                    pub_dict = {
                        'pmcid': pub.pmcid,
                        'title': pub.title,
                        'abstract': pub.abstract or '',
                        'keywords': [kw.keyword.keyword for kw in pub.keywords] if pub.keywords else [],
                        'mesh_terms': [mt.mesh_term.term for mt in pub.mesh_terms] if pub.mesh_terms else [],
                        'publication_date': pub.publication_date,
                        'journal': pub.journal
                    }
                    all_pubs_dict.append(pub_dict)
                except Exception as e:
                    logger.warning(f"Error converting publication {pub.pmcid}: {e}")
                    # Skip this publication but continue
                    continue
            
            logger.info(f" Converted {len(all_pubs_dict)} publications to dict")
            
            # Stratified sampling for diversity
            selected = []
            
            # 1. Sample by year (ensure temporal diversity)
            years = {}
            for pub in all_pubs_dict:
                if pub['publication_date']:
                    year = pub['publication_date'].year
                    if year not in years:
                        years[year] = []
                    years[year].append(pub)
            
            # Take 2-3 per year if available
            for year_pubs in years.values():
                selected.extend(random.sample(year_pubs, min(2, len(year_pubs))))
            
            # 2. Ensure we have exactly num_examples
            if len(selected) < self.num_examples:
                remaining = [p for p in all_pubs_dict if p not in selected]
                if remaining:
                    num_to_add = min(len(remaining), self.num_examples - len(selected))
                    selected.extend(random.sample(remaining, num_to_add))
            elif len(selected) > self.num_examples:
                selected = random.sample(selected, self.num_examples)
            
            logger.info(f" Selected {len(selected)} diverse publications for annotation")
            return selected
    
    async def create_annotations(self, output_file: str = "annotations_gold.json"):
        """
        Create gold-standard annotations using strong LLM
        """
        # Configure DSPy with strong model
        dspy.settings.configure(lm=self.strong_lm)
        
        # Select publications (already as dicts)
        publications = await self.select_diverse_publications()
        
        if not publications:
            logger.error(" No publications selected for annotation!")
            return []
        
        # Extract entities with strong model
        extractor = BiologicalEntityExtractorModule()
        
        annotations = []
        
        for i, pub_data in enumerate(publications, 1):
            logger.info(f" Annotating {i}/{len(publications)}: {pub_data['pmcid']}")
            
            try:
                # Extract with strong model (pub_data is already a dict)
                result = extractor.forward(pub_data)
                
                # Store as training example
                annotation = {
                    'input': {
                        'pmcid': pub_data['pmcid'],
                        'title': pub_data['title'],
                        'abstract': pub_data['abstract'],
                        'keywords': pub_data['keywords'],
                        'mesh_terms': pub_data['mesh_terms']
                    },
                    'output': result,
                    'metadata': {
                        'pmcid': pub_data['pmcid'],
                        'year': pub_data['publication_date'].year if pub_data['publication_date'] else None,
                        'journal': pub_data['journal']
                    }
                }
                
                annotations.append(annotation)
                logger.info(f" Annotated: {len(result['organisms'])} organisms, {len(result['phenomena'])} phenomena")
                
            except Exception as e:
                logger.error(f" Error annotating {pub_data['pmcid']}: {e}")
                import traceback
                traceback.print_exc()
        
        # Save annotations
        with open(output_file, 'w') as f:
            json.dump(annotations, f, indent=2)
        
        logger.info(f" Saved {len(annotations)} annotations to {output_file}")
        
        # Print statistics
        if annotations:
            self._print_annotation_stats(annotations)
        
        return annotations
    
    def _print_annotation_stats(self, annotations: List[Dict]):
        """Print statistics about annotations"""
        total_organisms = sum(len(a['output']['organisms']) for a in annotations)
        total_phenomena = sum(len(a['output']['phenomena']) for a in annotations)
        
        contexts = {}
        for a in annotations:
            ctx = a['output']['experimental_context']
            contexts[ctx] = contexts.get(ctx, 0) + 1
        
        logger.info(f"""
 Annotation Statistics:
   Total examples: {len(annotations)}
   Total organisms: {total_organisms} (avg: {total_organisms/len(annotations):.1f})
   Total phenomena: {total_phenomena} (avg: {total_phenomena/len(annotations):.1f})
   Contexts: {contexts}
        """)


async def main():
    creator = AnnotationDatasetCreator(num_examples=20)
    await creator.create_annotations()


if __name__ == "__main__":
    asyncio.run(main())