"""
Analytical queries for NASA Space Biology Knowledge Graph - OPTIMIZED
Discover research patterns, gaps, and collaborations with memory-efficient queries
"""
from neo4j_client import Neo4jClient
from typing import List, Dict, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GapAnalyzer:
    """Advanced gap analysis for identifying research opportunities"""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    def find_missing_combinations(self, limit: int = 100) -> List[Dict]:
        """
        Find organism-phenomenon-platform combinations that have never been studied
        Returns potential research gaps
        OPTIMIZED: Applies LIMIT before checking existence
        """
        query = """
        MATCH (o:Organism), (ph:Phenomenon), (pl:Platform)
        WITH o, ph, pl LIMIT $limit
        WHERE NOT EXISTS {
            MATCH (p:Publication)-[:STUDIES]->(o)
            WHERE (p)-[:INVESTIGATES]->(ph)
              AND (p)-[:CONDUCTED_ON]->(pl)
        }
        RETURN o.name AS organism,
               o.scientific_name AS scientific_name,
               o.category AS organism_category,
               ph.name AS phenomenon,
               ph.system AS biological_system,
               pl.name AS platform,
               pl.type AS platform_type
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def find_understudied_combinations(self, max_studies: int = 3, limit: int = 200) -> List[Dict]:
        """
        Find organism-phenomenon combinations with very few studies (potential gaps)
        OPTIMIZED: Added explicit LIMIT
        """
        query = """
        MATCH (p:Publication)-[:STUDIES]->(o:Organism)
        MATCH (p)-[:INVESTIGATES]->(ph:Phenomenon)
        WITH o, ph, count(DISTINCT p) AS study_count
        WHERE study_count <= $max_studies
        RETURN o.name AS organism,
               o.scientific_name AS scientific_name,
               ph.name AS phenomenon,
               ph.system AS biological_system,
               study_count
        ORDER BY study_count ASC, o.name
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, max_studies=max_studies, limit=limit)
            return [dict(record) for record in result]
    
    def calculate_completeness_matrix(self) -> List[Dict]:
        """
        Calculate completeness score for each biological system
        OPTIMIZED: Uses aggregation without creating large intermediate collections
        Recommended for general use with Neo4j Aura
        """
        query = """
        MATCH (ph:Phenomenon)
        WHERE ph.system IS NOT NULL
        WITH ph.system AS system, count(DISTINCT ph) AS total_phenomena
        
        MATCH (o:Organism)
        WITH system, total_phenomena, count(DISTINCT o) AS total_organisms
        
        OPTIONAL MATCH (p:Publication)-[:INVESTIGATES]->(ph:Phenomenon)
        WHERE ph.system = system
        WITH system, total_phenomena, total_organisms, p, ph
        OPTIONAL MATCH (p)-[:STUDIES]->(o:Organism)
        WHERE o IS NOT NULL
        
        WITH system, 
             total_phenomena, 
             total_organisms,
             count(DISTINCT o.name + '_' + ph.name) AS studied_combinations
        
        WITH system,
             total_organisms,
             total_phenomena,
             studied_combinations,
             (total_organisms * total_phenomena) AS possible_combinations
        WHERE possible_combinations > 0
        
        RETURN system,
               total_organisms,
               total_phenomena,
               studied_combinations,
               possible_combinations,
               round(100.0 * studied_combinations / possible_combinations, 2) AS completeness_percentage
        ORDER BY completeness_percentage ASC
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def calculate_completeness_matrix_paginated(self, 
                                                skip: int = 0, 
                                                limit: int = 5) -> Dict:
        """
        Version paginée pour traiter les systèmes biologiques par lots
        Idéal pour les API REST avec Neo4j Aura (mémoire limitée)
        
        Args:
            skip: Nombre de systèmes à sauter
            limit: Nombre de systèmes à retourner (recommandé: 5-10)
        
        Returns:
            Dict with 'data' and 'pagination' keys
        """
        query = """
        MATCH (ph:Phenomenon)
        WHERE ph.system IS NOT NULL
        WITH DISTINCT ph.system AS system
        ORDER BY system
        SKIP $skip
        LIMIT $limit
        
        WITH collect(system) AS systems
        UNWIND systems AS system
        
        MATCH (ph:Phenomenon {system: system})
        WITH system, count(DISTINCT ph) AS total_phenomena
        
        MATCH (o:Organism)
        WITH system, total_phenomena, count(DISTINCT o) AS total_organisms
        
        OPTIONAL MATCH (p:Publication)-[:INVESTIGATES]->(ph:Phenomenon {system: system})
        OPTIONAL MATCH (p)-[:STUDIES]->(o:Organism)
        WITH system,
             total_organisms,
             total_phenomena,
             count(DISTINCT CASE WHEN p IS NOT NULL AND o IS NOT NULL 
                                 THEN o.name + '_' + ph.name 
                                 ELSE NULL END) AS studied_combinations
        
        WITH system,
             total_organisms,
             total_phenomena,
             studied_combinations,
             (total_organisms * total_phenomena) AS possible_combinations
        
        RETURN system,
               total_organisms,
               total_phenomena,
               studied_combinations,
               possible_combinations,
               round(100.0 * studied_combinations / possible_combinations, 2) AS completeness_percentage
        ORDER BY completeness_percentage ASC
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, skip=skip, limit=limit)
            data = [dict(record) for record in result]
            
            count_query = """
            MATCH (ph:Phenomenon)
            WHERE ph.system IS NOT NULL
            RETURN count(DISTINCT ph.system) AS total
            """
            count_result = session.run(count_query)
            total = count_result.single()['total']
            
            return {
                'data': data,
                'pagination': {
                    'skip': skip,
                    'limit': limit,
                    'total': total,
                    'has_more': skip + limit < total
                }
            }
    
    def calculate_completeness_summary(self) -> Dict:
        """
        Version ultra-légère qui retourne juste un résumé global
        Sans détails par système (minimal memory usage)
        Idéal pour un dashboard ou une vue d'ensemble rapide
        """
        query = """
        MATCH (ph:Phenomenon)
        WHERE ph.system IS NOT NULL
        WITH count(DISTINCT ph.system) AS total_systems,
             count(DISTINCT ph) AS total_phenomena
        
        MATCH (o:Organism)
        WITH total_systems, total_phenomena, count(DISTINCT o) AS total_organisms
        
        MATCH (p:Publication)-[:INVESTIGATES]->(:Phenomenon)
        MATCH (p)-[:STUDIES]->(:Organism)
        WITH total_systems, 
             total_phenomena, 
             total_organisms,
             count(DISTINCT p) AS total_studies
        
        WITH total_systems,
             total_phenomena,
             total_organisms,
             total_studies,
             (total_organisms * total_phenomena) AS total_possible_combinations
        
        RETURN total_systems,
               total_phenomena,
               total_organisms,
               total_studies,
               total_possible_combinations,
               round(100.0 * total_studies / total_possible_combinations, 2) AS overall_completeness
        """
        
        with self.client.driver.session() as session:
            result = session.run(query)
            return dict(result.single())
    
    def find_critical_gaps_for_mars(self, limit: int = 50) -> List[Dict]:
        """
        Find gaps that are critical for Mars missions
        Focus on long-duration, isolation, and life-support systems
        OPTIMIZED: Added explicit LIMIT
        """
        query = """
        MATCH (o:Organism), (ph:Phenomenon)
        WHERE (
            toLower(o.name) CONTAINS 'human' OR 
            toLower(o.name) CONTAINS 'mouse' OR
            toLower(o.category) = 'plant' OR
            toLower(o.category) = 'microorganism'
        ) AND (
            toLower(ph.name) CONTAINS 'bone' OR
            toLower(ph.name) CONTAINS 'muscle' OR
            toLower(ph.name) CONTAINS 'cardiovascular' OR
            toLower(ph.name) CONTAINS 'immune' OR
            toLower(ph.name) CONTAINS 'radiation' OR
            toLower(ph.name) CONTAINS 'isolation' OR
            toLower(ph.name) CONTAINS 'reproduction' OR
            toLower(ph.system) IN ['musculoskeletal', 'immune', 'cardiovascular', 'reproductive']
        )
        AND NOT EXISTS {
            MATCH (p:Publication)-[:STUDIES]->(o)
            MATCH (p)-[:INVESTIGATES]->(ph)
        }
        RETURN o.name AS organism,
               o.category AS organism_category,
               ph.name AS phenomenon,
               ph.system AS biological_system,
               'CRITICAL_MARS' AS priority_level,
               'Long-duration space missions require this combination' AS rationale
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def analyze_platform_gaps(self, limit: int = 200) -> List[Dict]:
        """
        Analyze which platforms are underutilized for specific organism-phenomenon studies
        OPTIMIZED: Added explicit LIMIT
        """
        query = """
        MATCH (o:Organism), (ph:Phenomenon), (pl:Platform)
        WITH o, ph, pl
        OPTIONAL MATCH (p:Publication)-[:STUDIES]->(o)
        OPTIONAL MATCH (p)-[:INVESTIGATES]->(ph)
        OPTIONAL MATCH (p)-[:CONDUCTED_ON]->(pl)
        WITH o.name AS organism,
             ph.name AS phenomenon,
             pl.name AS platform,
             pl.type AS platform_type,
             count(DISTINCT p) AS study_count
        WHERE study_count = 0
        RETURN organism, phenomenon, platform, platform_type, study_count
        ORDER BY organism, phenomenon, platform
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def get_research_priority_matrix(self, limit: int = 100) -> List[Dict]:
        """
        Create a priority matrix based on mission importance vs current knowledge
        OPTIMIZED: Kept existing LIMIT
        """
        query = """
        MATCH (o:Organism), (ph:Phenomenon)
        WITH o, ph
        OPTIONAL MATCH (p:Publication)-[:STUDIES]->(o)
        OPTIONAL MATCH (p)-[:INVESTIGATES]->(ph)
        WITH o, ph, count(DISTINCT p) AS study_count
        
        WITH o, ph, study_count,
             CASE 
                WHEN toLower(o.name) CONTAINS 'human' THEN 10
                WHEN toLower(o.category) = 'plant' THEN 8
                WHEN toLower(o.category) = 'microorganism' THEN 7
                WHEN toLower(o.name) CONTAINS 'mouse' THEN 6
                ELSE 3
             END +
             CASE
                WHEN toLower(ph.system) IN ['musculoskeletal', 'cardiovascular'] THEN 10
                WHEN toLower(ph.system) IN ['immune', 'nervous'] THEN 8
                WHEN toLower(ph.system) IN ['reproductive', 'respiratory'] THEN 6
                ELSE 3
             END AS mission_importance
        
        WITH o, ph, study_count, mission_importance,
             CASE 
                WHEN study_count = 0 THEN 'UNKNOWN'
                WHEN study_count <= 2 THEN 'LOW'
                WHEN study_count <= 10 THEN 'MEDIUM'
                ELSE 'HIGH'
             END AS knowledge_level
        
        RETURN o.name AS organism,
               ph.name AS phenomenon,
               ph.system AS biological_system,
               study_count,
               mission_importance,
               knowledge_level,
               CASE 
                   WHEN mission_importance >= 15 AND study_count <= 2 THEN 'CRITICAL'
                   WHEN mission_importance >= 12 AND study_count <= 5 THEN 'HIGH'
                   WHEN mission_importance >= 8 AND study_count <= 10 THEN 'MEDIUM'
                   ELSE 'LOW'
               END AS priority_level
        ORDER BY mission_importance DESC, study_count ASC
        LIMIT $limit
        """
        
        with self.client.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]


class KnowledgeGraphAnalytics:
    """Pre-built analytical queries for scientific insights"""
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    def top_studied_organisms(self, limit: int = 15) -> List[Dict]:
        """Most studied organisms across all publications"""
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
            return [dict(record) for record in result]
    
    def top_investigated_phenomena(self, limit: int = 15) -> List[Dict]:
        """Most investigated biological phenomena"""
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
            return [dict(record) for record in result]
    
    def research_gaps_by_system(self) -> List[Dict]:
        """
        Biological systems with fewest studies (potential research gaps)
        Lower studies_per_phenomenon = potential gap
        """
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
            return [dict(record) for record in result]
    
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
            return [dict(record) for record in result]
    
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
        
        logger.info(f"Report exported to {output_file}")
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
    gap_analyzer = GapAnalyzer(client)
    
    try:
        organisms = analytics.top_studied_organisms(limit=10)
        print_section(
            "TOP 10 MOST STUDIED ORGANISMS",
            organisms,
            ['organism', 'scientific_name', 'study_count']
        )
        
        phenomena = analytics.top_investigated_phenomena(limit=10)
        print_section(
            "TOP 10 INVESTIGATED PHENOMENA",
            phenomena,
            ['phenomenon', 'biological_system', 'investigation_count']
        )
        
        gaps = analytics.research_gaps_by_system()
        print_section(
            "POTENTIAL RESEARCH GAPS (by system)",
            gaps,
            ['system', 'total_studies', 'studies_per_phenomenon']
        )
        
        contexts = analytics.spaceflight_vs_simulation()
        print_section(
            "EXPERIMENTAL CONTEXTS",
            contexts,
            ['context', 'count']
        )
        
        platforms = analytics.mission_platform_distribution()
        print_section(
            "MISSION PLATFORM DISTRIBUTION",
            platforms,
            ['platform', 'study_count']
        )
        
        clusters = analytics.related_research_clusters(min_similarity=0.7)
        print_section(
            "HIGHLY RELATED RESEARCH (similarity > 0.7)",
            clusters[:10],
            ['source_pmcid', 'related_pmcid', 'similarity']
        )
        
        multi_system = analytics.multi_system_phenomena()
        print_section(
            "CROSS-SYSTEM PHENOMENA",
            multi_system[:10],
            ['phenomenon', 'systems', 'studies']
        )
        
        stressor_matrix = analytics.stressor_organism_matrix()
        print_section(
            "STRESSOR-ORGANISM COMBINATIONS",
            stressor_matrix[:10],
            ['organism', 'stressors', 'study_count']
        )
        
        print(f"\n{'='*60}")
        print("   MOUSE RESEARCH FOCUS")
        print(f"{'='*60}\n")
        mouse_research = analytics.organism_phenomenon_network("mouse")
        if mouse_research:
            for research in mouse_research:
                print(f"Organism: {research['organism']}")
                print(f"Phenomena studied: {', '.join(research['phenomena'][:10])}")
                print(f"Total studies: {research['study_count']}\n")
        
        print(f"\n{'='*60}")
        print("   COMPLETENESS MATRIX (Paginated)")
        print(f"{'='*60}\n")
        completeness = gap_analyzer.calculate_completeness_matrix_paginated(skip=0, limit=5)
        for item in completeness['data']:
            print(f"{item['system']}: {item['completeness_percentage']}%")
        print(f"\nShowing {len(completeness['data'])} of {completeness['pagination']['total']} systems")
        
        print(f"\n{'='*60}")
        print("   EXPORTING COMPREHENSIVE REPORT")
        print(f"{'='*60}\n")
        analytics.export_summary_report()
        
    finally:
        client.close()


if __name__ == "__main__":
    main()