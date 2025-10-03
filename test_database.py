"""
Script de test et statistiques pour la base de données NASA
"""

import asyncio
from client import DatabaseClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Tester les fonctionnalités de base de données"""
    
    client = DatabaseClient()
    
    try:
        # Test de connexion
        logger.info("🔗 Test de connexion...")
        
        # Recherche de publications
        results = await client.search_publications(limit=5)
        logger.info(f"📊 {len(results)} publications trouvées")
        
        for pub in results:
            logger.info(f"   📄 {pub['pmcid']}: {pub['title'][:60]}...")
        
        # Recherche par mot-clé
        keyword_results = await client.search_publications(query="space", limit=3)
        logger.info(f"🔍 {len(keyword_results)} publications avec 'space'")
        
        # Recherche par auteur
        author_results = await client.search_publications(author="smith", limit=3)
        logger.info(f"👤 {len(author_results)} publications avec auteur 'Smith'")
        
        logger.info("✅ Tests réussis!")
        
    except Exception as e:
        logger.error(f"❌ Erreur test: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_database())