"""
NASA Publications Abstract Generator
Module DSPy pour générer des abstracts manquants à partir de publications scientifiques
dans le domaine des biosciences spatiales de la NASA
"""

from contextlib import redirect_stdout
import io
import dspy
import asyncio
import re
from typing import List, Dict, Literal, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from client import DatabaseClient
from extract_data import NCBIExtractor
import logging
from client import Publication, TextSection
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
    """Article scientifique sans abstract nécessitant une génération automatique"""
    id: str
    pmcid: str
    pmid: Optional[str]
    title: str
    abstract: str  # Vide ou None
    full_text_sections: Dict[str, str]
    article_type: ArticleType
    original_pmcid: Optional[str] = None  # Pour les corrections

# === Signatures DSPy ===

class ArticleClassifier(dspy.Signature):
    """
    Classificateur d'articles scientifiques pour identifier le type de publication.
    
    Contexte: Dans la base de données NASA biosciences, certains articles sont des corrections,
    erratas ou retractions d'autres articles. Il est crucial de les identifier car leur
    traitement diffère des articles de recherche originaux.
    
    Instructions:
    - Analyser le titre pour détecter des mots-clés comme "correction", "erratum", "retraction"
    - Examiner le contenu pour identifier la nature corrective
    - Les corrections mentionnent souvent l'article original corrigé
    - Les articles originaux présentent des recherches nouvelles
    """
    title = dspy.InputField(desc="Titre complet de l'article scientifique à analyser")
    content_preview = dspy.InputField(desc="Extrait du début du contenu de l'article (500 premiers caractères)")

    article_type: Literal["correction", "erratum", "retraction", "original"] = dspy.OutputField(
        desc="Type précis de l'article: 'correction' pour corrections d'articles, 'erratum' pour erreurs factuelles, 'retraction' pour retraits, 'original' pour recherche nouvelle"
    )
    confidence = dspy.OutputField(desc="Score de confiance de 0.0 à 1.0 sur la classification")
    reasoning = dspy.OutputField(desc="Justification détaillée de la classification basée sur les indices du titre et du contenu")

class OriginalArticleFinder(dspy.Signature):
    """
    Agent de recherche spécialisé pour identifier l'article original référencé par une correction.
    
    Contexte: Les corrections d'articles scientifiques NASA font référence à un article original
    qu'elles corrigent. Il faut retrouver cet article pour contextualiser la correction.
    
    Instructions:
    - Rechercher des mentions explicites de PMCIDs dans le texte de correction
    - Identifier les termes-clés de l'article original à partir du titre de la correction
    - Utiliser les outils de recherche NCBI pour valider les candidats
    - Prioriser les PMCIDs explicitement mentionnés
    
    Outils disponibles:
    - search_ncbi_for_pmcid: Rechercher par termes dans la base NCBI
    - validate_pmcid_exists: Vérifier l'existence d'un PMCID
    """
    correction_title = dspy.InputField(desc="Titre complet de l'article de correction à analyser")
    correction_content = dspy.InputField(desc="Contenu textuel de la correction (premiers 2000 caractères)")
    
    original_title = dspy.OutputField(desc="Titre probable reconstruit de l'article original corrigé")
    search_terms : List[str] = dspy.OutputField(desc="Termes de recherche optimisés pour retrouver l'article original dans NCBI")
    pmcid_candidates:List[str] = dspy.OutputField(desc="Liste des PMCIDs candidats trouvés (ex: PMC123456, PMC789012)")

class AbstractGenerator(dspy.Signature):
    """
    Générateur d'abstracts scientifiques pour publications de biosciences spatiales NASA.
    
    Contexte: Génération d'abstracts manquants pour des articles de recherche en biosciences
    spatiales. Les abstracts doivent suivre les standards scientifiques avec introduction,
    méthodologie, résultats et conclusions.
    
    Instructions CRITIQUES:
    - OBLIGATOIRE: Générer l'abstract en ANGLAIS uniquement, sauf si le contenu source est dans une autre langue
    - OBLIGATOIRE: Produire UN SEUL PARAGRAPHE CONTINU sans mise en forme (pas de gras, italique, puces, etc.)
    - Format scientifique standard: objectif/contexte, méthodologie, résultats principaux, conclusions/implications
    - Utiliser un vocabulaire scientifique précis et des termes techniques appropriés
    - Longueur: 150-250 mots strictement
    - Ton académique et objectif, style typique des publications scientifiques
    - Éviter les phrases marketing ou sensationnalistes
    """
    title = dspy.InputField(desc="Titre complet de l'article de recherche scientifique")
    content = dspy.InputField(desc="Contenu textuel structuré ou sections disponibles de l'article")
    content_source = dspy.InputField(desc="Source du contenu: 'structured_sections' si sections classiques trouvées, 'fallback_sections' si sections génériques utilisées")
    
    abstract = dspy.OutputField(desc="Abstract scientifique en UN SEUL PARAGRAPHE CONTINU de 150-250 mots, EN ANGLAIS, sans formatage, style académique standard")
    key_findings = dspy.OutputField(desc="Découvertes principales et résultats significatifs de l'étude (en anglais)")
    methodology = dspy.OutputField(desc="Approche méthodologique principale utilisée dans l'étude (en anglais)")

class CorrectionSummarizer(dspy.Signature):
    """
    Spécialisé dans la synthèse de corrections d'articles scientifiques.
    
    Contexte: Les corrections d'articles modifient ou clarifient des éléments de l'article
    original. Il faut créer un résumé qui explique clairement les changements apportés.
    
    Instructions CRITIQUES:
    - OBLIGATOIRE: Générer le résumé en ANGLAIS
    - OBLIGATOIRE: Produire UN SEUL PARAGRAPHE CONTINU sans mise en forme
    - Identifier précisément les éléments corrigés
    - Expliquer la nature de chaque correction
    - Évaluer l'impact sur les conclusions originales
    - Maintenir un ton objectif et factuel
    - Style académique professionnel
    """
    correction_content = dspy.InputField(desc="Texte complet de la correction décrivant les changements apportés")
    original_abstract = dspy.InputField(desc="Abstract de l'article original qui est corrigé")
    
    correction_summary = dspy.OutputField(desc="Résumé de correction en UN SEUL PARAGRAPHE CONTINU de 100-200 mots, EN ANGLAIS, sans formatage")
    corrected_elements = dspy.OutputField(desc="Liste spécifique des éléments corrigés (données, figures, conclusions, etc.)")
    impact_level = dspy.OutputField(desc="Niveau d'impact: 'minor' pour corrections mineures, 'major' pour changements significatifs, 'critical' pour corrections majeures")

# === Tools pour DSPy ReAct ===

def search_ncbi_for_pmcid(search_terms: str, email: str = "amrromuald234@gmail.com") -> str:
    """
    Rechercher un PMCID via l'API NCBI en utilisant des termes de recherche.
    
    Args:
        search_terms: Termes de recherche pour trouver l'article
        email: Email pour l'API NCBI (requis)
    
    Returns:
        PMCID trouvé ou message d'erreur
    """
    import requests
    import xml.etree.ElementTree as ET
    import time
    
    try:
        # Recherche via ESearch
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
                    # Retourner le premier ID trouvé sous forme PMC
                    return f"Found PMCID: PMC{ids}"
        
        return "No results found for search terms"
        
    except Exception as e:
        return f"Search error: {str(e)}"

def validate_pmcid_exists(pmcid: str, email: str = "amrromuald234@gmail.com") -> str:
    """
    Valider qu'un PMCID existe dans la base NCBI.
    
    Args:
        pmcid: PMCID à valider (format PMC123456)
        email: Email pour l'API NCBI
    
    Returns:
        Message de validation ou d'erreur
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

# === Modules DSPy ===

class AbstractGeneratorModule(dspy.Module):
    """
    Module principal pour la génération automatique d'abstracts manquants.
    """
    
    def __init__(self, db_client: DatabaseClient, ncbi_extractor: NCBIExtractor):
        super().__init__()
        self.db_client = db_client
        self.ncbi_extractor = ncbi_extractor
        
        # Modules DSPy avec configuration spécialisée
        self.classifier = dspy.ChainOfThought(ArticleClassifier)
        self.original_finder = dspy.ReAct(OriginalArticleFinder, tools=[search_ncbi_for_pmcid, validate_pmcid_exists])
        self.abstract_generator = dspy.ChainOfThought(AbstractGenerator)
        self.correction_summarizer = dspy.ChainOfThought(CorrectionSummarizer)
    
    async def forward_async(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """
        Processus principal asynchrone de génération d'abstract.
        
        Args:
            article: Article nécessitant un abstract
            
        Returns:
            Dictionnaire avec l'abstract généré et métadonnées
        """
        
        # 1. Classification de l'article
        article_type = self._classify_article(article)
        
        if article_type in [ArticleType.CORRECTION, ArticleType.ERRATUM]:
            return await self._handle_correction_async(article)
        else:
            return await self._generate_original_abstract(article)
    
    # Garder la méthode forward synchrone pour compatibilité DSPy
    def forward(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Version synchrone qui wrap l'async"""
        return asyncio.run(self.forward_async(article))
    
    async def _handle_correction_async(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Traiter spécifiquement une correction d'article de manière asynchrone"""
        
        # 1. Trouver l'article original avec DSPy ReAct
        original_pmcid = self._find_original_article_with_react(article)
        
        if original_pmcid:
            # 2. Récupérer l'abstract original (avec extraction si nécessaire)
            original_abstract = await self._get_or_extract_original_abstract(original_pmcid)
            
            if original_abstract:
                # 3. Générer un résumé de la correction
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
        
        # Fallback: traiter comme un article original
        logger.warning(f"Impossible de traiter {article.pmcid} comme correction, fallback vers génération")
        return await self._generate_original_abstract(article)

    async def _get_or_extract_original_abstract(self, pmcid: str) -> Optional[str]:
        """
        Récupérer l'abstract de l'article original depuis la BD, 
        ou l'extraire et l'ajouter à la BD si pas trouvé
        """
        try:
            # 1. Essayer de récupérer depuis la BD
            original_abstract = await self._get_original_abstract(pmcid)
            
            if original_abstract:
                logger.info(f"Abstract original trouvé en BD pour {pmcid}")
                return original_abstract
            
            # 2. Si pas trouvé en BD, vérifier si l'article existe
            pub_exists = await self._check_publication_exists_in_db(pmcid)
            
            if pub_exists:
                logger.warning(f"Article {pmcid} existe en BD mais sans abstract")
                return None
            
            # 3. Article pas en BD, l'extraire depuis NCBI
            logger.info(f"Article {pmcid} non trouvé en BD, extraction depuis NCBI...")
            
            extracted_pub = self.ncbi_extractor.fetch_publication_details(pmcid)
            
            if extracted_pub:
                # 4. Ajouter l'article extrait à la BD
                try:
                    pub_id = await self.db_client.create_publication(extracted_pub.to_dict())
                    logger.info(f" Article original {pmcid} extrait et ajouté à la BD avec ID {pub_id}")
                    return extracted_pub.abstract if extracted_pub.abstract else None
                except Exception as db_error:
                    logger.error(f" Erreur insertion article original {pmcid}: {db_error}")
                    # Retourner l'abstract même si l'insertion échoue
                    return extracted_pub.abstract if extracted_pub.abstract else None
            else:
                logger.error(f" Impossible d'extraire l'article original {pmcid} depuis NCBI")
                return None
                
        except Exception as e:
            logger.error(f"Erreur récupération/extraction abstract pour {pmcid}: {e}")
            return None

    async def _check_publication_exists_in_db(self, pmcid: str) -> bool:
        """Vérifier si une publication existe dans la BD"""
        try:
            async with self.db_client.async_session() as session:
                result = await session.execute(
                    select(Publication.id)
                    .where(Publication.pmcid == pmcid)
                )
                return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Erreur vérification existence {pmcid}: {e}")
            return False

    async def _generate_original_abstract(self, article: MissingAbstractArticle) -> Dict[str, str]:
        """Générer un abstract pour un article original avec fallback depuis la BD"""
        
        # 1. Essayer de trouver les sections structurées depuis la BD
        content, content_source = await self._extract_structured_content_from_db(article.id)
        
        # 2. Si pas de contenu structuré, utiliser les sections disponibles
        if not content:
            content, content_source = await self._extract_fallback_content_from_db(article.id)
        
        if not content:
            logger.warning(f"Aucun contenu exploitable trouvé pour {article.pmcid}")
            return {'error': 'No suitable content for abstract generation'}
        
        # Générer l'abstract
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
            logger.error(f"Erreur génération abstract pour {article.pmcid}: {e}")
            return {'error': f'Generation failed: {str(e)}'}
    
    async def _extract_structured_content_from_db(self, publication_id: str) -> Tuple[str, str]:
        """Extraire le contenu de sections structurées classiques depuis la BD"""
        
        # Sections recherchées avec priorité
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
                # Construire la condition OR pour chaque groupe de mots-clés
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
                    .limit(1)  # Prendre la première section correspondante
                )
                
                section = result.scalar_one_or_none()
                if section:
                    # Limiter chaque section à 800 caractères et enlever le formatage
                    truncated_content = section.content[:800]
                    section_type = self._categorize_section(section.section_name)
                    # Format simple sans markdown
                    structured_content.append(f"{section_type}: {truncated_content}")
                    found_sections.append(section_type)
                    logger.debug(f"Section trouvée: {section.section_name} -> {section_type}")
            
            if structured_content:
                content = " ".join(structured_content)  # Joindre avec des espaces
                source = f"structured_sections_db ({', '.join(found_sections)})"
                logger.info(f"Contenu structuré trouvé en BD: {found_sections}")
                return content, source
        
        return "", ""
    
    async def _extract_fallback_content_from_db(self, publication_id: str, max_chars: int = 2500) -> Tuple[str, str]:
        """Extraire le contenu des premières sections disponibles depuis la BD comme fallback"""
        
        async with self.db_client.async_session() as session:
            # Récupérer les 5 premières sections par ordre
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
                    
                # Calculer combien de caractères on peut encore prendre
                remaining_chars = max_chars - current_chars
                section_char_limit = min(remaining_chars, 800)  # Max 800 par section
                
                if section_char_limit > 100:  # Au moins 100 caractères utiles
                    truncated_content = section.content[:section_char_limit]
                    # Format simple sans markdown
                    fallback_content.append(f"{section.section_name}: {truncated_content}")
                    section_names.append(section.section_name)
                    current_chars += len(truncated_content)
            
            if fallback_content:
                content = " ".join(fallback_content)  # Joindre avec des espaces
                source = f"fallback_sections_db ({', '.join(section_names)})"
                logger.info(f"Contenu fallback utilisé depuis BD: {section_names}")
                return content, source
        
        return "", ""
    
    def _categorize_section(self, section_name: str) -> str:
        """Catégoriser une section selon son nom"""
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
    
    # === Méthodes utilitaires ===
    
    def _get_content_preview(self, sections: Dict[str, str], max_chars: int = 500) -> str:
        """Obtenir un aperçu du contenu pour la classification"""
        content = ""
        for section_name, section_content in sections.items():
            content += f"{section_name}: {section_content[:200]}\n"
            if len(content) > max_chars:
                break
        return content[:max_chars]
    
    def _get_full_content(self, sections: Dict[str, str]) -> str:
        """Obtenir le contenu complet formaté sans markdown"""
        return " ".join([f"{name}: {content}" for name, content in sections.items()])
    
    async def _get_original_abstract(self, pmcid: str) -> Optional[str]:
        """Récupérer l'abstract de l'article original depuis la BD"""
        try:
            async with self.db_client.async_session() as session:
                result = await session.execute(
                    select(Publication.abstract)
                    .where(Publication.pmcid == pmcid)
                )
                abstract = result.scalar_one_or_none()
                return abstract if abstract else None
        except Exception as e:
            logger.error(f"Erreur récupération abstract pour {pmcid}: {e}")
            return None


# === Orchestrateur principal ===

class AbstractGenerationOrchestrator:
    """
    Orchestrateur pour le processus complet de génération d'abstracts.
    
    Coordonne l'ensemble du pipeline: identification des articles manquants,
    génération des abstracts, et sauvegarde en base de données.
    """
    
    def __init__(self, db_client: DatabaseClient, llm_model: str = "gpt-4"):
        self.db_client = db_client
        
        # Configurer DSPy avec modèle spécialisé
        lm = dspy.LM(
            model="openrouter/x-ai/grok-4-fast:free",
            api_base="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        dspy.settings.configure(lm=lm)
        
        # Initialiser les modules
        self.ncbi_extractor = NCBIExtractor(
            email="amrromuald234@gmail.com",
            api_key=os.getenv("NCBI_API_KEY")
        )
        self.generator = AbstractGeneratorModule(db_client, self.ncbi_extractor)
    
    async def find_missing_abstracts(self) -> List[MissingAbstractArticle]:
        """Identifier tous les articles sans abstract ayant du contenu exploitable"""
        
        # Requête pour articles sans abstract (NULL ou vide)
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
            
            # Grouper par publication et construire les objets
            publications_data = {}
            for pub, section in result.all():
                if pub.id not in publications_data:
                    publications_data[pub.id] = {
                        'publication': pub,
                        'sections': {}
                    }
                
                if section:
                    publications_data[pub.id]['sections'][section.section_name] = section.content
            
            # Convertir en MissingAbstractArticle
            missing_articles = []
            for pub_data in publications_data.values():
                pub = pub_data['publication']
                
                # Ne traiter que les articles qui ont des sections de texte
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
                    logger.warning(f"Article {pub.pmcid} ignoré: pas de sections de texte")
            
            logger.info(f"Trouvé {len(missing_articles)} articles sans abstract avec du contenu")
            return missing_articles
    
    async def generate_missing_abstracts(self, batch_size: int = 5):
        """Générer tous les abstracts manquants avec traitement par batch"""
        
        missing_articles = await self.find_missing_abstracts()
        
        if not missing_articles:
            logger.info("Aucun abstract manquant trouvé")
            return
        
        logger.info(f"Début de génération pour {len(missing_articles)} articles")
        
        results = {
            'generated': [],
            'corrections': [],
            'failed': []
        }
        
        # Traitement par batch pour optimiser les performances
        for i in range(0, len(missing_articles), batch_size):
            batch = missing_articles[i:i+batch_size]
            
            logger.info(f"Traitement batch {i//batch_size + 1}/{(len(missing_articles) + batch_size - 1) // batch_size}: {len(batch)} articles")
            
            for article in batch:
                try:
                    logger.info(f" Génération abstract pour {article.pmcid} ({article.title[:50]}...)")
                    
                    # Utiliser la version async
                    result = await self.generator.forward_async(article)
                    
                    if 'error' in result:
                        logger.error(f" Erreur contenu {article.pmcid}: {result['error']}")
                        results['failed'].append(article.pmcid)
                        continue
                    
                    # Sauvegarder en base
                    await self._save_generated_abstract(article, result)
                    
                    if result.get('generation_type') == 'correction_summary':
                        results['corrections'].append(article.pmcid)
                        logger.info(f" Résumé de correction généré pour {article.pmcid}")
                    else:
                        results['generated'].append(article.pmcid)
                        logger.info(f" Abstract généré pour {article.pmcid}")
                    
                except Exception as e:
                    logger.error(f" Erreur génération {article.pmcid}: {e}")
                    results['failed'].append(article.pmcid)
        
        # Rapport final détaillé
        logger.info(f"""
 Génération d'abstracts terminée:
    Abstracts générés: {len(results['generated'])}
    Résumés de corrections: {len(results['corrections'])}
    Échecs: {len(results['failed'])}
    Taux de succès: {((len(results['generated']) + len(results['corrections'])) / len(missing_articles) * 100):.1f}%
        """)
        
        if results['failed']:
            logger.warning(f" Articles échoués: {results['failed'][:10]}{'...' if len(results['failed']) > 10 else ''}")
        
        return results
    
    async def _save_generated_abstract(self, article: MissingAbstractArticle, result: Dict[str, str]):
        """Sauvegarder l'abstract généré avec métadonnées en base"""
        
        update_data = {
            'abstract_generated': result.get('abstract_generated'),
            'generation_type': result.get('generation_type'),
        }
        
        # Ajouter métadonnées supplémentaires si disponibles
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
            logger.error(f" Échec sauvegarde pour {article.pmcid}")


# === Script principal ===

async def main():
    """Script principal pour générer les abstracts manquants"""
    
    # Configuration
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    db_client = DatabaseClient()
    orchestrator = AbstractGenerationOrchestrator(db_client)
    
    try:
        # Générer les abstracts manquants
        results = await orchestrator.generate_missing_abstracts(batch_size=2)  # Batch optimisé
        
        print(" Processus terminé avec succès!")
    
    except Exception as e:
        logger.error(f" Erreur fatale: {e}")
        raise
    finally:
        await db_client.close()
    
    # Écrire l'historique DSPy pour analyse
    f = io.StringIO()
    with redirect_stdout(f):
        dspy.inspect_history()
    output = f.getvalue()
    try:
        with open("dspy_inspect.txt", "w", encoding='utf-8') as f:
            f.write("=== HISTORIQUE DSPy GENERATION ABSTRACTS ===\n\n")
            f.write(output)
    except Exception as e:
        logger.warning(f"Erreur sauvegarde historique DSPy: {e}")


if __name__ == "__main__":
    asyncio.run(main())