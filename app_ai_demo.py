"""
Streamlit Demo App for AI Modules
Test Summarizer + RAG Assistant in one interface
"""
import streamlit as st
import asyncio
import os
from typing import List, Optional
import dspy
from ai_summarizer import SummaryService
from ai_rag_assistant import RAGService
from search_engine import HybridSearchEngine, SearchMode  # ← AJOUTEZ
from client import DatabaseClient, Publication
from sqlalchemy import select, func, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="🤖 NASA AI Assistant Demo",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (inchangé)
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e8f4f8;
        border-left-color: #2196F3;
    }
    .search-result {
        padding: 0.8rem;
        border-left: 3px solid #667eea;
        margin-bottom: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .score-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        background-color: #e3f2fd;
        color: #1976d2;
    }
</style>
""", unsafe_allow_html=True)


# === Initialize Services ===

@st.cache_resource
def get_llm():
    """Initialize DSPy LLM (cached)"""
    return dspy.LM(
        "openai/mistral-small-latest",
        api_key=os.environ.get("MISTRAL_API_KEY"),
        api_base="https://api.mistral.ai/v1",
        max_tokens=2000000
    )


@st.cache_resource
def get_search_engine():
    """Initialize hybrid search engine (cached)"""
    return HybridSearchEngine()


@st.cache_resource
def get_services():
    """Initialize AI services (cached)"""
    llm = get_llm()
    rag_service = RAGService(llm)  # ← Créer une instance persistante
    
    return {
        'summarizer': SummaryService(llm),
        'rag': rag_service,  # ← Réutiliser la même instance
        'search_engine': get_search_engine()
    }


services = get_services()


# === Helper Functions ===

def run_async(coro):
    """Run async function in new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def search_publications_hybrid(
    query: str, 
    mode: SearchMode = SearchMode.HYBRID,
    limit: int = 10
) -> List[dict]:
    """
    Search publications using hybrid search engine
    Returns list of dicts with pmcid, title, journal, score, method
    """
    try:
        # Use hybrid search engine
        search_results = run_async(
            services['search_engine'].search(
                query=query,
                mode=mode,
                limit=limit,
                min_similarity=0.3
            )
        )
        
        # Convert SearchResult objects to dicts
        results = []
        for result in search_results['results']:
            results.append({
                'pmcid': result.pmcid,
                'title': result.title,
                'journal': result.journal,
                'abstract': result.abstract,
                'score': result.score,
                'search_method': result.search_method,
                'match_type': result.match_type
            })
        
        return results
    
    except Exception as e:
        st.error(f" Search error: {str(e)}")
        return []


def get_random_pmcids_sync(n: int = 5) -> List[str]:
    """Get random PMCIDs for testing (fallback method)"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    postgres_url = os.getenv("POSTGRES_URL")
    sync_url = postgres_url.replace("postgresql+asyncpg://", "postgresql://")
    if not sync_url.startswith("postgresql://"):
        sync_url = f"postgresql://{sync_url}"
    
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        result = session.execute(
            text("SELECT pmcid FROM publications ORDER BY RANDOM() LIMIT :limit"),
            {"limit": n}
        )
        return [row.pmcid for row in result]


# === Sidebar ===

with st.sidebar:
    st.title(" NASA AI Assistant")
    st.markdown("---")
    
    st.markdown("###  Choose Module")
    module = st.radio(
        "Select functionality:",
        options=[" Article Summarizer", " RAG Q&A Assistant"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    search_option = None
    search_mode_option = None
    
    if module == " Article Summarizer":
        st.markdown("###  Find Article")
        search_option = st.radio(
            "How to find article?",
            ["Enter PMCID", "Search by keyword", "Random article"],
            label_visibility="collapsed"
        )
        
        # Search mode selector (only for keyword search)
        if search_option == "Search by keyword":
            st.markdown("###  Search Mode")
            search_mode_option = st.radio(
                "Search strategy:",
                ["Hybrid (Best)", "Semantic Only", "Keyword Only"],
                label_visibility="collapsed",
                help="Hybrid combines semantic understanding with keyword matching"
            )
    else:
        st.markdown("###  Tips")
        st.info("""
        **How to use RAG Assistant:**
        1. Search for relevant articles
        2. Select 1-3 articles
        3. Ask a question
        4. Get AI-powered answer with citations!
        """)
        
        # Search mode for RAG
        st.markdown("###  Search Mode")
        search_mode_option = st.radio(
            "Search strategy:",
            ["Hybrid (Best)", "Semantic Only", "Keyword Only"],
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    st.caption("Powered by DSPy + Mistral AI")


# Map search mode option to SearchMode enum
def get_search_mode(option: str) -> SearchMode:
    if option == "Semantic Only":
        return SearchMode.SEMANTIC
    elif option == "Keyword Only":
        return SearchMode.FULLTEXT
    else:  # Hybrid (Best)
        return SearchMode.HYBRID


# === Main Content ===

st.title(f"{module}")

# ==========================================
# MODULE 1: ARTICLE SUMMARIZER
# ==========================================

if module == " Article Summarizer":
    
    selected_pmcid = None
    
    if search_option == "Enter PMCID":
        col1, col2 = st.columns([3, 1])
        with col1:
            pmcid_input = st.text_input(
                "Enter PMCID:",
                placeholder="e.g., PMC4136787",
                key="pmcid_direct"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(" Load", key="load_direct"):
                if pmcid_input:
                    selected_pmcid = pmcid_input.strip()
    
    elif search_option == "Search by keyword":
        search_query = st.text_input(
            "Search publications:",
            placeholder="e.g., bone density microgravity",
            key="search_keyword"
        )
        
        if search_query:
            # Get selected search mode
            mode = get_search_mode(search_mode_option or "Hybrid (Best)")
            
            with st.spinner(f" Searching ({mode.value})..."):
                results = search_publications_hybrid(
                    search_query, 
                    mode=mode,
                    limit=10
                )
            
            if results:
                st.success(f" Found {len(results)} publications using {mode.value} search")
                
                # Display results with enhanced info
                for i, r in enumerate(results, 1):
                    with st.container():
                        col1, col2 = st.columns([0.9, 0.1])
                        
                        with col1:
                            st.markdown(f"""
                            <div class="search-result">
                                <strong>{i}. {r['title']}</strong><br>
                                <small> {r['journal']} |  {r['pmcid']}</small><br>
                                <small> Score: <span class="score-badge">{r['score']:.3f}</span> 
                                | Method: {r['search_method']} | Match: {r['match_type']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("Select", key=f"select_sum_{r['pmcid']}"):
                                selected_pmcid = r['pmcid']
                                st.session_state.selected_pmcid_sum = selected_pmcid
                                st.rerun()
                
                # Use session state to persist selection
                if 'selected_pmcid_sum' in st.session_state:
                    selected_pmcid = st.session_state.selected_pmcid_sum
            else:
                st.warning("No publications found. Try different keywords or search mode.")
    
    else:  # Random article
        if st.button(" Pick Random Article", key="random"):
            with st.spinner("Finding random article..."):
                random_pmcids = get_random_pmcids_sync(1)
                if random_pmcids:
                    selected_pmcid = random_pmcids[0]
                    st.session_state.random_pmcid = selected_pmcid
        
        if 'random_pmcid' in st.session_state:
            selected_pmcid = st.session_state.random_pmcid
            st.info(f" Selected: {selected_pmcid}")
    
    # Generate summary
    if selected_pmcid:
        st.markdown("---")
        
        if st.button(" Generate AI Summary", type="primary", key="generate_summary"):
            with st.spinner(f"🤖 Generating summary for {selected_pmcid}..."):
                try:
                    summary_data = run_async(
                        services['summarizer'].summarize_by_pmcid(selected_pmcid)
                    )
                    
                    st.markdown(f"""
                    <div class="summary-card">
                        <h2> {summary_data['title']}</h2>
                        <p><strong>PMCID:</strong> {summary_data['pmcid']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("###  Executive Summary")
                    st.info(summary_data['summary']['executive_summary'])
                    
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        " Key Findings",
                        " Methodology",
                        "🧬 Organisms",
                        " Space Relevance",
                        " Future Directions"
                    ])
                    
                    with tab1:
                        st.markdown(summary_data['summary']['key_findings'])
                    with tab2:
                        st.markdown(summary_data['summary']['methodology'])
                    with tab3:
                        st.markdown(summary_data['summary']['organisms_studied'])
                    with tab4:
                        st.markdown(summary_data['summary']['space_relevance'])
                    with tab5:
                        st.markdown(summary_data['summary']['future_directions'])
                    
                    st.markdown("---")
                    import json
                    summary_json = json.dumps(summary_data, indent=2)
                    st.download_button(
                        " Download Summary (JSON)",
                        summary_json,
                        file_name=f"summary_{selected_pmcid}.json",
                        mime="application/json"
                    )
                    
                except Exception as e:
                    st.error(f" Error generating summary: {str(e)}")
                    st.exception(e)


# ==========================================
# MODULE 2: RAG Q&A ASSISTANT
# ==========================================

else:  # RAG Assistant
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = []
    
    st.markdown("###  Step 1: Select Articles")
    
    #  AJOUT : Sélecteur de méthode de sélection
    selection_method = st.radio(
        "How would you like to select articles?",
        options=[" Search & Select", " Enter PMCIDs Manually", " Both Methods"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # ========== METHOD 1: MANUAL PMCID ENTRY ==========
    if selection_method in [" Enter PMCIDs Manually", " Both Methods"]:
        st.markdown("####  Manual Entry")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            manual_pmcids = st.text_input(
                "Enter PMCIDs (comma-separated):",
                placeholder="e.g., PMC4136787, PMC5234567, PMC9876543",
                key="manual_pmcids_input",
                help="Enter multiple PMCIDs separated by commas"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(" Add PMCIDs", key="add_manual_pmcids"):
                if manual_pmcids:
                    # Parse and validate PMCIDs
                    pmcids = [p.strip().upper() for p in manual_pmcids.split(',')]
                    pmcids = [p if p.startswith('PMC') else f'PMC{p}' for p in pmcids]
                    
                    # Add to selected articles (avoid duplicates)
                    added = 0
                    for pmcid in pmcids:
                        if pmcid not in st.session_state.selected_articles:
                            st.session_state.selected_articles.append(pmcid)
                            added += 1
                    
                    if added > 0:
                        st.success(f" Added {added} article(s)")
                        st.rerun()
                    else:
                        st.info("ℹ All PMCIDs already selected")
        
        # Display manually added articles
        if st.session_state.selected_articles:
            manual_articles = st.session_state.selected_articles.copy()
            if manual_articles:
                st.markdown("**Manually added articles:**")
                for pmcid in manual_articles:
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.markdown(f"• `{pmcid}`")
                    with col2:
                        if st.button("", key=f"remove_manual_{pmcid}", help="Remove"):
                            st.session_state.selected_articles.remove(pmcid)
                            st.rerun()
        
        if selection_method == " Both Methods":
            st.markdown("---")
    
    # ========== METHOD 2: HYBRID SEARCH ==========
    if selection_method in [" Search & Select", " Both Methods"]:
        st.markdown("####  Search & Select")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query_rag = st.text_input(
                "Search for relevant articles:",
                placeholder="e.g., immune system spaceflight",
                key="search_rag"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(" Search", key="search_btn_rag"):
                if search_query_rag:
                    mode = get_search_mode(search_mode_option or "Hybrid (Best)")
                    
                    with st.spinner(f" Searching ({mode.value})..."):
                        results = search_publications_hybrid(
                            search_query_rag,
                            mode=mode,
                            limit=15
                        )
                        st.session_state.search_results = results
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            st.success(f" Found {len(st.session_state.search_results)} publications")
            
            for result in st.session_state.search_results[:10]:
                col1, col2 = st.columns([0.1, 0.9])
                
                with col1:
                    selected = st.checkbox(
                        "Select article",
                        key=f"select_{result['pmcid']}",
                        value=result['pmcid'] in st.session_state.selected_articles,
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown(f"""
                    <div class="search-result">
                        <strong>{result['pmcid']}</strong> - {result['title']}<br>
                        <small> {result['journal']} | Score: <span class="score-badge">{result['score']:.3f}</span></small>
                    </div>
                    """, unsafe_allow_html=True)
                
                if selected and result['pmcid'] not in st.session_state.selected_articles:
                    st.session_state.selected_articles.append(result['pmcid'])
                elif not selected and result['pmcid'] in st.session_state.selected_articles:
                    st.session_state.selected_articles.remove(result['pmcid'])
    
    # ========== SUMMARY & ACTIONS ==========
    st.markdown("---")
    
    if st.session_state.selected_articles:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(f" **{len(st.session_state.selected_articles)} article(s) selected:**")
            st.markdown(", ".join([f"`{p}`" for p in st.session_state.selected_articles]))
        
        with col2:
            if st.button(" Clear All", key="clear_selection_all"):
                st.session_state.selected_articles = []
                st.rerun()
    else:
        st.info("ℹ No articles selected yet. Use manual entry or search to add articles.")
    
    st.markdown("---")
    
    # ========== STEP 2: ASK QUESTIONS (reste inchangé) ==========
    st.markdown("###  Step 2: Ask Questions")
    
    #  AJOUT : Afficher le nombre d'interactions
    if services['rag'].conversation_history:
        st.caption(f" Conversation history: {len(services['rag'].conversation_history)} exchanges")
    
    for message in st.session_state.chat_history:
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong> You:</strong><br>{message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>{message['content']}
            </div>
            """, unsafe_allow_html=True)
            
            if message.get('citations'):
                st.caption(f" Sources: {', '.join(message['citations'])}")
            
            if message.get('confidence'):
                confidence_color = {
                    'high': '🟢',
                    'medium': '🟡',
                    'low': ''
                }
                conf_level = message['confidence'].split(':')[0].lower()
                st.caption(f"{confidence_color.get(conf_level, '')} Confidence: {message['confidence']}")
    
    question = st.text_input(
        "Ask a question about the selected articles:",
        placeholder="e.g., How does microgravity affect bone density?",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 5])
    
    with col1:
        ask_button = st.button(" Ask", type="primary", key="ask_btn")
    
    with col2:
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button(" Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                services['rag'].clear_history()
                st.rerun()
        
        with col2b:
            if st.button(" New Topic", key="new_topic"):
                st.session_state.chat_history = []
                st.session_state.selected_articles = []
                services['rag'].clear_history()
                st.rerun()
    
    if ask_button and question:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question
        })
        
        with st.spinner("🤖 Thinking..."):
            try:
                result = run_async(
                    services['rag'].ask(
                        question,
                        pmcids=st.session_state.selected_articles if st.session_state.selected_articles else None
                    )
                )
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result['answer'],
                    'citations': result.get('citations', []),
                    'confidence': result.get('confidence', 'unknown'),
                    'reasoning_steps': result.get('reasoning_steps', [])
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f" Error: {str(e)}")
                st.exception(e)
    
    if st.session_state.chat_history:
        last_message = st.session_state.chat_history[-1]
        if last_message['role'] == 'assistant' and last_message.get('reasoning_steps'):
            with st.expander("🧠 View Reasoning Steps"):
                for i, step in enumerate(last_message['reasoning_steps'], 1):
                    st.markdown(f"{i}. {step}")


# === Footer ===

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
     NASA Space Biology AI Assistant | Powered by DSPy + Mistral AI<br>
     608 Publications | 🧬 45+ Organisms |  120+ Phenomena
</div>
""", unsafe_allow_html=True)