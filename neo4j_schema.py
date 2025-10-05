"""
Neo4j Knowledge Graph Schema for NASA Bioscience Publications
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    """Types de nœuds dans le graphe"""
    PUBLICATION = "Publication"
    ORGANISM = "Organism"
    PHENOMENON = "Phenomenon"
    FINDING = "Finding"
    PLATFORM = "Platform"
    STRESSOR = "Stressor"
    AUTHOR = "Author"


class RelationType(Enum):
    """Types de relations dans le graphe"""
    # Publication → Entities
    STUDIES = "STUDIES"  # Publication → Organism
    INVESTIGATES = "INVESTIGATES"  # Publication → Phenomenon
    REPORTS = "REPORTS"  # Publication → Finding
    CONDUCTED_ON = "CONDUCTED_ON"  # Publication → Platform
    EXPOSES_TO = "EXPOSES_TO"  # Publication → Stressor
    AUTHORED_BY = "AUTHORED_BY"  # Publication → Author
    
    # Inter-entity relations
    AFFECTS = "AFFECTS"  # Organism → Phenomenon
    CAUSES = "CAUSES"  # Stressor → Phenomenon
    SUPPORTS = "SUPPORTS"  # Finding → Finding (consensus)
    CONTRADICTS = "CONTRADICTS"  # Finding → Finding (conflict)
    BUILDS_ON = "BUILDS_ON"  # Publication → Publication (citation/extension)
    
    # Taxonomic/hierarchical
    IS_A = "IS_A"  # Organism → Organism (taxonomie)
    PART_OF = "PART_OF"  # Phenomenon → BiologicalSystem


@dataclass
class Neo4jConstraints:
    """Contraintes d'unicité et index"""
    
    UNIQUE_CONSTRAINTS = [
        ("Publication", "pmcid"),
        ("Organism", "scientific_name"),
        ("Phenomenon", "name"),
        ("Platform", "name"),
        ("Stressor", "name"),
        ("Author", "name")
    ]
    
    INDEXES = [
        ("Publication", "publication_date"),
        ("Publication", "journal"),
        ("Phenomenon", "system"),
        ("Organism", "category")
    ]
    
    FULLTEXT_INDEXES = [
        ("Publication", ["title", "abstract"]),
        ("Phenomenon", ["name", "description"])
    ]


# Schéma de nœuds avec propriétés
NODE_SCHEMAS = {
    "Publication": {
        "properties": [
            "pmcid:string:unique",
            "title:string",
            "abstract:string",
            "publication_date:date",
            "journal:string",
            "doi:string",
            "experimental_context:string",  # spaceflight, ground_simulation, etc.
            "extraction_confidence:float",
            "embedding:float[]"  # Vector embedding pour recherche sémantique
        ],
        "indexes": ["pmcid", "publication_date", "experimental_context"]
    },
    
    "Organism": {
        "properties": [
            "name:string",
            "scientific_name:string:unique",
            "category:string",  # mammal, plant, cell_line, microorganism
            "common_names:string[]",
            "taxonomy_id:string"
        ],
        "indexes": ["scientific_name", "category"]
    },
    
    "Phenomenon": {
        "properties": [
            "name:string:unique",
            "description:string",
            "system:string",  # musculoskeletal, immune, cardiovascular, etc.
            "synonyms:string[]",
            "ontology_id:string"  # Link to bio-ontology if available
        ],
        "indexes": ["name", "system"]
    },
    
    "Finding": {
        "properties": [
            "statement:string",
            "evidence_level:string",  # strong, moderate, weak
            "effect_size:float",
            "p_value:float",
            "publication_pmcid:string"
        ],
        "indexes": ["publication_pmcid"]
    },
    
    "Platform": {
        "properties": [
            "name:string:unique",  # ISS, Space Shuttle, BION-M1, etc.
            "type:string",  # spacecraft, ground_facility, simulation
            "description:string"
        ],
        "indexes": ["name"]
    },
    
    "Stressor": {
        "properties": [
            "name:string:unique",  # microgravity, radiation, isolation
            "category:string",  # physical, psychological, environmental
            "description:string"
        ],
        "indexes": ["name", "category"]
    },
    
    "Author": {
        "properties": [
            "name:string:unique",
            "affiliation:string",
            "orcid:string"
        ],
        "indexes": ["name"]
    }
}


# Schéma de relations avec propriétés
RELATION_SCHEMAS = {
    "STUDIES": {
        "from": "Publication",
        "to": "Organism",
        "properties": [
            "sample_size:integer",
            "exposure_duration:string"
        ]
    },
    
    "INVESTIGATES": {
        "from": "Publication",
        "to": "Phenomenon",
        "properties": [
            "is_primary_focus:boolean",
            "confidence:float"
        ]
    },
    
    "REPORTS": {
        "from": "Publication",
        "to": "Finding",
        "properties": [
            "page_reference:string"
        ]
    },
    
    "AFFECTS": {
        "from": "Stressor",
        "to": "Phenomenon",
        "properties": [
            "effect_direction:string",  # increases, decreases, modulates
            "effect_size:float",
            "evidence_count:integer"  # Number of publications supporting this
        ]
    },
    
    "CONTRADICTS": {
        "from": "Finding",
        "to": "Finding",
        "properties": [
            "conflict_severity:string",  # major, minor
            "reconciliation_hypothesis:string"
        ]
    },
    
    "BUILDS_ON": {
        "from": "Publication",
        "to": "Publication",
        "properties": [
            "relationship_type:string",  # extends, validates, contradicts, replicates
            "confidence:float"
        ]
    }
}


def get_cypher_create_constraints() -> List[str]:
    """Génère les requêtes Cypher pour créer les contraintes"""
    queries = []
    
    for node_label, property_name in Neo4jConstraints.UNIQUE_CONSTRAINTS:
        queries.append(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_label}) "
            f"REQUIRE n.{property_name} IS UNIQUE"
        )
    
    return queries


def get_cypher_create_indexes() -> List[str]:
    """Génère les requêtes Cypher pour créer les index"""
    queries = []
    
    for node_label, property_name in Neo4jConstraints.INDEXES:
        queries.append(
            f"CREATE INDEX IF NOT EXISTS FOR (n:{node_label}) ON (n.{property_name})"
        )
    
    return queries


def get_cypher_create_fulltext_indexes() -> List[str]:
    """Génère les requêtes Cypher pour les index fulltext"""
    queries = []
    
    for node_label, properties in Neo4jConstraints.FULLTEXT_INDEXES:
        index_name = f"{node_label.lower()}_fulltext"
        props_str = ", ".join([f"n.{prop}" for prop in properties])
        
        queries.append(
            f"CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS "
            f"FOR (n:{node_label}) ON EACH [{props_str}]"
        )
    
    return queries


if __name__ == "__main__":
    """Print schema summary"""
    print("=== Neo4j Schema Summary ===\n")
    
    print(" Node Types:")
    for node_type in NodeType:
        print(f"  - {node_type.value}")
    
    print(f"\n Relation Types:")
    for rel_type in RelationType:
        print(f"  - {rel_type.value}")
    
    print(f"\n Constraints:")
    for query in get_cypher_create_constraints():
        print(f"  {query}")
    
    print(f"\n Indexes:")
    for query in get_cypher_create_indexes():
        print(f"  {query}")