#!/usr/bin/env python3
"""
Test script to debug SpoonOS agent responses
"""

import asyncio
import os
from ai_agent import AICodeGenerator

async def test_generation():
    """Test code generation and see what SpoonOS returns"""
    
    print("🧪 Testing SpoonOS Code Generation")
    print("=" * 60)
    
    # Initialize generator
    generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")
    
    if not generator.agent:
        print("❌ Agent not initialized")
        return
    
    print("✅ Agent initialized")
    print()
    
    # Test task
    task = "Create a Python module with two functions: one to validate emails and one to validate phone numbers"
    
    print(f"📝 Task: {task}")
    print()
    print("🤖 Running SpoonOS agent...")
    print()
    
    result = await generator.generate_code_for_task(task)
    
    print("=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print()
    
    print(f"Success: {result['success']}")
    print(f"Files generated: {len(result.get('files', []))}")
    print()
    
    if result['success']:
        for i, file in enumerate(result['files'], 1):
            print(f"\n{'='*60}")
            print(f"File {i}: {file['path']}")
            print(f"Description: {file['description']}")
            print(f"Content length: {len(file['content'])} characters")
            print(f"{'='*60}")
            print("\nContent preview:")
            print(file['content'][:300])
            print("...")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print()
    print("=" * 60)
    print("RAW RESPONSE (first 1000 chars):")
    print("=" * 60)
    print(result.get('raw_response', '')[:1000])

if __name__ == "__main__":
    asyncio.run(test_generation())

