"""
Test Generic RAG with ReAct
"""
import asyncio
from ai_generic_rag import GenericRAGService
import dspy
import os

async def test_react():
    llm = dspy.LM(
        "openai/mistral-small-latest",
        api_key=os.environ.get("MISTRAL_API_KEY"),
        api_base="https://api.mistral.ai/v1",
        max_tokens=2000000
    )
    
    service = GenericRAGService(llm)
    
    # Test 1: Simple search question
    print("\n" + "="*60)
    print("Test 1: What are the effects of microgravity on bones?")
    print("="*60)
    
    result = await service.ask("What are the effects of microgravity on bones?")
    
    print(f"\n Answer:\n{result['answer']}\n")
    print(f" Citations: {result.get('citations', [])}")
    print(f" Tools Used: {result.get('tools_used', [])}")
    print("\n🧠 Reasoning Trace:")
    for step in result.get('reasoning_trace', [])[:5]:
        print(f"   {step}")
    
    # Test 2: Follow-up question
    print("\n" + "="*60)
    print("Test 2: Who were the authors of the first study?")
    print("="*60)
    
    result = await service.ask("Who were the authors of the first study?")
    
    print(f"\n Answer:\n{result['answer']}\n")
    print(f" Tools Used: {result.get('tools_used', [])}")
    
    await service.close()


if __name__ == "__main__":
    asyncio.run(test_react())