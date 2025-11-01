"""
DSPy Module for intelligent section extraction from XML tags
"""

import dspy
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
import logging
import re

logger = logging.getLogger(__name__)

class SectionExtractor(dspy.Signature):
    """
    Intelligent section extractor from unstructured XML content.
    
    Context: Analyze XML content from scientific articles to identify
    and extract logical sections even when they are not explicitly
    marked with <sec> or <section> tags.
    
    Instructions:
    - Analyze structure patterns in XML content
    - Identify potential section titles (h1-h6, title tags, etc.)
    - Group content logically by section
    - Detect transitions between sections based on subject change
    - Ignore pure formatting tags (bold, italic, etc.)
    - Prioritize thematic coherence of content
    """
    xml_content = dspy.InputField(desc="Raw XML content of article without explicit sections")
    available_tags = dspy.InputField(desc="List of available XML tags in content")
    content_length = dspy.InputField(desc="Approximate content length in characters")
    
    sections = dspy.OutputField(desc="Dictionary of extracted sections {section_name: content}")
    section_patterns = dspy.OutputField(desc="Patterns used to identify sections")
    confidence_score = dspy.OutputField(desc="Confidence score from 0.0 to 1.0 on extraction")

class ContentStructureAnalyzer(dspy.Signature):
    """
    Structure analyzer to identify content organization patterns.
    
    Context: Some articles use non-conventional structures
    to organize their content. We need to detect these patterns to extract
    sections intelligently.
    
    Instructions:
    - Identify elements that serve as section delimiters
    - Detect repetition patterns in structure
    - Analyze tag hierarchy to understand organization
    - Spot visual structure clues (numbering, formatting)
    """
    xml_structure = dspy.InputField(desc="Hierarchical structure of XML tags")
    content_preview = dspy.InputField(desc="Content preview (first 1000 characters)")
    
    structure_type = dspy.OutputField(desc="Detected structure type: 'hierarchical', 'sequential', 'mixed', 'unstructured'")
    delimiter_patterns = dspy.OutputField(desc="Delimiter patterns identified in content")
    extraction_strategy = dspy.OutputField(desc="Recommended strategy for section extraction")

class IntelligentSectionExtractorModule(dspy.Module):
    """
    DSPy Module for intelligent section extraction from XML content
    """
    
    def __init__(self):
        super().__init__()
        self.structure_analyzer = dspy.ChainOfThought(ContentStructureAnalyzer)
        self.section_extractor = dspy.ChainOfThought(SectionExtractor)
        
        # Tags to ignore (pure formatting)
        self.formatting_tags = {
            'b', 'strong', 'i', 'em', 'u', 'sup', 'sub', 'span', 'font',
            'br', 'hr', 'img', 'a', 'link', 'style', 'script'
        }
        
        # Potential structure tags
        self.structure_tags = {
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'title', 'subtitle',
            'p', 'div', 'section', 'article', 'header', 'footer'
        }
    
    def forward(self, xml_content: str) -> Dict[str, Any]:
        """
        Intelligently extract sections from XML content
        """
        try:
            # 1. Analyze XML structure
            structure_analysis = self._analyze_xml_structure(xml_content)
            
            if not structure_analysis['available_tags']:
                logger.warning("No structural tags found")
                return {'sections': {}, 'method': 'failed', 'reason': 'no_structure'}
            
            # 2. Analyze structure with DSPy
            analyzer_result = self.structure_analyzer(
                xml_structure=structure_analysis['hierarchy'],
                content_preview=structure_analysis['content_preview']
            )
            
            # 3. Extract sections with DSPy
            extractor_result = self.section_extractor(
                xml_content=xml_content[:5000],  # Limit for context
                available_tags=str(structure_analysis['available_tags']),
                content_length=str(len(xml_content))
            )
            
            # 4. Process and validate results
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
            logger.error(f"DSPy extraction error: {e}")
            # Fallback to basic extraction
            return self._fallback_extraction(xml_content)
    
    def _analyze_xml_structure(self, xml_content: str) -> Dict[str, Any]:
        """Analyze XML structure of content"""
        try:
            # Parse XML
            root = ET.fromstring(f"<root>{xml_content}</root>")
            
            # Collect all tags
            all_tags = set()
            structure_tags = set()
            
            for elem in root.iter():
                tag_name = elem.tag.lower()
                all_tags.add(tag_name)
                
                if tag_name in self.structure_tags:
                    structure_tags.add(tag_name)
            
            # Build hierarchy
            hierarchy = self._build_hierarchy(root)
            
            # Content preview
            content_preview = ''.join(root.itertext())[:1000]
            
            return {
                'available_tags': list(structure_tags),
                'all_tags': list(all_tags),
                'hierarchy': hierarchy,
                'content_preview': content_preview
            }
            
        except ET.ParseError:
            logger.warning("Malformed XML content, basic analysis")
            return {
                'available_tags': [],
                'all_tags': [],
                'hierarchy': '',
                'content_preview': xml_content[:1000]
            }
    
    def _build_hierarchy(self, element, level=0) -> str:
        """Build XML hierarchy representation"""
        hierarchy = "  " * level + f"<{element.tag}>\n"
        
        for child in element:
            if len(list(child)) > 0:  # Has children
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
        """Process and validate DSPy extraction results"""
        
        sections = {}
        
        try:
            # Try to parse sections from DSPy response
            if hasattr(extractor_result, 'sections'):
                raw_sections = extractor_result.sections
                
                # If it's a string, try to parse it
                if isinstance(raw_sections, str):
                    sections = self._parse_sections_from_string(raw_sections)
                elif isinstance(raw_sections, dict):
                    sections = raw_sections
            
            # Validation and cleaning
            validated_sections = {}
            for name, content in sections.items():
                if content and len(content.strip()) > 50:  # Minimum content
                    validated_sections[name] = content.strip()
            
            # If not enough sections, use fallback strategy
            if len(validated_sections) < 2:
                logger.info("Insufficient DSPy results, using fallback")
                return self._fallback_section_extraction(xml_content)
            
            return validated_sections
            
        except Exception as e:
            logger.error(f"DSPy results processing error: {e}")
            return self._fallback_section_extraction(xml_content)
    
    def _parse_sections_from_string(self, sections_str: str) -> Dict[str, str]:
        """Parse sections from string"""
        sections = {}
        
        # Pattern to detect sections in "Name: Content" format
        section_pattern = r'([A-Za-z\s]+):\s*([^:]+?)(?=\n[A-Za-z\s]+:|$)'
        matches = re.findall(section_pattern, sections_str, re.DOTALL)
        
        for name, content in matches:
            clean_name = name.strip()
            clean_content = content.strip()
            if clean_name and clean_content:
                sections[clean_name] = clean_content
        
        return sections
    
    def _fallback_extraction(self, xml_content: str) -> Dict[str, Any]:
        """Fallback extraction if DSPy fails"""
        sections = self._fallback_section_extraction(xml_content)
        
        return {
            'sections': sections,
            'method': 'fallback_basic',
            'structure_type': 'unknown',
            'confidence': 0.5,
            'patterns_used': 'basic_paragraph_splitting'
        }
    
    def _fallback_section_extraction(self, xml_content: str) -> Dict[str, str]:
        """Basic extraction by paragraphs if everything fails"""
        try:
            root = ET.fromstring(f"<root>{xml_content}</root>")
            
            # Extract all paragraphs
            paragraphs = []
            for p in root.findall('.//p'):
                text = ''.join(p.itertext()).strip()
                if text and len(text) > 100:
                    paragraphs.append(text)
            
            # Group into reasonably sized sections
            sections = {}
            current_section = []
            section_num = 1
            
            for para in paragraphs:
                current_section.append(para)
                
                # New section every 3-4 paragraphs or if too long
                if len(current_section) >= 3 or sum(len(p) for p in current_section) > 2000:
                    sections[f"Section_{section_num}"] = ' '.join(current_section)
                    current_section = []
                    section_num += 1
            
            # Add the last section if it exists
            if current_section:
                sections[f"Section_{section_num}"] = ' '.join(current_section)
            
            return sections
            
        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return {}