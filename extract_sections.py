"""
Module DSPy pour l'extraction intelligente de sections à partir de tags XML
"""

import dspy
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class SectionExtractor(dspy.Signature):
    """
    Extracteur intelligent de sections à partir de contenu XML non-structuré.
    
    Contexte: Analyser le contenu XML d'articles scientifiques pour identifier
    et extraire des sections logiques même quand elles ne sont pas explicitement
    marquées avec des balises <sec> ou <section>.
    
    Instructions:
    - Analyser les patterns de structure dans le contenu XML
    - Identifier les titres de sections potentiels (balises h1-h6, title, etc.)
    - Regrouper le contenu logiquement par section
    - Détecter les transitions entre sections basées sur le changement de sujet
    - Ignorer les balises de mise en forme pure (bold, italic, etc.)
    - Prioriser la cohérence thématique du contenu
    """
    xml_content = dspy.InputField(desc="Contenu XML brut de l'article sans sections explicites")
    available_tags = dspy.InputField(desc="Liste des balises XML disponibles dans le contenu")
    content_length = dspy.InputField(desc="Longueur approximative du contenu en caractères")
    
    sections = dspy.OutputField(desc="Dictionnaire des sections extraites {nom_section: contenu}")
    section_patterns = dspy.OutputField(desc="Patterns utilisés pour identifier les sections")
    confidence_score = dspy.OutputField(desc="Score de confiance de 0.0 à 1.0 sur l'extraction")

class ContentStructureAnalyzer(dspy.Signature):
    """
    Analyseur de structure pour identifier les patterns d'organisation du contenu.
    
    Contexte: Certains articles utilisent des structures non-conventionnelles
    pour organiser leur contenu. Il faut détecter ces patterns pour extraire
    les sections de manière intelligente.
    
    Instructions:
    - Identifier les éléments qui servent de délimiteurs de sections
    - Détecter les patterns de répétition dans la structure
    - Analyser la hiérarchie des balises pour comprendre l'organisation
    - Repérer les indices visuels de structure (numérotation, formatage)
    """
    xml_structure = dspy.InputField(desc="Structure hiérarchique des balises XML")
    content_preview = dspy.InputField(desc="Aperçu du contenu textuel (premiers 1000 caractères)")
    
    structure_type = dspy.OutputField(desc="Type de structure détectée: 'hierarchical', 'sequential', 'mixed', 'unstructured'")
    delimiter_patterns = dspy.OutputField(desc="Patterns de délimiteurs identifiés dans le contenu")
    extraction_strategy = dspy.OutputField(desc="Stratégie recommandée pour l'extraction des sections")

class IntelligentSectionExtractorModule(dspy.Module):
    """
    Module DSPy pour l'extraction intelligente de sections à partir de contenu XML
    """
    
    def __init__(self):
        super().__init__()
        self.structure_analyzer = dspy.ChainOfThought(ContentStructureAnalyzer)
        self.section_extractor = dspy.ChainOfThought(SectionExtractor)
        
        # Tags à ignorer (mise en forme pure)
        self.formatting_tags = {
            'b', 'strong', 'i', 'em', 'u', 'sup', 'sub', 'span', 'font',
            'br', 'hr', 'img', 'a', 'link', 'style', 'script'
        }
        
        # Tags potentiels de structure
        self.structure_tags = {
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'title', 'subtitle',
            'p', 'div', 'section', 'article', 'header', 'footer'
        }
    
    def forward(self, xml_content: str) -> Dict[str, any]:
        """
        Extraire intelligemment les sections du contenu XML
        """
        try:
            # 1. Analyser la structure XML
            structure_analysis = self._analyze_xml_structure(xml_content)
            
            if not structure_analysis['available_tags']:
                logger.warning("Aucune balise structurelle trouvée")
                return {'sections': {}, 'method': 'failed', 'reason': 'no_structure'}
            
            # 2. Analyser la structure avec DSPy
            analyzer_result = self.structure_analyzer(
                xml_structure=structure_analysis['hierarchy'],
                content_preview=structure_analysis['content_preview']
            )
            
            # 3. Extraire les sections avec DSPy
            extractor_result = self.section_extractor(
                xml_content=xml_content[:5000],  # Limiter pour le contexte
                available_tags=str(structure_analysis['available_tags']),
                content_length=str(len(xml_content))
            )
            
            # 4. Traitement et validation des résultats
            sections = self._process_extraction_results(
                extractor_result,
                xml_content,
                analyzer_result.extraction_strategy
            )
            
            return {
                'sections': sections,
                'method': 'dspy_intelligent',
                'structure_type': analyzer_result.structure_type,
                'confidence': float(extractor_result.confidence_score),
                'patterns_used': extractor_result.section_patterns
            }
            
        except Exception as e:
            logger.error(f"Erreur extraction DSPy: {e}")
            # Fallback sur extraction basique
            return self._fallback_extraction(xml_content)
    
    def _analyze_xml_structure(self, xml_content: str) -> Dict[str, any]:
        """Analyser la structure XML du contenu"""
        try:
            # Parser le XML
            root = ET.fromstring(f"<root>{xml_content}</root>")
            
            # Collecter toutes les balises
            all_tags = set()
            structure_tags = set()
            
            for elem in root.iter():
                tag_name = elem.tag.lower()
                all_tags.add(tag_name)
                
                if tag_name in self.structure_tags:
                    structure_tags.add(tag_name)
            
            # Construire hiérarchie
            hierarchy = self._build_hierarchy(root)
            
            # Aperçu du contenu
            content_preview = ''.join(root.itertext())[:1000]
            
            return {
                'available_tags': list(structure_tags),
                'all_tags': list(all_tags),
                'hierarchy': hierarchy,
                'content_preview': content_preview
            }
            
        except ET.ParseError:
            logger.warning("Contenu XML malformé, analyse basique")
            return {
                'available_tags': [],
                'all_tags': [],
                'hierarchy': '',
                'content_preview': xml_content[:1000]
            }
    
    def _build_hierarchy(self, element, level=0) -> str:
        """Construire une représentation de la hiérarchie XML"""
        hierarchy = "  " * level + f"<{element.tag}>\n"
        
        for child in element:
            if len(list(child)) > 0:  # A des enfants
                hierarchy += self._build_hierarchy(child, level + 1)
            else:
                hierarchy += "  " * (level + 1) + f"<{child.tag}/>\n"
        
        return hierarchy
    
    def _process_extraction_results(
        self, 
        extractor_result, 
        xml_content: str, 
        strategy: str
    ) -> Dict[str, str]:
        """Traiter et valider les résultats d'extraction DSPy"""
        
        sections = {}
        
        try:
            # Tenter de parser les sections depuis la réponse DSPy
            if hasattr(extractor_result, 'sections'):
                raw_sections = extractor_result.sections
                
                # Si c'est un string, essayer de le parser
                if isinstance(raw_sections, str):
                    sections = self._parse_sections_from_string(raw_sections)
                elif isinstance(raw_sections, dict):
                    sections = raw_sections
            
            # Validation et nettoyage
            validated_sections = {}
            for name, content in sections.items():
                if content and len(content.strip()) > 50:  # Contenu minimum
                    validated_sections[name] = content.strip()
            
            # Si pas assez de sections, utiliser stratégie de fallback
            if len(validated_sections) < 2:
                logger.info("Résultats DSPy insuffisants, utilisation de fallback")
                return self._fallback_section_extraction(xml_content)
            
            return validated_sections
            
        except Exception as e:
            logger.error(f"Erreur traitement résultats DSPy: {e}")
            return self._fallback_section_extraction(xml_content)
    
    def _parse_sections_from_string(self, sections_str: str) -> Dict[str, str]:
        """Parser les sections depuis une chaîne de caractères"""
        sections = {}
        
        # Pattern pour détecter les sections au format "Nom: Contenu"
        section_pattern = r'([A-Za-z\s]+):\s*([^:]+?)(?=\n[A-Za-z\s]+:|$)'
        matches = re.findall(section_pattern, sections_str, re.DOTALL)
        
        for name, content in matches:
            clean_name = name.strip()
            clean_content = content.strip()
            if clean_name and clean_content:
                sections[clean_name] = clean_content
        
        return sections
    
    def _fallback_extraction(self, xml_content: str) -> Dict[str, any]:
        """Extraction de fallback si DSPy échoue"""
        sections = self._fallback_section_extraction(xml_content)
        
        return {
            'sections': sections,
            'method': 'fallback_basic',
            'structure_type': 'unknown',
            'confidence': 0.5,
            'patterns_used': 'basic_paragraph_splitting'
        }
    
    def _fallback_section_extraction(self, xml_content: str) -> Dict[str, str]:
        """Extraction basique par paragraphes si tout échoue"""
        try:
            root = ET.fromstring(f"<root>{xml_content}</root>")
            
            # Extraire tous les paragraphes
            paragraphs = []
            for p in root.findall('.//p'):
                text = ''.join(p.itertext()).strip()
                if text and len(text) > 100:
                    paragraphs.append(text)
            
            # Grouper en sections de taille raisonnable
            sections = {}
            current_section = []
            section_num = 1
            
            for para in paragraphs:
                current_section.append(para)
                
                # Nouvelle section tous les 3-4 paragraphes ou si trop long
                if len(current_section) >= 3 or sum(len(p) for p in current_section) > 2000:
                    sections[f"Section_{section_num}"] = ' '.join(current_section)
                    current_section = []
                    section_num += 1
            
            # Ajouter la dernière section si elle existe
            if current_section:
                sections[f"Section_{section_num}"] = ' '.join(current_section)
            
            return sections
            
        except Exception as e:
            logger.error(f"Erreur extraction fallback: {e}")
            return {}