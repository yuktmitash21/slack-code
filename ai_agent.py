"""
AI Agent Module using SpoonOS Framework
Generates code based on task descriptions
"""

import os
import logging
from typing import Dict, List, Optional
import asyncio

# Import SpoonOS
try:
    from spoon_ai.agents.toolcall import ToolCallAgent
    from spoon_ai.chat import ChatBot
    from spoon_ai.tools import ToolManager
    from spoon_ai.tools.base import BaseTool
    SPOONOS_AVAILABLE = True
except ImportError as e:
    SPOONOS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"SpoonOS not available: {e}")
    logger.error("Install with: pip install git+https://github.com/XSpoonAi/[correct-repo].git")
    ToolCallAgent = None
    ChatBot = None
    ToolManager = None
    BaseTool = None

logger = logging.getLogger(__name__)

# Setup performance logging
performance_logger = logging.getLogger('performance')
performance_logger.setLevel(logging.INFO)
performance_handler = logging.FileHandler('performance.log')
performance_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
performance_handler.setFormatter(performance_formatter)
performance_logger.addHandler(performance_handler)


if SPOONOS_AVAILABLE:
    class CodeGenerationTool(BaseTool):
        """Tool for generating code files based on task descriptions"""
        
        name: str = "generate_code"
        description: str = "Generate code files based on task description"
        parameters: dict = {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path for the generated file (e.g., 'src/auth.py')"
                },
                "code_content": {
                    "type": "string",
                    "description": "The actual code content to write"
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what the code does"
                }
            },
            "required": ["file_path", "code_content", "description"]
        }
        
        async def execute(self, file_path: str, code_content: str, description: str) -> str:
            """Execute the code generation"""
            performance_logger.info(f"Executing code generation tool for {file_path}")
            return f"Generated {file_path}: {description}\n\nContent preview:\n{code_content[:200]}..."


    class FileAnalysisTool(BaseTool):
        """Tool for analyzing existing repository structure"""
        
        name: str = "analyze_repo"
        description: str = "Analyze repository structure to understand existing code"
        parameters: dict = {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Path to repository to analyze"
                }
            },
            "required": ["repo_path"]
        }
        
        async def execute(self, repo_path: str) -> str:
            """Analyze repository structure"""
            performance_logger.info(f"Analyzing repository {repo_path}")
            return f"Repository analysis for {repo_path}"


    class CodingAgent(ToolCallAgent):
        """AI Coding Agent using SpoonOS Framework"""
        
        name: str = "coding_agent"
        description: str = "AI agent that generates code based on task descriptions"
        
        system_prompt: str = """
You are an expert software engineer AI assistant built with SpoonOS framework.
Your role is to generate high-quality, production-ready code based on task descriptions.

IMPORTANT: You will be provided with the COMPLETE CODEBASE context including all existing files.

When given a coding task, you can:
1. CREATE new files - Generate new code files with proper structure
2. MODIFY existing files - Update existing files by providing the COMPLETE updated file content
   - When modifying, provide the ENTIRE file with all existing code preserved
   - Only change the specific parts mentioned in the task
   - Keep all imports, functions, and features that aren't being modified
3. DELETE files or code:
   - To DELETE ENTIRE FILES: Mark with [DELETED] tag and list EACH file explicitly
   - To DELETE CODE from a file: Provide the complete file with the unwanted code removed
   - When user says "delete all X files", list each one explicitly by name
   - DO NOT create files describing deletions - use proper deletion markers

Best Practices:
- Analyze the existing codebase structure and patterns
- Use consistent naming conventions and coding style
- Add proper imports, error handling, and documentation
- Include inline comments explaining complex logic
- Follow the existing architecture and design patterns

Always use the generate_code tool to create/modify code files with:
- Appropriate file paths matching the existing structure (e.g., src/auth.py, utils/helpers.js)
- Complete, functional code
- Proper formatting and indentation matching the codebase style

Be specific and practical. Generate actual implementation code, not just stubs or placeholders.
"""
        
        available_tools: ToolManager = ToolManager([
            CodeGenerationTool(),
            FileAnalysisTool()
        ])
        
        def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
            """Initialize the coding agent with SpoonOS"""
            super().__init__(
                llm=ChatBot(
                    llm_provider=llm_provider,
                    model_name=model_name
                )
            )


class AICodeGenerator:
    """High-level interface for AI code generation using SpoonOS"""
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
        """
        Initialize AI Code Generator with SpoonOS
        
        Args:
            llm_provider: LLM provider (openai, anthropic, gemini, deepseek, openrouter)
            model_name: Model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.agent = None
        
        if not SPOONOS_AVAILABLE:
            logger.error("SpoonOS not available. AI code generation disabled.")
            logger.error("Install SpoonOS to enable AI features")
            return
        
        try:
            self.agent = CodingAgent(llm_provider, model_name)
            logger.info(f"✅ AI Coding Agent initialized with SpoonOS using {llm_provider}/{model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize SpoonOS agent: {e}")
            self.agent = None
    
    async def generate_code_for_task(self, task_description: str, 
                                     context: Optional[str] = None) -> Dict:
        """
        Generate code based on task description using SpoonOS
        
        Args:
            task_description: Description of the coding task
            context: Optional context about the repository/project
            
        Returns:
            dict with generated code files and descriptions
        """
        if not self.agent:
            return {
                "success": False,
                "error": "SpoonOS agent not available",
                "files": []
            }
        
        try:
            # Build the prompt for SpoonOS agent
            prompt = f"""Task: {task_description}

Please generate the necessary code files for this task.

IMPORTANT: After using the generate_code tool, you MUST output the actual code in your response.
Format your response like this:

File: path/to/file.py