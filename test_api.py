"""
Test script for AI API with sessions
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_generic_rag():
    """Test Generic RAG with session"""
    print("\n" + "="*60)
    print("🧪 Testing Generic RAG")
    print("="*60)
    
    # 1. Create session
    response = requests.post(f"{BASE_URL}/api/sessions", json={
        "service_type": "generic_rag",
        "metadata": {"user": "test_user"}
    })
    
    session = response.json()
    session_id = session['session_id']
    print(f"\n Created session: {session_id}")
    
    # 2. Ask first question
    response = requests.post(
        f"{BASE_URL}/api/rag/generic",
        headers={"X-Session-ID": session_id},
        json={
            "question": "What are the effects of microgravity on bone density?",
            "top_k": 5,
            "search_mode": "hybrid"
        }
    )
    
    answer1 = response.json()
    print(f"\n Q1: What are the effects of microgravity on bone density?")
    print(f" A1: {answer1['answer'][:200]}...")
    print(f" Citations: {', '.join(answer1['citations'][:3])}")
    
    # 3. Ask follow-up question
    response = requests.post(
        f"{BASE_URL}/api/rag/generic",
        headers={"X-Session-ID": session_id},
        json={
            "question": "Who were the authors of the first article?",
            "top_k": 3,
            "search_mode": "hybrid"
        }
    )
    
    answer2 = response.json()
    print(f"\n Q2: Who were the authors of the first article?")
    print(f" A2: {answer2['answer'][:200]}...")
    
    # 4. Get session history
    response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/history")
    history = response.json()
    
    print(f"\n Session History ({history['message_count']} messages)")
    for msg in history['messages']:
        print(f"  {msg['role']}: {msg['content'][:80]}...")
    
    # 5. Clean up
    requests.delete(f"{BASE_URL}/api/sessions/{session_id}")
    print(f"\n Deleted session")


def test_rag_assistant():
    """Test RAG Assistant with specific PMCIDs"""
    print("\n" + "="*60)
    print("🧪 Testing RAG Assistant")
    print("="*60)
    
    # Create session
    response = requests.post(f"{BASE_URL}/api/sessions", json={
        "service_type": "rag_assistant"
    })
    
    session_id = response.json()['session_id']
    print(f"\n Created session: {session_id}")
    
    # Ask with specific PMCIDs
    response = requests.post(
        f"{BASE_URL}/api/rag/ask",
        headers={"X-Session-ID": session_id},
        json={
            "question": "What organisms were studied?",
            "pmcids": ["PMC4136787", "PMC5234567"]
        }
    )
    
    answer = response.json()
    print(f"\n Answer: {answer['answer'][:200]}...")
    print(f" Citations: {', '.join(answer['citations'])}")
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/sessions/{session_id}")


def test_summarizer():
    """Test Summarizer"""
    print("\n" + "="*60)
    print("🧪 Testing Summarizer")
    print("="*60)
    
    # Create session
    response = requests.post(f"{BASE_URL}/api/sessions", json={
        "service_type": "summarizer"
    })
    
    session_id = response.json()['session_id']
    print(f"\n Created session: {session_id}")
    
    # Summarize
    response = requests.post(
        f"{BASE_URL}/api/summarize",
        headers={"X-Session-ID": session_id},
        json={"pmcid": "PMC4136787"}
    )
    
    summary = response.json()
    print(f"\n Title: {summary['title']}")
    print(f" Summary: {summary['summary']['executive_summary'][:200]}...")
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/sessions/{session_id}")


if __name__ == "__main__":
    test_generic_rag()
    test_rag_assistant()
    test_summarizer()
    
    print("\n" + "="*60)
    print(" All tests completed!")
    print("="*60)