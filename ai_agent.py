"""
AI Agent Module using Direct OpenAI API
Generates code based on task descriptions

Note: Old SpoonOS implementation moved to spoon_os_client.py for reference
"""

import os
import logging
from typing import Dict, List, Optional
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICodeGenerator:
    """High-level interface for AI code generation using direct OpenAI API"""
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
        """
        Initialize AI Code Generator with direct OpenAI
        
        Args:
            llm_provider: LLM provider (only openai supported now)
            model_name: Model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        
        # Verify OpenAI API key
        if not os.environ.get("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY required for code generation")
        
        logger.info(f"✅ AI Code Generator initialized with {model_name}")
    
    async def generate_code_for_task(self, task_description: str, 
                                     context: Optional[str] = None) -> Dict:
        """
        Generate code based on task description using direct OpenAI API
        
        Args:
            task_description: Description of the coding task
            context: Optional context about the repository/project
            
        Returns:
            dict with generated code files and descriptions
        """
        try:
            import openai
            
            # Build the prompt
            system_prompt = """You are an expert software engineer AI assistant.
Your role is to generate high-quality, production-ready code based on task descriptions.

CRITICAL RULE: You MUST ALWAYS generate actual code in this EXACT format:

📄 File: path/to/file.ext [NEW/MODIFIED/DELETED]