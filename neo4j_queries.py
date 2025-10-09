"""
Analytical queries for NASA Space Biology Knowledge Graph
Discover research patterns, gaps, and collaborations
"""
from neo4j_client import Neo4jClient
from typing import List, Dict, Optional
import logging
import json
from redis_cache import get_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeGraphAnalytics:
    """Pre-built analytical queries for scientific insights"""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
        self.cache = get_cache()
    
    def top_studied_organisms(self, limit: int = 15) -> List[Dict]:
        """Most studied organisms across all publications"""
        # Cache pour 1 heure (3600 secondes)
        cache_key = self.cache._generate_key('neo4j:top_organisms', limit=limit)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(" Using cached top_studied_organisms")
            return cached
        
        query = """
        MATCH (p:Publication)-[:STUDIES]->(o:Organism)
        RETURN o.name AS organism, 
               o.scientific_name AS scientific_name,
               o.category AS category,
               count(DISTINCT p) AS study_count
        ORDER BY study_count DESC
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            data = [dict(record) for record in result]
            
            # Cache pour 1 heure
            self.cache.set(cache_key, data, ttl=3600)
            
            return data
    
    def top_investigated_phenomena(self, limit: int = 15) -> List[Dict]:
        """Most investigated biological phenomena"""
        # Cache pour 1 heure
        cache_key = self.cache._generate_key('neo4j:top_phenomena', limit=limit)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(" Using cached top_investigated_phenomena")
            return cached
        
        query = """
        MATCH (p:Publication)-[:INVESTIGATES]->(ph:Phenomenon)
        RETURN ph.name AS phenomenon,
               ph.system AS biological_system,
               count(DISTINCT p) AS investigation_count
        ORDER BY investigation_count DESC
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            data = [dict(record) for record in result]
            
            self.cache.set(cache_key, data, ttl=3600)
            
            return data
    
    def research_gaps_by_system(self) -> List[Dict]:
        """
        Biological systems with fewest studies (potential research gaps)
        Lower studies_per_phenomenon = potential gap
        """
        # Cache pour 2 heures (7200 secondes)
        cache_key = self.cache._generate_key('neo4j:research_gaps')
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(" Using cached research_gaps_by_system")
            return cached
        
        query = """
        MATCH (ph:Phenomenon)
        WITH ph.system AS system, count(ph) AS phenomenon_count
        MATCH (p:Publication)-[:INVESTIGATES]->(ph2:Phenomenon {system: system})
        RETURN system,
               phenomenon_count AS phenomena_in_system,
               count(DISTINCT p) AS total_studies,
               round(toFloat(count(DISTINCT p)) / phenomenon_count, 2) AS studies_per_phenomenon
        ORDER BY studies_per_phenomenon ASC
        LIMIT 10
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            data = [dict(record) for record in result]
            
            self.cache.set(cache_key, data, ttl=7200)
            
            return data
    
    def spaceflight_vs_simulation(self) -> List[Dict]:
        """Compare spaceflight vs ground simulation studies"""
        query = """
        MATCH (p:Publication)
        WHERE p.experimental_context IS NOT NULL
        WITH p.experimental_context AS context, count(p) AS count
        RETURN context, count
        ORDER BY count DESC
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def organism_phenomenon_network(self, organism_name: str) -> List[Dict]:
        """
        Find all phenomena studied for a specific organism
        Example: organism_name = "mouse" or "Mus musculus"
        """
        # Cache pour 30 minutes (1800 secondes)
        cache_key = self.cache._generate_key('neo4j:organism_network', organism=organism_name)
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f" Using cached organism_phenomenon_network for {organism_name}")
            return cached
        
        query = """
        MATCH (p:Publication)-[:STUDIES]->(o:Organism)
        WHERE toLower(o.name) CONTAINS toLower($organism_name) 
           OR toLower(o.scientific_name) CONTAINS toLower($organism_name)
        MATCH (p)-[:INVESTIGATES]->(ph:Phenomenon)
        RETURN o.scientific_name AS organism,
               collect(DISTINCT ph.name) AS phenomena,
               count(DISTINCT p) AS study_count
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, organism_name=organism_name)
            data = [dict(record) for record in result]
            
            self.cache.set(cache_key, data, ttl=1800)
            
            return data
    
    def mission_platform_distribution(self) -> List[Dict]:
        """Distribution of studies across space missions/platforms"""
        query = """
        MATCH (p:Publication)-[:CONDUCTED_ON]->(pl:Platform)
        RETURN pl.name AS platform,
               count(DISTINCT p) AS study_count
        ORDER BY study_count DESC
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def related_research_clusters(self, min_similarity: float = 0.7) -> List[Dict]:
        """
        Find clusters of highly related research (BUILDS_ON relationships)
        Useful for identifying research themes
        """
        query = """
        MATCH (p1:Publication)-[r:BUILDS_ON]->(p2:Publication)
        WHERE r.similarity >= $min_similarity
        RETURN p1.pmcid AS source_pmcid,
               p2.pmcid AS related_pmcid,
               r.similarity AS similarity
        ORDER BY r.similarity DESC
        LIMIT 50
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, min_similarity=min_similarity)
            return [dict(record) for record in result]
    
    def multi_system_phenomena(self) -> List[Dict]:
        """
        Phenomena investigated across multiple biological systems
        (cross-system effects - important for spaceflight)
        """
        query = """
        MATCH (p:Publication)-[:INVESTIGATES]->(ph:Phenomenon)
        WITH ph.name AS phenomenon, collect(DISTINCT ph.system) AS systems, count(DISTINCT p) AS studies
        WHERE size(systems) > 1
        RETURN phenomenon, systems, studies
        ORDER BY studies DESC
        LIMIT 20
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def stressor_organism_matrix(self) -> List[Dict]:
        """
        Which organisms are exposed to which stressors?
        Creates a matrix view of experimental conditions
        """
        query = """
        MATCH (p:Publication)-[:STUDIES]->(o:Organism)
        MATCH (p)-[:EXPOSES_TO]->(s:Stressor)
        RETURN o.scientific_name AS organism,
               collect(DISTINCT s.name) AS stressors,
               count(DISTINCT p) AS study_count
        ORDER BY study_count DESC
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def understudied_combinations(self) -> List[Dict]:
        """
        Find organism-phenomenon combinations with only 1 study
        (potential research opportunities)
        """
        query = """
        MATCH (p:Publication)-[:STUDIES]->(o:Organism)
        MATCH (p)-[:INVESTIGATES]->(ph:Phenomenon)
        WITH o.scientific_name AS organism, 
             ph.name AS phenomenon, 
             count(DISTINCT p) AS study_count
        WHERE study_count = 1
        RETURN organism, phenomenon, study_count
        ORDER BY organism
        LIMIT 30
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def export_summary_report(self, output_file: str = "knowledge_graph_report.json"):
        """Generate comprehensive summary report"""
        report = {
            "top_organisms": self.top_studied_organisms(limit=10),
            "top_phenomena": self.top_investigated_phenomena(limit=10),
            "research_gaps": self.research_gaps_by_system(),
            "experimental_contexts": self.spaceflight_vs_simulation(),
            "mission_platforms": self.mission_platform_distribution(),
            "research_clusters": self.related_research_clusters(min_similarity=0.7),
            "multi_system_phenomena": self.multi_system_phenomena(),
            "stressor_matrix": self.stressor_organism_matrix()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f" Report exported to {output_file}")
        return report


def print_section(title: str, data: List[Dict], keys: List[str]):
    """Pretty print a section of results"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")
    
    if not data:
        print("  No data available")
        return
    
    for i, item in enumerate(data, 1):
        print(f"{i}. ", end="")
        for key in keys:
            value = item.get(key, 'N/A')
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            print(f"{key}: {value}  ", end="")
        print()


def main():
    """Run all analytical queries"""
    client = Neo4jClient()
    analytics = KnowledgeGraphAnalytics(client)
    
    try:
        # 1. Top Organisms
        organisms = analytics.top_studied_organisms(limit=10)
        print_section(
            "🧬 TOP 10 MOST STUDIED ORGANISMS",
            organisms,
            ['organism', 'scientific_name', 'study_count']
        )
        
        # 2. Top Phenomena
        phenomena = analytics.top_investigated_phenomena(limit=10)
        print_section(
            " TOP 10 INVESTIGATED PHENOMENA",
            phenomena,
            ['phenomenon', 'biological_system', 'investigation_count']
        )
        
        # 3. Research Gaps
        gaps = analytics.research_gaps_by_system()
        print_section(
            " POTENTIAL RESEARCH GAPS (by system)",
            gaps,
            ['system', 'total_studies', 'studies_per_phenomenon']
        )
        
        # 4. Spaceflight vs Simulation
        contexts = analytics.spaceflight_vs_simulation()
        print_section(
            " EXPERIMENTAL CONTEXTS",
            contexts,
            ['context', 'count']
        )
        
        # 5. Mission Platforms
        platforms = analytics.mission_platform_distribution()
        print_section(
            " MISSION PLATFORM DISTRIBUTION",
            platforms,
            ['platform', 'study_count']
        )
        
        # 6. Research Clusters
        clusters = analytics.related_research_clusters(min_similarity=0.7)
        print_section(
            " HIGHLY RELATED RESEARCH (similarity > 0.7)",
            clusters[:10],
            ['source_pmcid', 'related_pmcid', 'similarity']
        )
        
        # 7. Multi-system Phenomena
        multi_system = analytics.multi_system_phenomena()
        print_section(
            " CROSS-SYSTEM PHENOMENA",
            multi_system[:10],
            ['phenomenon', 'systems', 'studies']
        )
        
        # 8. Stressor-Organism Matrix
        stressor_matrix = analytics.stressor_organism_matrix()
        print_section(
            " STRESSOR-ORGANISM COMBINATIONS",
            stressor_matrix[:10],
            ['organism', 'stressors', 'study_count']
        )
        
        # 9. Example: Mouse research
        print(f"\n{'='*60}")
        print("   MOUSE RESEARCH FOCUS")
        print(f"{'='*60}\n")
        mouse_research = analytics.organism_phenomenon_network("mouse")
        if mouse_research:
            for research in mouse_research:
                print(f"Organism: {research['organism']}")
                print(f"Phenomena studied: {', '.join(research['phenomena'][:10])}")
                print(f"Total studies: {research['study_count']}\n")
        
        # 10. Export full report
        print(f"\n{'='*60}")
        print("   EXPORTING COMPREHENSIVE REPORT")
        print(f"{'='*60}\n")
        analytics.export_summary_report()
        
    finally:
        client.close()


if __name__ == "__main__":
    main()