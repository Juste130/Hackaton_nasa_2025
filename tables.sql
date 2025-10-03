-- NASA Bioscience Publications Database Schema
-- PostgreSQL 15+ avec extension pgvector pour recherche sémantique

-- Activer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Pour recherche full-text fuzzy

-- Table principale des publications
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pmcid VARCHAR(20) UNIQUE NOT NULL,
    pmid VARCHAR(20),
    doi VARCHAR(255),
    title TEXT NOT NULL,
    abstract TEXT,
    publication_date DATE,
    journal VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Recherche full-text
    title_search TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', title)) STORED,
    abstract_search TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', COALESCE(abstract, ''))) STORED,
    
    -- Embedding vectoriel pour recherche sémantique (768 dimensions pour SPECTER)
    embedding vector(768)
);

-- Index pour performance
CREATE INDEX idx_publications_pmcid ON publications(pmcid);
CREATE INDEX idx_publications_date ON publications(publication_date);
CREATE INDEX idx_publications_title_search ON publications USING GIN(title_search);
CREATE INDEX idx_publications_abstract_search ON publications USING GIN(abstract_search);
CREATE INDEX idx_publications_embedding ON publications USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- Table des auteurs
CREATE TABLE authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firstname VARCHAR(255),
    lastname VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    orcid VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(firstname, lastname)
);

CREATE INDEX idx_authors_lastname ON authors(lastname);

-- Table de liaison publication-auteur
CREATE TABLE publication_authors (
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    author_id UUID REFERENCES authors(id) ON DELETE CASCADE,
    author_order INTEGER NOT NULL, -- Ordre dans la liste d'auteurs
    affiliation TEXT,
    PRIMARY KEY (publication_id, author_id)
);

-- Table des mots-clés
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) -- ex: organism, experiment_type, phenomenon
);

CREATE INDEX idx_keywords_keyword ON keywords USING gin(keyword gin_trgm_ops);

-- Liaison publication-keywords
CREATE TABLE publication_keywords (
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (publication_id, keyword_id)
);

-- Table des MeSH terms (vocabulaire médical contrôlé)
CREATE TABLE mesh_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term VARCHAR(255) UNIQUE NOT NULL,
    tree_number VARCHAR(50) -- Position hiérarchique dans MeSH
);

CREATE TABLE publication_mesh_terms (
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    mesh_term_id UUID REFERENCES mesh_terms(id) ON DELETE CASCADE,
    is_major_topic BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (publication_id, mesh_term_id)
);

-- Table des sections de texte intégral
CREATE TABLE text_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    section_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    section_order INTEGER,
    embedding vector(768),
    
    UNIQUE(publication_id, section_name)
);

CREATE INDEX idx_text_sections_pub ON text_sections(publication_id);

-- Table des citations (relations entre publications)
CREATE TABLE citations (
    citing_publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    cited_publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    context TEXT, -- Contexte de la citation dans le texte
    PRIMARY KEY (citing_publication_id, cited_publication_id)
);

CREATE INDEX idx_citations_citing ON citations(citing_publication_id);
CREATE INDEX idx_citations_cited ON citations(cited_publication_id);

-- Table des entités extraites par IA (organismes, phénomènes, missions)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- organism, phenomenon, mission, method
    entity_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255), -- Forme normalisée
    description TEXT,
    
    UNIQUE(entity_type, entity_name)
);

CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities USING gin(entity_name gin_trgm_ops);

-- Liaison publication-entités
CREATE TABLE publication_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    context TEXT, -- Phrase où l'entité apparaît
    
    UNIQUE(publication_id, entity_id)
);

-- Table des insights générés par IA
CREATE TABLE ai_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL, -- key_finding, methodology, gap, recommendation
    content TEXT NOT NULL,
    confidence FLOAT,
    generated_at TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(50) -- GPT-4, Claude-3.5, etc.
);

CREATE INDEX idx_insights_pub ON ai_insights(publication_id);
CREATE INDEX idx_insights_type ON ai_insights(insight_type);

-- Table des relations sémantiques entre publications
CREATE TABLE publication_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_1_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    publication_2_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- similar, contradicts, extends, supports
    similarity_score FLOAT,
    description TEXT,
    
    CHECK (publication_1_id < publication_2_id), -- Éviter doublons
    UNIQUE(publication_1_id, publication_2_id, relationship_type)
);

-- Table des clusters thématiques
CREATE TABLE research_clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cluster_name VARCHAR(255) NOT NULL,
    description TEXT,
    centroid_embedding vector(768),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cluster_publications (
    cluster_id UUID REFERENCES research_clusters(id) ON DELETE CASCADE,
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    distance_to_centroid FLOAT,
    PRIMARY KEY (cluster_id, publication_id)
);

-- Table des gaps de recherche identifiés
CREATE TABLE research_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gap_description TEXT NOT NULL,
    gap_category VARCHAR(100), -- methodology, organism, phenomenon, etc.
    priority VARCHAR(20), -- high, medium, low
    supporting_publication_ids UUID[], -- Array de publication IDs
    identified_at TIMESTAMP DEFAULT NOW()
);

-- Table des consensus scientifiques
CREATE TABLE scientific_consensus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255) NOT NULL,
    consensus_statement TEXT,
    consensus_level VARCHAR(20), -- strong, moderate, weak, none
    supporting_count INTEGER,
    contradicting_count INTEGER,
    publication_ids UUID[], -- Publications liées
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Vue pour recherche combinée
CREATE VIEW search_view AS
SELECT 
    p.id,
    p.pmcid,
    p.pmid,
    p.title,
    p.abstract,
    p.publication_date,
    p.journal,
    ARRAY_AGG(DISTINCT a.lastname || ', ' || a.firstname) AS authors,
    ARRAY_AGG(DISTINCT k.keyword) AS keywords,
    ARRAY_AGG(DISTINCT e.entity_name) AS entities,
    p.embedding
FROM publications p
LEFT JOIN publication_authors pa ON p.id = pa.publication_id
LEFT JOIN authors a ON pa.author_id = a.id
LEFT JOIN publication_keywords pk ON p.id = pk.publication_id
LEFT JOIN keywords k ON pk.keyword_id = k.id
LEFT JOIN publication_entities pe ON p.id = pe.publication_id
LEFT JOIN entities e ON pe.entity_id = e.id
GROUP BY p.id;

-- Fonction de recherche sémantique
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding vector(768),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    publication_id UUID,
    pmcid VARCHAR,
    title TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.pmcid,
        p.title,
        1 - (p.embedding <=> query_embedding) AS similarity
    FROM publications p
    WHERE p.embedding IS NOT NULL
        AND (1 - (p.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour trouver publications similaires
CREATE OR REPLACE FUNCTION find_similar_publications(
    source_pmcid VARCHAR,
    limit_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    pmcid VARCHAR,
    title TEXT,
    similarity FLOAT
) AS $$
DECLARE
    source_embedding vector(768);
BEGIN
    SELECT embedding INTO source_embedding
    FROM publications
    WHERE publications.pmcid = source_pmcid;
    
    IF source_embedding IS NULL THEN
        RAISE EXCEPTION 'Publication not found or no embedding available';
    END IF;
    
    RETURN QUERY
    SELECT 
        p.pmcid,
        p.title,
        1 - (p.embedding <=> source_embedding) AS similarity
    FROM publications p
    WHERE p.pmcid != source_pmcid
        AND p.embedding IS NOT NULL
    ORDER BY p.embedding <=> source_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour mise à jour automatique
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER publications_updated_at
    BEFORE UPDATE ON publications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();