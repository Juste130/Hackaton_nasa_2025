"""
DSPy modules for structured biological entity extraction
"""
import dspy
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# === DSPy Signature: Biological Entity Extraction ===

class BiologicalEntityExtractor(dspy.Signature):
    """
    Extracts structured biological entities from NASA bioscience space publications.
    
    Context: 
    - Publications describing experiments in microgravity/radiation/space environments
    - Focus on model organisms (mice, rats, humans, plants, cells)
    - Biological phenomena studied (muscle atrophy, bone loss, immune dysfunction)
    
    Instructions:
    1. ORGANISMS: Normalize scientific names (e.g., "mice" -> "Mus musculus")
       - Categorize: "mammal", "plant", "cell_line", "microorganism", "human"
    
    2. PHENOMENA: Identify biological processes studied
       - Use standardized terminology (e.g., "bone resorption" not "bone problems")
       - Distinguish phenomena from symptoms
    
    3. BIOLOGICAL SYSTEMS: Affected organs/systems
       - E.g., "musculoskeletal", "immune", "cardiovascular", "neurological"
    
    4. EXPERIMENTAL CONTEXT: Type of space environment
       - "spaceflight" (real), "ground_simulation" (parabolic flight, clinostat), "computational_model"
    
    5. PLATFORM: Identify mission/device if mentioned
       - E.g., "ISS", "Space Shuttle", "Rodent Habitat", "Cell Culture Unit"
    
    Strict rules:
    - DO NOT invent information not present in the text
    - If uncertain about organism category -> "unknown"
    - If no platform mentioned -> null
    - Prioritize terms used in abstract/keywords
    """
    
    # INPUTS
    title: str = dspy.InputField(desc="Publication title")
    abstract: str = dspy.InputField(desc="Complete abstract")
    keywords: list = dspy.InputField(desc="Author-provided keywords (can be empty)")
    mesh_terms: list = dspy.InputField(desc="Medical MeSH terms (can be empty)")
    
    # OUTPUTS
    organisms: list[dict] = dspy.OutputField(
        desc="List of organisms: [{name: str, scientific_name: str, category: str}]. "
             "Categories: 'mammal', 'plant', 'cell_line', 'microorganism', 'human', 'unknown'"
    )
    
    phenomena: list[dict] = dspy.OutputField(
        desc="List of biological phenomena: [{name: str, description: str, system: str}]. "
             "Systems: 'musculoskeletal', 'immune', 'cardiovascular', 'neurological', 'metabolic', 'other'"
    )
    
    experimental_context: str = dspy.OutputField(
        desc="Experiment type: 'spaceflight' | 'ground_simulation' | 'computational_model' | 'review'"
    )
    
    platform: Optional[str] = dspy.OutputField(
        desc="Mission/space platform name if mentioned (e.g., 'ISS', 'Space Shuttle'), else null"
    )
    
    stressors: list[str] = dspy.OutputField(
        desc="Environmental stress factors studied: ['microgravity', 'radiation', 'isolation', 'altered_atmosphere', etc.]"
    )


# === DSPy Module with ChainOfThought ===

class BiologicalEntityExtractorModule(dspy.Module):
    """Extraction module with chain-of-thought reasoning"""
    
    def __init__(self):
        super().__init__()
        self.extractor = dspy.ChainOfThought(BiologicalEntityExtractor)
    
    def forward(self, title: str = "", abstract: str = "", keywords: Optional[list] = None, mesh_terms: Optional[list] = None, publication_data: Dict = None):
        """
        Extract entities from a publication
        
        Args:
            title: Publication title
            abstract: Complete abstract
            keywords: Author-provided keywords
            mesh_terms: Medical MeSH terms
            publication_data: Alternative dict format with all fields (for backward compatibility)
        
        Returns:
            Dict with extracted entities + metadata (or dspy.Prediction for DSPy compiler)
        """
        # Handle both calling conventions
        if publication_data is not None:
            # Called with dict (backward compatibility)
            title = publication_data.get('title', '')
            abstract = publication_data.get('abstract', '')
            keywords = publication_data.get('keywords', [])
            mesh_terms = publication_data.get('mesh_terms', [])
            return_dict = True
        else:
            # Called by DSPy with kwargs
            keywords = keywords or []
            mesh_terms = mesh_terms or []
            return_dict = False
        
        try:
            # Validation
            if not abstract or len(abstract) < 50:
                if return_dict:
                    logger.warning(f"Abstract too short")
                    return self._empty_result()
                else:
                    # Return minimal Prediction for DSPy
                    return dspy.Prediction(
                        organisms=[],
                        phenomena=[],
                        experimental_context='unknown',
                        platform=None,
                        stressors=[]
                    )
            
            # DSPy extraction
            result = self.extractor(
                title=title,
                abstract=abstract,
                keywords=keywords,
                mesh_terms=mesh_terms
            )
            
            if return_dict:
                # Post-processing and validation for dict return
                extracted = {
                    'organisms': self._validate_organisms(result.organisms),
                    'phenomena': self._validate_phenomena(result.phenomena),
                    'experimental_context': result.experimental_context,
                    'platform': result.platform if result.platform != "null" else None,
                    'stressors': result.stressors,
                    'extraction_confidence': self._compute_confidence(result)
                }
                
                logger.info(f" Extracted: {len(extracted['organisms'])} organisms, {len(extracted['phenomena'])} phenomena")
                return extracted
            else:
                # Return Prediction directly for DSPy compiler
                # Apply validation to the result
                validated_result = dspy.Prediction(
                    organisms=self._validate_organisms(result.organisms),
                    phenomena=self._validate_phenomena(result.phenomena),
                    experimental_context=result.experimental_context,
                    platform=result.platform if result.platform != "null" else None,
                    stressors=result.stressors
                )
                return validated_result
            
        except Exception as e:
            logger.error(f" DSPy extraction error: {e}")
            if return_dict:
                return self._empty_result()
            else:
                return dspy.Prediction(
                    organisms=[],
                    phenomena=[],
                    experimental_context='unknown',
                    platform=None,
                    stressors=[]
                )
    
    def _validate_organisms(self, organisms_raw) -> List[Dict]:
        """Validate and normalize organism list"""
        validated = []
        
        if not organisms_raw:
            return validated
        
        for org in organisms_raw:
            if isinstance(org, dict) and 'name' in org:
                # Normalize category
                category = org.get('category', 'unknown').lower()
                valid_categories = ['mammal', 'plant', 'cell_line', 'microorganism', 'human', 'unknown']
                if category not in valid_categories:
                    category = 'unknown'
                
                validated.append({
                    'name': org['name'].strip(),
                    'scientific_name': org.get('scientific_name', org['name']).strip(),
                    'category': category
                })
        
        return validated
    
    def _validate_phenomena(self, phenomena_raw) -> List[Dict]:
        """Validate and normalize phenomena list"""
        validated = []
        
        if not phenomena_raw:
            return validated
        
        valid_systems = ['musculoskeletal', 'immune', 'cardiovascular', 'neurological', 'metabolic', 'other']
        
        for phen in phenomena_raw:
            if isinstance(phen, dict) and 'name' in phen:
                system = phen.get('system', 'other').lower()
                if system not in valid_systems:
                    system = 'other'
                
                validated.append({
                    'name': phen['name'].strip(),
                    'description': phen.get('description', '').strip(),
                    'system': system
                })
        
        return validated
    
    def _compute_confidence(self, result) -> float:
        """
        Calculate confidence score based on quantity of extracted entities
        """
        org_count = len(result.organisms) if result.organisms else 0
        phen_count = len(result.phenomena) if result.phenomena else 0
        
        # Simple heuristic: more entities = higher confidence
        if org_count >= 2 and phen_count >= 2:
            return 0.9
        elif org_count >= 1 and phen_count >= 1:
            return 0.7
        elif org_count >= 1 or phen_count >= 1:
            return 0.5
        else:
            return 0.3
    
    def _empty_result(self) -> Dict:
        """Empty result in case of error"""
        return {
            'organisms': [],
            'phenomena': [],
            'experimental_context': 'unknown',
            'platform': None,
            'stressors': [],
            'extraction_confidence': 0.0
        }


# === Unit Test ===

def test_extractor():
    """Quick module test"""
    import dspy
    from config import DSPY_MODEL, OPENROUTER_API_KEY
    
    # DSPy configuration
    lm = dspy.LM(
        model=DSPY_MODEL,
        api_base="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    dspy.settings.configure(lm=lm)
    
    # Example publication
    test_pub = {
        'pmcid': 'PMC_TEST',
        'title': 'Effects of Microgravity on Bone Loss in Mice',
        'abstract': """
        Spaceflight-induced bone loss is a major concern for long-duration missions. 
        We studied C57BL/6 mice aboard the International Space Station for 30 days. 
        Results showed significant decrease in bone mineral density and increased osteoclast activity.
        """,
        'keywords': ['microgravity', 'bone loss', 'mice', 'ISS'],
        'mesh_terms': ['Bone Density', 'Osteoclasts', 'Weightlessness']
    }
    
    # Extraction
    extractor = BiologicalEntityExtractorModule()
    result = extractor.forward(publication_data=test_pub)
    
    print("=== Extraction Result ===")
    print(f"Organisms: {result['organisms']}")
    print(f"Phenomena: {result['phenomena']}")
    print(f"Context: {result['experimental_context']}")
    print(f"Platform: {result['platform']}")
    print(f"Confidence: {result['extraction_confidence']}")


if __name__ == "__main__":
    test_extractor()