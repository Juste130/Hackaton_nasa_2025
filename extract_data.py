"""
NASA Bioscience Publications Extractor
Extrait les données de 608 publications depuis NCBI/PubMed Central
et les insère directement dans PostgreSQL
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
from client import DatabaseClient
from extract_sections import IntelligentSectionExtractorModule

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = "amrromuald234@gmail.com"  # NCBI demande un email pour tracking

#api key from .env file
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv("NCBI_API_KEY")


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
    full_text_content: Optional[str]  # NOUVEAU - Ajout du champ manquant
    mesh_terms: List[str]  # Medical Subject Headings
    references: List[str]  # PMIDs cités

    def to_dict(self):
        return asdict(self)


class NCBIExtractor:
    def __init__(self, email: str, api_key: Optional[str] = None, db_client: Optional[DatabaseClient] = None):
        self.email = email
        self.api_key = api_key
        self.rate_limit = 0.34 if not api_key else 0.3  # secondes entre requêtes
        self.db_client = db_client
        
        # Initialiser le module DSPy d'extraction de sections
        self.section_extractor_dspy = IntelligentSectionExtractorModule()

    def _make_request(self, endpoint: str, params: Dict) -> requests.Response:
        """Effectue une requête à l'API NCBI avec rate limiting"""
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
            logger.error(f"Erreur requête {endpoint}: {e}")
            raise

    async def check_publication_exists(self, pmcid: str) -> bool:
        """Vérifier si une publication existe déjà dans la base"""
        if not self.db_client:
            return False
        
        existing = await self.db_client.get_publication_by_pmcid(pmcid)
        return existing is not None

    def _clean_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Nettoyer et valider le texte"""
        if not text:
            return ""
        
        # Nettoyer les caractères de contrôle et espaces multiples
        cleaned = ' '.join(text.strip().split())
        
        # Limiter la longueur si spécifiée
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned

    def _clean_and_deduplicate_keywords(self, keywords_list: List[str]) -> List[str]:
        """Nettoyer et dédupliquer les mots-clés"""
        unique_keywords = set()
        
        for keyword in keywords_list:
            if keyword and isinstance(keyword, str):
                # Nettoyer
                cleaned = self._clean_text(keyword.strip(), 255)
                if cleaned and len(cleaned) > 1:  # Au moins 2 caractères
                    # Normaliser pour déduplication
                    normalized = cleaned.lower()
                    unique_keywords.add(normalized)
        
        return list(unique_keywords)

    def _extract_text_sections(self, body_element) -> Dict[str, str]:
        """
        Extraire les sections de texte avec stratégies multiples incluant DSPy
        """
        sections = {}
        
        if body_element is None:
            return sections
        
        # Stratégie 1: Sections explicites avec titres
        explicit_sections = body_element.findall('.//sec')
        
        if explicit_sections and len(explicit_sections) >= 2:
            logger.info("Utilisation des sections explicites")
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
        
        # Stratégie 2: Extraction intelligente avec DSPy
        logger.info("Tentative d'extraction intelligente avec DSPy")
        try:
            # Convertir l'élément body en XML string
            body_xml = ET.tostring(body_element, encoding='unicode', method='xml')
            
            # Utiliser le module DSPy pour extraction intelligente
            dspy_result = self.section_extractor_dspy.forward(body_xml)
            
            if dspy_result['sections'] and len(dspy_result['sections']) >= 2:
                logger.info(f" DSPy a extrait {len(dspy_result['sections'])} sections avec confiance {dspy_result.get('confidence', 0)}")
                return dspy_result['sections']
            else:
                logger.info("DSPy n'a pas trouvé suffisamment de sections, fallback")
                
        except Exception as e:
            logger.warning(f"Erreur extraction DSPy: {e}, utilisation du fallback")
        
        # Stratégie 3: Fallback - Full Text
        logger.info("Utilisation du fallback Full Text")
        full_text_content = self._extract_full_text_content(body_element)
        
        if full_text_content and len(full_text_content) > 100:
            sections["Full Text"] = full_text_content
        
        return sections

    def _extract_full_text_content(self, body_element) -> str:
        """
        Extraire le contenu textuel complet du body
        """
        if body_element is None:
            return ""
            
        # Extraire tout le texte du body
        full_text = self._clean_text(''.join(body_element.itertext()))
        
        # Nettoyer et filtrer
        if len(full_text) < 100:
            return ""
        
        return full_text

    def fetch_publication_details(self, pmcid: str) -> Optional[Publication]:
        """
        Récupère les détails complets d'une publication via PMC ID
        """
        logger.info(f"Extraction de {pmcid}...")

        try:
            # 1. Récupérer le XML complet depuis PMC
            params = {
                'db': 'pmc',
                'id': pmcid.replace('PMC', ''),
                'retmode': 'xml'
            }

            response = self._make_request('efetch.fcgi', params)
            root = ET.fromstring(response.content)

            # 2. Parser le XML
            article = root.find('.//article')
            if article is None:
                logger.warning(f"Article non trouvé pour {pmcid}")
                return None

            # Extraire métadonnées
            meta = article.find('.//article-meta')
            front = article.find('.//front')

            if not meta or not front:
                logger.warning(f"Métadonnées manquantes pour {pmcid}")
                return None

            # Titre
            title_elem = meta.find('.//article-title')
            title = self._clean_text(''.join(title_elem.itertext()) if title_elem is not None else "No title")
            
            if not title or title == "No title":
                logger.warning(f"Titre manquant pour {pmcid}")
                return None

            # Abstract
            abstract_elem = meta.find('.//abstract')
            abstract = self._clean_text(''.join(abstract_elem.itertext()) if abstract_elem is not None else "")

            # Auteurs
            authors = []
            for contrib in meta.findall('.//contrib[@contrib-type="author"]'):
                name = contrib.find('.//name')
                if name is not None:
                    firstname = self._clean_text(name.findtext('given-names', ''), 255)
                    lastname = self._clean_text(name.findtext('surname', ''), 255)
                    
                    if lastname:  # Au moins le nom de famille est requis
                        aff_elem = contrib.find('.//aff')
                        affiliation = self._clean_text(''.join(aff_elem.itertext()) if aff_elem is not None else '')
                        
                        authors.append({
                            'firstname': firstname if firstname else None,
                            'lastname': lastname,
                            'affiliation': affiliation if affiliation else None
                        })

            # Date de publication
            pub_date = meta.find('.//pub-date[@pub-type="epub"]') or meta.find('.//pub-date')
            year = pub_date.findtext('year', '') if pub_date is not None else ''
            month = pub_date.findtext('month', '01') if pub_date is not None else '01'
            day = pub_date.findtext('day', '01') if pub_date is not None else '01'
            
            # Validation et formatage de la date
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

            # MeSH terms (requiert une requête séparée à PubMed)
            mesh_terms = self._fetch_mesh_terms(pmid) if pmid else []

            # Sections du texte avec nouvelle stratégie incluant DSPy
            body = article.find('.//body')
            sections = self._extract_text_sections(body)
            
            # Extraire le texte complet pour la nouvelle colonne
            full_text = self._extract_full_text_content(body)
            
            # Si pas de texte complet depuis body, essayer depuis l'article entier
            if not full_text or len(full_text) < 200:
                full_text = self._clean_text(''.join(article.itertext()))
                if len(full_text) > 10000:
                    full_text = full_text[:10000]  # Limiter à 10k caractères

            # Validation: s'assurer qu'on a au moins une section
            if not sections:
                logger.warning(f"Aucune section textuelle extraite pour {pmcid}")
                if full_text and len(full_text) > 200:
                    sections["Full Text"] = full_text[:5000]  # Section limitée

            # Références (PMIDs cités)
            references = []
            ref_list = article.find('.//ref-list')
            if ref_list is not None:
                for ref in ref_list.findall('.//ref'):
                    pub_id = ref.find('.//pub-id[@pub-id-type="pmid"]')
                    if pub_id is not None and pub_id.text:
                        references.append(pub_id.text.strip())

            # Validation finale
            if not title or not pmcid:
                logger.warning(f"Données essentielles manquantes pour {pmcid}")
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
                full_text_content=full_text,  # MAINTENANT DÉFINI DANS LA DATACLASS
                mesh_terms=mesh_terms,
                references=references
            )

            # Log des sections et du texte complet
            logger.info(f" {pmcid} extrait avec {len(sections)} section(s) et {len(full_text) if full_text else 0} chars de texte complet")
            return publication

        except Exception as e:
            logger.error(f"Erreur extraction {pmcid}: {e}")
            return None

    def _fetch_mesh_terms(self, pmid: str) -> List[str]:
        """Récupère les MeSH terms depuis PubMed"""
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
            logger.warning(f"Erreur extraction MeSH pour PMID {pmid}: {e}")
            return []

    async def batch_extract_to_db(self, pmcid_list: List[str], skip_existing: bool = True):
        """
        Extrait toutes les publications et les insère directement dans la base de données
        """
        if not self.db_client:
            raise ValueError("DatabaseClient requis pour insertion en base")

        results = []
        failed = []
        skipped = []
        
        total = len(pmcid_list)
        logger.info(f" Début extraction de {total} publications vers PostgreSQL")

        for i, pmcid in enumerate(pmcid_list, 1):
            logger.info(f"Progression: {i}/{total} - {pmcid}")

            try:
                # Vérifier si la publication existe déjà
                if skip_existing and await self.check_publication_exists(pmcid):
                    skipped.append(pmcid)
                    continue

                # Extraire les données
                pub = self.fetch_publication_details(pmcid)

                if pub:
                    # Vérifier qu'on a au moins une section
                    if not pub.full_text_sections:
                        logger.warning(f" {pmcid} sans sections, tentative d'extraction alternative")
                        
                    # Insérer en base de données
                    try:
                        pub_id = await self.db_client.create_publication(pub.to_dict())
                        results.append(pub_id)
                        logger.info(f" {pmcid} inséré en base avec ID {pub_id}")
                    except Exception as db_error:
                        logger.error(f" Erreur insertion {pmcid}: {db_error}")
                        failed.append(pmcid)
                else:
                    failed.append(pmcid)

                # Checkpoint tous les 25 documents
                if i % 25 == 0:
                    logger.info(f" Checkpoint: {len(results)} succès, {len(failed)} échecs, {len(skipped)} ignorés")

            except Exception as e:
                logger.error(f" Erreur générale {pmcid}: {e}")
                failed.append(pmcid)

        logger.info(f"\n Extraction terminée:")
        logger.info(f"    Succès: {len(results)}")
        logger.info(f"    Échecs: {len(failed)}")
        logger.info(f"   ⏭  Ignorés: {len(skipped)}")

        if failed:
            logger.warning(f" Publications échouées: {failed}")

        return results, failed, skipped


async def main():
    """Fonction principale d'extraction"""
    
    # 1. Charger la liste des PMCIDs depuis le CSV
    logger.info(" Chargement de la liste des publications...")
    df = pd.read_csv("https://raw.githubusercontent.com/jgalazka/SB_publications/refs/heads/main/SB_publication_PMC.csv")
    
    pmcids = []
    for i in range(len(df)):
        link = df["Link"][i]
        pmcid = link.split("/")[-2] if link.endswith('/') else link.split("/")[-1]
        pmcids.append(pmcid)
    
    # Test avec un sous-ensemble
    # pmcids = pmcids[:10]  # Décommenter pour tester
    
    logger.info(f" {len(pmcids)} publications à extraire")

    # 2. Initialiser le client de base de données
    db_client = DatabaseClient()
    
    try:
        # Créer les tables si nécessaire
        await db_client.create_tables()
        
        # 3. Initialiser l'extracteur
        extractor = NCBIExtractor(
            email=EMAIL,
            api_key=API_KEY,
            db_client=db_client
        )

        # 4. Lancer l'extraction avec insertion directe en base
        results, failed, skipped = await extractor.batch_extract_to_db(
            pmcids, 
            skip_existing=True
        )

        logger.info(f"\n Processus terminé!")
        logger.info(f"    Total traité: {len(pmcids)}")
        logger.info(f"    Insertions réussies: {len(results)}")
        logger.info(f"    Échecs: {len(failed)}")
        logger.info(f"   ⏭  Déjà existants: {len(skipped)}")

        # Statistiques finales
        total_in_db = len(results) + len(skipped)
        logger.info(f"     Total en base: {total_in_db}")

    except Exception as e:
        logger.error(f" Erreur fatale: {e}")
        raise
    finally:
        await db_client.close()


if __name__ == "__main__":
    asyncio.run(main())