"""
Multi-Hop RAG Assistant with ReAct Tools for NASA Publications
Uses DSPy ReAct for autonomous tool selection and execution
"""
import dspy
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from client import DatabaseClient, Publication, TextSection
from neo4j_client import Neo4jClient
from sqlalchemy import select, create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncio
import logging
import json
import os
import nest_asyncio
from dotenv import load_dotenv
import re

load_dotenv()
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None


# === Citation Tracking ===
class CitationTracker:
    """Track PMCIDs used during tool execution"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.used_pmcids = set()
        self.tool_calls = []
    
    def add_pmcid(self, pmcid: str, source_tool: str):
        """Add a PMCID that was used"""
        if pmcid and pmcid.startswith('PMC'):
            self.used_pmcids.add(pmcid)
            self.tool_calls.append(f"{source_tool}({pmcid})")
            logger.info(f" Tracked citation: {pmcid} from {source_tool}")
    
    def get_citations(self) -> List[str]:
        """Get list of cited PMCIDs"""
        return sorted(list(self.used_pmcids))


# Global citation tracker
citation_tracker = CitationTracker()


class PublicationTools:
    """Synchronous tools for ReAct agent with citation tracking"""
    
    def __init__(self):
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        logger.info(f" Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
        
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self.neo4j_client = Neo4jClient()
        self.db_client = DatabaseClient()
        
        logger.info(" PublicationTools initialized")

    def get_article_sections(self, pmcid: str, limit: int = 10) -> str:
        """Get list of section names for an article"""
        logger.info(f" Getting sections for {pmcid}")
        citation_tracker.add_pmcid(pmcid, "get_article_sections")
        
        try:
            with self.SessionLocal() as session:
                pub_result = session.execute(
                    select(Publication).where(Publication.pmcid == pmcid)
                )
                pub = pub_result.scalar_one_or_none()
                
                if not pub:
                    return f"Article {pmcid} not found in database"
                
                sections_result = session.execute(
                    select(TextSection.section_name, TextSection.section_order)
                    .where(TextSection.publication_id == pub.id)
                    .order_by(TextSection.section_order)
                    .limit(limit)
                )
                
                sections = sections_result.fetchall()
                
                if not sections:
                    return f"No sections found for {pmcid}"
                
                output = f"Sections available in {pmcid} ({pub.title[:50]}...):\n"
                for section_name, section_order in sections:
                    output += f"{section_order}. {section_name}\n"
                
                logger.info(f" Found {len(sections)} sections")
                return output
        
        except Exception as e:
            logger.error(f" Sections error: {e}")
            return f"Failed to get sections: {str(e)}"
    
    def get_section_content(self, pmcid: str, section_name: str, max_chars: int = 2000) -> str:
        """Get content of a specific section"""
        logger.info(f" Getting '{section_name}' content for {pmcid}")
        citation_tracker.add_pmcid(pmcid, "get_section_content")
        
        try:
            with self.SessionLocal() as session:
                pub_result = session.execute(
                    select(Publication).where(Publication.pmcid == pmcid)
                )
                pub = pub_result.scalar_one_or_none()
                
                if not pub:
                    return f"Article {pmcid} not found in database"
                
                section_result = session.execute(
                    select(TextSection.content, TextSection.section_name)
                    .where(
                        TextSection.publication_id == pub.id,
                        TextSection.section_name.ilike(f"%{section_name}%")
                    )
                    .limit(1)
                )
                
                section_row = section_result.first()
                
                if not section_row:
                    return f"Section '{section_name}' not found in {pmcid}"
                
                content, actual_section_name = section_row
                
                if len(content) > max_chars:
                    truncated_content = content[:max_chars] + "... [truncated]"
                else:
                    truncated_content = content
                
                output = f"Content of section '{actual_section_name}' in {pmcid}:\n\n"
                output += truncated_content
                
                logger.info(f" Retrieved {len(content)} characters")
                return output
        
        except Exception as e:
            logger.error(f" Section content error: {e}")
            return f"Failed to get section content: {str(e)}"
    
    def get_article_metadata(self, pmcid: str) -> str:
        """Get detailed metadata for an article"""
        logger.info(f" Getting metadata for {pmcid}")
        citation_tracker.add_pmcid(pmcid, "get_article_metadata")
        
        try:
            with self.SessionLocal() as session:
                result = session.execute(
                    select(Publication).where(Publication.pmcid == pmcid)
                )
                pub = result.scalar_one_or_none()
                
                if not pub:
                    return f"Article {pmcid} not found in database"
                
                output = f"[{pmcid}]\n"
                output += f"Title: {pub.title}\n"
                output += f"Journal: {pub.journal}\n"
                output += f"Date: {pub.publication_date}\n"
                
                if hasattr(pub, 'doi') and pub.doi:
                    output += f"DOI: {pub.doi}\n"
                
                output += f"\nAbstract:\n{pub.abstract[:500] if pub.abstract else 'N/A'}...\n"
                
                logger.info(f" Retrieved metadata")
                return output
        
        except Exception as e:
            logger.error(f" Metadata error: {e}")
            return f"Failed to get metadata: {str(e)}"
    
    def get_article_authors(self, pmcid: str) -> str:
        """Get list of authors for a specific article from PostgreSQL"""
        logger.info(f" Getting authors for {pmcid}")
        citation_tracker.add_pmcid(pmcid, "get_article_authors")
        
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("""
                    SELECT 
                        CONCAT(a.firstname, ' ', a.lastname) as name,
                        a.email,
                        a.orcid,
                        pa.author_order
                    FROM authors a
                    JOIN publication_authors pa ON a.id = pa.author_id
                    JOIN publications p ON pa.publication_id = p.id
                    WHERE p.pmcid = :pmcid
                    ORDER BY pa.author_order
                """), {"pmcid": pmcid})
                
                authors = result.fetchall()
                
                if not authors:
                    return f"No author information found for {pmcid}"
                
                logger.info(f" Found {len(authors)} authors")
                
                output = f"Authors of {pmcid} ({len(authors)} total):\n"
                for idx, (name, email, orcid, order) in enumerate(authors[:8], 1):
                    output += f"{order}. {name}"
                    if orcid:
                        output += f" (ORCID: {orcid})"
                    elif email:
                        output += f" ({email})"
                    output += "\n"
                
                if len(authors) > 8:
                    output += f"... and {len(authors) - 8} more authors\n"
                
                return output
        
        except Exception as e:
            logger.error(f" Author lookup error: {e}", exc_info=True)
            return f"Failed to get authors: {str(e)}"
    
    def get_related_articles(self, pmcid: str, limit: int = 3) -> str:
        """Get semantically related articles"""
        logger.info(f" Getting related articles for {pmcid}")
        citation_tracker.add_pmcid(pmcid, "get_related_articles")
        
        try:
            with self.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (p1:Publication {pmcid: $pmcid})-[r:BUILDS_ON]-(p2:Publication)
                    RETURN p2.pmcid AS pmcid, r.similarity AS similarity
                    ORDER BY r.similarity DESC
                    LIMIT $limit
                """, pmcid=pmcid, limit=limit)
                
                related = [
                    {"pmcid": record["pmcid"], "similarity": record["similarity"]}
                    for record in result
                ]
                
                #  Track related PMCIDs
                for rel in related:
                    citation_tracker.add_pmcid(rel["pmcid"], "get_related_articles")
                
                if not related:
                    return f"No related articles found for {pmcid}"
                
                output = f"Related articles to {pmcid}:\n"
                for rel in related:
                    output += f"- {rel['pmcid']} (similarity: {rel['similarity']:.3f})\n"
                
                logger.info(f" Found {len(related)} related articles")
                return output
        
        except Exception as e:
            logger.error(f" Related articles error: {e}")
            return f"Failed: {str(e)}"
    
    def search_by_organism(self, organism: str, limit: int = 5) -> str:
        """Find articles studying a specific organism"""
        logger.info(f"🧬 Searching articles for organism: {organism}")
        
        try:
            with self.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (p:Publication)-[:STUDIES]->(o:Organism)
                    WHERE toLower(o.name) CONTAINS toLower($organism)
                       OR toLower(o.scientific_name) CONTAINS toLower($organism)
                    RETURN DISTINCT p.pmcid AS pmcid
                    LIMIT $limit
                """, organism=organism, limit=limit)
                
                pmcids = [record["pmcid"] for record in result]
                
                #  Track PMCIDs from organism search
                for pmcid in pmcids:
                    citation_tracker.add_pmcid(pmcid, "search_by_organism")
                
                if not pmcids:
                    return f"No articles found studying {organism}"
                
                logger.info(f" Found {len(pmcids)} articles")
                return f"Found {len(pmcids)} articles studying {organism}:\n" + ", ".join(pmcids)
        
        except Exception as e:
            logger.error(f" Organism search error: {e}")
            return f"Search failed: {str(e)}"
    
    def search_by_phenomenon(self, phenomenon: str, limit: int = 5) -> str:
        """Find articles investigating a specific phenomenon"""
        logger.info(f" Searching articles for phenomenon: {phenomenon}")
        
        try:
            with self.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (p:Publication)-[:INVESTIGATES]->(ph:Phenomenon)
                    WHERE toLower(ph.name) CONTAINS toLower($phenomenon)
                    RETURN DISTINCT p.pmcid AS pmcid
                    LIMIT $limit
                """, phenomenon=phenomenon, limit=limit)
                
                pmcids = [record["pmcid"] for record in result]
                
                #  Track PMCIDs from phenomenon search
                for pmcid in pmcids:
                    citation_tracker.add_pmcid(pmcid, "search_by_phenomenon")
                
                if not pmcids:
                    return f"No articles found investigating {phenomenon}"
                
                logger.info(f" Found {len(pmcids)} articles")
                return f"Found {len(pmcids)} articles investigating {phenomenon}:\n" + ", ".join(pmcids)
        
        except Exception as e:
            logger.error(f" Phenomenon search error: {e}")
            return f"Search failed: {str(e)}"
    
    def search_by_mesh_term(self, mesh_term: str, limit: int = 5) -> str:
        """Find articles by MeSH term"""
        logger.info(f" Searching articles for MeSH term: {mesh_term}")
        
        try:
            with self.neo4j_client.driver.session() as session:
                result = session.run("""
                    MATCH (p:Publication)-[:HAS_MESH_TERM]->(m:MeshTerm)
                    WHERE toLower(m.name) CONTAINS toLower($mesh_term)
                       OR toLower(m.descriptor) CONTAINS toLower($mesh_term)
                    RETURN DISTINCT p.pmcid AS pmcid
                    LIMIT $limit
                """, mesh_term=mesh_term, limit=limit)
                
                pmcids = [record["pmcid"] for record in result]
                
                #  Track PMCIDs from MeSH search
                for pmcid in pmcids:
                    citation_tracker.add_pmcid(pmcid, "search_by_mesh_term")
                
                if not pmcids:
                    return f"No articles found with MeSH term '{mesh_term}'"
                
                logger.info(f" Found {len(pmcids)} articles")
                return f"Found {len(pmcids)} articles with MeSH term '{mesh_term}':\n" + ", ".join(pmcids)
        
        except Exception as e:
            logger.error(f" MeSH search error: {e}")
            return f"Search failed: {str(e)}"
    
    def close(self):
        self.neo4j_client.close()
        logger.info(" Closed connections")


#  Initialize tools ONCE at module level
logger.info(" Initializing PublicationTools...")
_tools_instance = PublicationTools()
logger.info(" PublicationTools ready")


def get_tools_instance():
    """Get singleton tools instance"""
    return _tools_instance


# === Tool Functions for ReAct ===

def get_article_sections(pmcid: str, limit: int = 10) -> str:
    """Get list of section names for an article"""
    return get_tools_instance().get_article_sections(pmcid, limit)


def get_section_content(pmcid: str, section_name: str, max_chars: int = 2000) -> str:
    """Get content of a specific section from an article"""
    return get_tools_instance().get_section_content(pmcid, section_name, max_chars)


def get_article_metadata(pmcid: str) -> str:
    """Get detailed metadata for an article"""
    return get_tools_instance().get_article_metadata(pmcid)


def get_article_authors(pmcid: str) -> str:
    """Get list of authors for a specific article"""
    return get_tools_instance().get_article_authors(pmcid)


def get_related_articles(pmcid: str, limit: int = 3) -> str:
    """Get semantically related articles"""
    return get_tools_instance().get_related_articles(pmcid, limit)


def search_by_organism(organism: str, limit: int = 5) -> str:
    """Find articles studying a specific organism"""
    return get_tools_instance().search_by_organism(organism, limit)


def search_by_phenomenon(phenomenon: str, limit: int = 5) -> str:
    """Find articles investigating a specific phenomenon"""
    return get_tools_instance().search_by_phenomenon(phenomenon, limit)


def search_by_mesh_term(mesh_term: str, limit: int = 5) -> str:
    """Find articles by MeSH term"""
    return get_tools_instance().search_by_mesh_term(mesh_term, limit)


# === DSPy Citation Extraction ===

class CitationExtraction(dspy.Signature):
    """Extract cited PMCIDs from answer text and tool usage"""
    
    answer: str = dspy.InputField(desc="Generated answer text")
    tool_usage: str = dspy.InputField(desc="List of tools used with PMCIDs")
    
    cited_pmcids: List[str] = dspy.OutputField(desc="List of PMCIDs that were used to generate the answer")


class CitationExtractor(dspy.Module):
    """Extract citations from answer and tool usage"""
    
    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(CitationExtraction)
    
    def forward(self, answer: str, tool_usage: str) -> List[str]:
        """Extract PMCIDs that were actually used"""
        try:
            result = self.extract(answer=answer, tool_usage=tool_usage)
            
            # Validate PMCIDs
            valid_pmcids = []
            if hasattr(result, 'cited_pmcids') and result.cited_pmcids:
                for pmcid in result.cited_pmcids:
                    if isinstance(pmcid, str) and re.match(r'^PMC\d+$', pmcid.strip()):
                        valid_pmcids.append(pmcid.strip())
            
            return valid_pmcids
        except:
            return []


# === ReAct Agent ===

class RAGAssistant(dspy.Module):
    """Multi-hop RAG assistant with autonomous tool use via ReAct"""
    
    def __init__(self, llm: Optional[dspy.LM] = None):
        super().__init__()
        
        if llm:
            dspy.settings.configure(lm=llm)
        
        logger.info("🤖 Configuring ReAct agent with tools...")
        
        class RAGSignature(dspy.Signature):
            """Answer scientific questions using available tools like a researcher with proper citations"""
            question = dspy.InputField(desc="Scientific question about publications")
            answer = dspy.OutputField(desc="Comprehensive answer with specific details and citations")

        self.agent = dspy.ReAct(
            signature=RAGSignature,
            tools=[
                get_article_sections,
                get_section_content,
                get_article_metadata,
                get_article_authors,
                get_related_articles,
                search_by_organism,
                search_by_phenomenon,
                search_by_mesh_term
            ],
            max_iters=8  #  Plus d'itérations pour multi-hop
        )
        
        #  Citation extractor
        self.citation_extractor = CitationExtractor()
        
        logger.info(" ReAct agent ready with 8 tools + citation extraction")
    
    def forward(self, question: str, conversation_context: Optional[List[Dict]] = None) -> Dict:
        """Answer question using ReAct - AI autonomously decides which tools to use"""
        logger.info(f"🤖 Processing question: {question[:100]}...")
        
        #  Reset citation tracker for new question
        citation_tracker.reset()
        
        #  Add conversation context to question if available
        context_question = question
        if conversation_context:
            last_interactions = conversation_context[-2:]  # Dernières 2 interactions
            if last_interactions:
                context_summary = "\n\nPrevious conversation context:\n"
                for entry in last_interactions:
                    context_summary += f"Q: {entry['question']}\nA: {entry['answer'][:150]}...\n\n"
                context_question = context_summary + f"Current question: {question}"
        
        try:
            result = self.agent(question=context_question)
            
            reasoning_trace = []
            tools_used = []
            
            if hasattr(result, '__dict__'):
                for key, value in result.__dict__.items():
                    if 'thought' in key.lower() and value:
                        reasoning_trace.append(f" {value}")
                    elif ('action' in key.lower() or 'tool' in key.lower()) and value:
                        tools_used.append(str(value))
                        reasoning_trace.append(f" {value}")
                    elif 'observation' in key.lower() and value:
                        obs_text = str(value)[:200]
                        reasoning_trace.append(f" {obs_text}...")
            
            answer_text = result.answer if hasattr(result, 'answer') else str(result)
            
            #  Get citations from tracker (method principale)
            tracked_citations = citation_tracker.get_citations()
            
            #  Also try DSPy extraction as backup
            tool_usage_text = " | ".join(citation_tracker.tool_calls)
            try:
                extracted_citations = self.citation_extractor(
                    answer=answer_text,
                    tool_usage=tool_usage_text
                )
            except:
                extracted_citations = []
            
            #  Combine both methods
            all_citations = list(set(tracked_citations + extracted_citations))
            
            logger.info(f" Generated answer with {len(all_citations)} citations, {len(set(tools_used))} tools used")
            logger.info(f" Citations: {all_citations}")
            
            return {
                'answer': answer_text,
                'citations': all_citations,
                'reasoning_trace': reasoning_trace,
                'tools_used': list(set(tools_used)),
                'confidence': 'high' if len(all_citations) > 0 else 'medium'
            }
        
        except Exception as e:
            logger.error(f" ReAct error: {e}", exc_info=True)
            return {
                'answer': f"I encountered an error: {str(e)}",
                'citations': [],
                'reasoning_trace': [f"Error: {str(e)}"],
                'tools_used': [],
                'confidence': 'low'
            }


# === Service Wrapper ===

class RAGService:
    """Service wrapper for RAG assistant with conversation state"""
    
    def __init__(self, llm: Optional[dspy.LM] = None):
        self.assistant = RAGAssistant(llm)
        self.conversation_history = []
    
    async def ask(
        self, 
        question: str, 
        pmcids: Optional[List[str]] = None
    ) -> Dict:
        """Ask a question about publications with conversation memory"""
        
        #  Si des PMCIDs sont fournis, enrichir la question
        if pmcids:
            question_with_context = f"Based on articles {', '.join(pmcids)}: {question}"
        else:
            question_with_context = question
        
        #  Passer l'historique conversationnel
        result = self.assistant(
            question=question_with_context,
            conversation_context=self.conversation_history
        )
        
        result['question'] = question
        
        #  Sauvegarder dans l'historique
        self.conversation_history.append({
            'question': question,
            'answer': result['answer'],
            'citations': result['citations']
        })
        
        #  Limiter l'historique à 10 dernières interactions
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return result
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info(" Conversation history cleared")
    
    async def close(self):
        pass


# === CLI for Testing ===

async def main():
    """Interactive CLI for testing RAG assistant"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configure LLM
    llm = dspy.LM(
        "openai/mistral-small-latest",
        api_key=os.environ.get("MISTRAL_API_KEY"),
        api_base="https://api.mistral.ai/v1",
        max_tokens=2000
    )
    
    service = RAGService(llm)
    
    print("\n🤖 NASA Publications RAG Assistant with ReAct")
    print("="*60)
    print("Ask questions about space biology research!")
    print("I'll autonomously search and use the right tools.\n")
    print("Available tools:")
    print("• get_article_sections, get_section_content")
    print("• get_article_metadata, get_article_authors")
    print("• get_related_articles")
    print("• search_by_organism, search_by_phenomenon, search_by_mesh_term\n")
    
    try:
        while True:
            question = input("\n Your question (or 'quit'): ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question.lower() == 'clear':
                service.clear_history()
                print(" Conversation history cleared")
                continue
            
            pmcids_input = input(" Optional PMCIDs (comma-separated, or press Enter): ").strip()
            pmcids = [p.strip() for p in pmcids_input.split(',')] if pmcids_input else None
            
            print("\n🤖 Thinking and using tools autonomously...\n")
            
            result = await service.ask(question, pmcids)
            
            print(f" Answer:\n{result['answer']}\n")
            
            if result.get('citations'):
                print(f" Sources: {', '.join(result['citations'])}")
            
            print(f" Tools Used: {', '.join(result.get('tools_used', []))}")
            print(f" Confidence: {result.get('confidence', 'unknown')}")
            
            if result.get('reasoning_trace'):
                print(f"\n🧠 Reasoning Trace:")
                for step in result['reasoning_trace'][:8]:
                    print(f"   {step}")
    
    finally:
        await service.close()
        print("\n Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())