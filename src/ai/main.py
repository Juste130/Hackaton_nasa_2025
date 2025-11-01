"""
AI Main Module - AI Agents and Models Testing
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agents():
    """Test AI agents functionality"""
    print(" Testing AI Agents...")
    
    choice = input("""
Choose agent to test:
1. RAG Assistant
2. Summarizer
3. Generic RAG
4. Abstract Generator
5. Test all agents
Enter choice (1-5): """)
    
    if choice == "1":
        test_rag_assistant()
    elif choice == "2":
        test_summarizer()
    elif choice == "3":
        test_generic_rag()
    elif choice == "4":
        test_abstract_generator()
    elif choice == "5":
        test_all_agents()
    else:
        print("Invalid choice")

def test_rag_assistant():
    """Test RAG Assistant"""
    try:
        from .agents.ai_rag_assistant import RAGService
        print(" RAG Assistant available")
    except ImportError as e:
        print(f" Could not import RAG Assistant: {e}")

def test_summarizer():
    """Test Summarizer"""
    try:
        from .agents.ai_summarizer import SummaryService
        print(" Summarizer available")
    except ImportError as e:
        print(f" Could not import Summarizer: {e}")

def test_generic_rag():
    """Test Generic RAG"""
    try:
        from .agents.ai_generic_rag import GenericRAGService
        print(" Generic RAG available")
    except ImportError as e:
        print(f" Could not import Generic RAG: {e}")

def test_abstract_generator():
    """Test Abstract Generator"""
    try:
        from .agents.abstract_generator import AbstractGenerator
        print(" Abstract Generator available")
    except ImportError as e:
        print(f" Could not import Abstract Generator: {e}")

def test_all_agents():
    """Test all available agents"""
    print(" Testing all agents...")
    test_rag_assistant()
    test_summarizer()
    test_generic_rag()
    test_abstract_generator()
    print(" Agent testing complete!")

if __name__ == "__main__":
    test_agents()