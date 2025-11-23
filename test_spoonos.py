#!/usr/bin/env python3
"""
Test script to debug SpoonOS agent responses
"""

import asyncio
import os
import logging
from ai_agent import AICodeGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_generation():
    """Test code generation and see what SpoonOS returns"""
    
    logger.info("🧪 Testing SpoonOS Code Generation")
    logger.info("=" * 60)
    
    # Initialize generator
    generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")
    
    if not generator.agent:
        logger.error("❌ Agent not initialized")
        return
    
    logger.info("✅ Agent initialized")
    logger.info()
    
    # Test task
    task = "Create a Python module with two functions: one to validate emails and one to validate phone numbers"
    
    logger.info(f"📝 Task: {task}")
    logger.info()
    logger.info("🤖 Running SpoonOS agent...")
    logger.info()
    
    result = await generator.generate_code_for_task(task)
    
    logger.info("=" * 60)
    logger.info("📊 RESULTS")
    logger.info("=" * 60)
    logger.info()
    
    logger.info(f"Success: {result['success']}")
    logger.info(f"Files generated: {len(result.get('files', []))}")
    logger.info()
    
    if result['success']:
        for i, file in enumerate(result['files'], 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"File {i}: {file['path']}")
            logger.info(f"Description: {file['description']}")
            logger.info(f"Content length: {len(file['content'])} characters")
            logger.info(f"{'='*60}")
            logger.info("\nContent preview:")
            logger.info(file['content'][:300])
            logger.info("...")
    else:
        logger.error(f"❌ Error: {result.get('error')}")
    
    logger.info()
    logger.info("=" * 60)
    logger.info("RAW RESPONSE (first 1000 chars):")
    logger.info("=" * 60)
    logger.info(result.get('raw_response', '')[:1000])

if __name__ == "__main__":
    asyncio.run(test_generation())