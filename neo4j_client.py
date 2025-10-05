"""
Neo4j Client for NASA Knowledge Graph
"""
import os
from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable
import logging
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from neo4j_schema import (
    get_cypher_create_constraints,
    get_cypher_create_indexes,
    get_cypher_create_fulltext_indexes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client for knowledge graph operations"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        logger.info(f" Connected to Neo4j at {NEO4J_URI}")
    
    def close(self):
        """Close driver connection"""
        self.driver.close()
        logger.info(" Neo4j connection closed")
    
    def verify_connectivity(self):
        """Test connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                assert result.single()["test"] == 1
                logger.info(" Neo4j connectivity verified")
                return True
        except ServiceUnavailable as e:
            logger.error(f" Cannot connect to Neo4j: {e}")
            return False
    
    def initialize_schema(self):
        """Create constraints and indexes"""
        with self.driver.session() as session:
            # Constraints
            logger.info(" Creating constraints...")
            for query in get_cypher_create_constraints():
                try:
                    session.run(query)
                    logger.info(f"   {query[:50]}...")
                except Exception as e:
                    logger.warning(f"   Constraint already exists or error: {e}")
            
            # Indexes
            logger.info(" Creating indexes...")
            for query in get_cypher_create_indexes():
                try:
                    session.run(query)
                    logger.info(f"   {query[:50]}...")
                except Exception as e:
                    logger.warning(f"   Index already exists or error: {e}")
            
            # Fulltext indexes
            logger.info(" Creating fulltext indexes...")
            for query in get_cypher_create_fulltext_indexes():
                try:
                    session.run(query)
                    logger.info(f"   {query[:50]}...")
                except Exception as e:
                    logger.warning(f"   Fulltext index already exists or error: {e}")
        
        logger.info(" Schema initialization complete!")
    
    def clear_database(self):
        """ DANGER: Delete all nodes and relationships"""
        with self.driver.session() as session:
            logger.warning(" Clearing entire database...")
            session.run("MATCH (n) DETACH DELETE n")
            logger.info(" Database cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                ORDER BY count DESC
            """)
            
            stats = {record["label"]: record["count"] for record in result}
            
            # Relationship stats
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS rel_type, count(*) AS count
                ORDER BY count DESC
            """)
            
            rel_stats = {record["rel_type"]: record["count"] for record in result}
            
            return {
                "nodes": stats,
                "relationships": rel_stats,
                "total_nodes": sum(stats.values()),
                "total_relationships": sum(rel_stats.values())
            }
    
    def print_stats(self):
        """Pretty print database stats"""
        stats = self.get_stats()
        
        print("\n=== Neo4j Database Statistics ===")
        print(f"\n Total Nodes: {stats['total_nodes']}")
        for label, count in stats['nodes'].items():
            print(f"  - {label}: {count}")
        
        print(f"\n Total Relationships: {stats['total_relationships']}")
        for rel_type, count in stats['relationships'].items():
            print(f"  - {rel_type}: {count}")


def main():
    """Initialize Neo4j schema"""
    client = Neo4jClient()
    
    # Verify connection
    if not client.verify_connectivity():
        logger.error(" Cannot proceed without Neo4j connection")
        return
    
    # Initialize schema
    client.initialize_schema()
    
    # Print stats
    client.print_stats()
    
    client.close()


if __name__ == "__main__":
    main()