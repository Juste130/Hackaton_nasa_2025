"""
Streamlit Dashboard for NASA Space Biology Search
Interactive search with graph visualization
"""
import streamlit as st
import streamlit.components.v1 as components
import asyncio
from search_engine import HybridSearchEngine, SearchMode
import plotly.graph_objects as go
import pandas as pd
import nest_asyncio
from pyvis.network import Network
import tempfile
import os

# Fix asyncio event loop conflicts with Streamlit
nest_asyncio.apply()

# Page config
st.set_page_config(
    page_title="NASA Space Biology Search",
    page_icon="",
    layout="wide"
)

# Cache the search engine but don't close connections aggressively
@st.cache_resource
def get_search_engine():
    """Create and cache search engine instance"""
    engine = HybridSearchEngine()
    engine._should_close = False  # ← Don't close in Streamlit context
    return engine

engine = get_search_engine()

# Wrapper function to run async code in Streamlit
def run_search(query, mode, limit, min_similarity, year_from, year_to, journal=None):
    """Synchronous wrapper for async search"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            engine.search(
                query=query,
                mode=mode,
                limit=limit,
                min_similarity=min_similarity,
                year_from=year_from,
                year_to=year_to,
                journal=journal
            )
        )
        return result
    finally:
        pass

def fetch_graph_data(pmcids):
    """Fetch Neo4j subgraph for given publications"""
    from neo4j_client import Neo4jClient
    
    neo4j_client = Neo4jClient()
    
    try:
        with neo4j_client.driver.session() as session:
            # Cypher query to get subgraph
            query = """
            MATCH (p:Publication)
            WHERE p.pmcid IN $pmcids
            OPTIONAL MATCH (p)-[r1:STUDIES]->(o:Organism)
            OPTIONAL MATCH (p)-[r2:INVESTIGATES]->(ph:Phenomenon)
            OPTIONAL MATCH (p)-[r3:CONDUCTED_ON]->(pl:Platform)
            OPTIONAL MATCH (p)-[r4:BUILDS_ON]->(p2:Publication)
            WHERE p2.pmcid IN $pmcids
            RETURN p, o, ph, pl, p2, r1, r2, r3, r4
            """
            
            result = session.run(query, pmcids=pmcids)
            
            nodes = {}
            edges = []
            
            for record in result:
                # Publication node
                if record["p"]:
                    pub = record["p"]
                    pmcid = pub["pmcid"]
                    if pmcid not in nodes:
                        nodes[pmcid] = {
                            "id": pmcid,
                            "label": pub.get("title", pmcid)[:50] + "...",
                            "type": "Publication",
                            "full_title": pub.get("title", ""),
                            "color": "#4A90E2"
                        }
                
                # Organism node
                if record["o"]:
                    org = record["o"]
                    org_id = f"org_{org['scientific_name']}"
                    if org_id not in nodes:
                        nodes[org_id] = {
                            "id": org_id,
                            "label": org.get("name", org["scientific_name"]),
                            "type": "Organism",
                            "color": "#50C878"
                        }
                    
                    if record["r1"]:
                        edges.append({
                            "from": record["p"]["pmcid"],
                            "to": org_id,
                            "label": "STUDIES",
                            "color": "#50C878"
                        })
                
                # Phenomenon node
                if record["ph"]:
                    phen = record["ph"]
                    phen_id = f"phen_{phen['name']}"
                    if phen_id not in nodes:
                        nodes[phen_id] = {
                            "id": phen_id,
                            "label": phen["name"][:40],
                            "type": "Phenomenon",
                            "color": "#E74C3C"
                        }
                    
                    if record["r2"]:
                        edges.append({
                            "from": record["p"]["pmcid"],
                            "to": phen_id,
                            "label": "INVESTIGATES",
                            "color": "#E74C3C"
                        })
                
                # Platform node
                if record["pl"]:
                    plat = record["pl"]
                    plat_id = f"plat_{plat['name']}"
                    if plat_id not in nodes:
                        nodes[plat_id] = {
                            "id": plat_id,
                            "label": plat["name"],
                            "type": "Platform",
                            "color": "#F39C12"
                        }
                    
                    if record["r3"]:
                        edges.append({
                            "from": record["p"]["pmcid"],
                            "to": plat_id,
                            "label": "CONDUCTED_ON",
                            "color": "#F39C12"
                        })
                
                # Publication-Publication link
                if record["p2"] and record["r4"]:
                    edges.append({
                        "from": record["p"]["pmcid"],
                        "to": record["p2"]["pmcid"],
                        "label": f"BUILDS_ON ({record['r4'].get('similarity', 0):.2f})",
                        "color": "#9B59B6",
                        "dashes": True
                    })
            
            return list(nodes.values()), edges
    
    finally:
        neo4j_client.close()

def render_graph(nodes, edges):
    """Render interactive graph using Pyvis"""
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        notebook=True,
        directed=True
    )
    
    # Configure physics
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 200,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {"iterations": 150}
      }
    }
    """)
    
    # Add nodes
    for node in nodes:
        size = 30 if node["type"] == "Publication" else 20
        net.add_node(
            node["id"],
            label=node["label"],
            color=node["color"],
            size=size,
            title=f"<b>{node['type']}</b><br>{node.get('full_title', node['label'])}"
        )
    
    # Add edges
    for edge in edges:
        net.add_edge(
            edge["from"],
            edge["to"],
            label=edge.get("label", ""),
            color=edge.get("color", "#888888"),
            dashes=edge.get("dashes", False)
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        net.save_graph(f.name)
        return f.name

# Title
st.title(" NASA Space Biology Knowledge Search")
st.markdown("Search across 608 space biology publications with semantic understanding")

# Sidebar filters
with st.sidebar:
    st.header(" Search Settings")
    
    search_mode = st.selectbox(
        "Search Mode",
        options=[SearchMode.HYBRID, SearchMode.SEMANTIC, SearchMode.FULLTEXT],
        format_func=lambda x: {
            SearchMode.HYBRID: " Hybrid (Best)",
            SearchMode.SEMANTIC: " Semantic (Concepts)",
            SearchMode.FULLTEXT: " Full-Text (Keywords)"
        }[x]
    )
    
    limit = st.slider("Results per page", 5, 50, 7)
    min_similarity = st.slider("Min similarity", 0.1, 1.0, 0.3, 0.05)
    
    st.markdown("---")
    st.markdown("###  Filters")
    year_from = st.number_input("Year from", 2000, 2024, 2010)
    year_to = st.number_input("Year to", 2000, 2024, 2024)
    
    show_graph = st.checkbox(" Show Knowledge Graph", value=True)
    
    st.markdown("---")
    st.markdown("###  Example Queries")
    
    example_queries = {
        "🦴 Bone loss": "bone loss in microgravity",
        "🧬 Immune system": "immune dysregulation in spaceflight",
        " Muscle atrophy": "muscle atrophy weightlessness",
        "🧠 Neurological": "neurological changes space",
        " Cardiovascular": "cardiovascular adaptation microgravity"
    }
    
    for label, example_query in example_queries.items():
        if st.button(label, key=f"btn_{label}"):
            st.session_state.example_query = example_query

# Main search
query = st.text_input(
    " Search query", 
    value=st.session_state.get('example_query', ''),
    placeholder="e.g., bone loss in microgravity"
)

# Clear example query after use
if 'example_query' in st.session_state:
    del st.session_state.example_query

if query:
    with st.spinner(" Searching..."):
        try:
            results = run_search(
                query=query,
                mode=search_mode,
                limit=limit,
                min_similarity=min_similarity,
                year_from=year_from,
                year_to=year_to
            )
            
            # Display results
            if results["total_count"] == 0:
                st.warning("No results found. Try adjusting the similarity threshold or search terms.")
            else:
                st.success(f" Found {results['total_count']} results (page {results['page']}/{results['total_pages']})")
                
                # Knowledge Graph Visualization
                if show_graph and results["results"]:
                    st.markdown("---")
                    st.subheader(" Knowledge Graph - Research Connections")
                    
                    with st.spinner("Loading graph..."):
                        pmcids = [r.pmcid for r in results["results"]]
                        nodes, edges = fetch_graph_data(pmcids)
                        
                        if nodes:
                            # Graph stats
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Publications", len([n for n in nodes if n["type"] == "Publication"]))
                            col2.metric("Organisms", len([n for n in nodes if n["type"] == "Organism"]))
                            col3.metric("Phenomena", len([n for n in nodes if n["type"] == "Phenomenon"]))
                            
                            # Render graph
                            graph_file = render_graph(nodes, edges)
                            with open(graph_file, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            components.html(html_content, height=650)
                            
                            # Cleanup
                            os.unlink(graph_file)
                            
                            st.caption("""
                            **Legend:** 
                             Publications | 🟢 Organisms |  Phenomena | 🟠 Platforms | 
                            Purple dashed lines = BUILDS_ON relationships
                            """)
                        else:
                            st.info("No graph data available for these results.")
                
                st.markdown("---")
                
                # Add export button
                col1, col2 = st.columns([3, 1])
                with col2:
                    export_data = [
                        {
                            "PMCID": r.pmcid,
                            "Title": r.title,
                            "Score": r.score,
                            "Journal": r.journal,
                            "Date": r.publication_date
                        }
                        for r in results["results"]
                    ]
                    df = pd.DataFrame(export_data)
                    st.download_button(
                        " Export CSV",
                        df.to_csv(index=False),
                        "search_results.csv",
                        "text/csv"
                    )
                
                # Display results
                for i, result in enumerate(results["results"], 1):
                    with st.expander(
                        f"**{i}. {result.title}**  (Score: {result.score:.3f})",
                        expanded=(i == 1)  # Expand first result
                    ):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**PMCID:** `{result.pmcid}`")
                            
                            if result.journal:
                                st.markdown(f"**Journal:** {result.journal}")
                            
                            if result.publication_date:
                                st.markdown(f"**Date:** {result.publication_date}")
                            
                            st.markdown("**Abstract:**")
                            st.markdown(f"_{result.abstract}_")
                            
                            if result.full_text_snippet:
                                st.markdown("**Matched Text:**")
                                st.info(result.full_text_snippet)
                            
                            # Link to PubMed Central
                            st.markdown(f"[ View on PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/articles/{result.pmcid}/)")
                        
                        with col2:
                            st.metric("Similarity Score", f"{result.score:.3f}")
                            st.caption(f"Method: {result.search_method}")
                            st.caption(f"Type: {result.match_type or 'N/A'}")
                            
                            # Color-coded score indicator
                            if result.score > 0.7:
                                st.success("🟢 High Match")
                            elif result.score > 0.5:
                                st.info("🟡 Good Match")
                            else:
                                st.warning("🟠 Fair Match")
        
        except Exception as e:
            st.error(f" Search failed: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
     NASA Space Biology Knowledge Graph | 608 Publications | Powered by OpenAI + Neo4j + PostgreSQL
</div>
""", unsafe_allow_html=True)