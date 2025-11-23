"""
SpoonOS-based AI Agent Module (DEPRECATED - kept for reference)
This was replaced with direct OpenAI API due to timeout and reliability issues.

Original implementation using SpoonOS ToolCallAgent framework.
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
    ToolCallAgent = None
    ChatBot = None
    ToolManager = None
    BaseTool = None

logger = logging.getLogger(__name__)


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
            return f"Repository analysis for {repo_path}"


    class CodingAgent(ToolCallAgent):
        """AI Coding Agent using SpoonOS Framework"""
        
        name: str = "coding_agent"
        description: str = "AI agent that generates code based on task descriptions"
        
        system_prompt: str = """
You are an expert software engineer AI assistant built with SpoonOS framework.
Your role is to generate high-quality, production-ready code based on task descriptions.

CRITICAL RULE: You MUST ALWAYS generate actual code. NEVER just think about the task or say what needs to be done.

OUTPUT FORMAT REQUIRED:
For EVERY file you create or modify, include this in your response:

📄 File: path/to/file.ext [NEW/MODIFIED]
```language
complete actual code here
```

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

RULES:
- ALWAYS output actual code in the format shown above
- DO NOT just say "thinking completed" or "task finished"
- DO NOT describe what to do without showing the code
- Generate COMPLETE, WORKING code (not stubs or TODOs)
- Be specific and practical with actual implementation

Every response MUST contain code blocks with the file marker format shown above.
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


class SpoonOSCodeGenerator:
    """
    SpoonOS-based AI Code Generator (DEPRECATED)
    
    This implementation had issues:
    - Tool selection timeouts (25 seconds)
    - "Thinking completed, no action needed" responses
    - Complexity with ToolCallAgent framework
    
    Replaced with direct OpenAI API for reliability and simplicity.
    """
    
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
    
    async def generate_code_for_task_spoonos(self, task_description: str, 
                                             context: Optional[str] = None) -> Dict:
        """
        Generate code based on task description using SpoonOS ToolCallAgent
        
        ISSUES WITH THIS APPROACH:
        - Tool selection timeout after 25 seconds
        - Agent returns "thinking completed" instead of code
        - Complex tool extraction logic needed
        - Unreliable tool calls
        
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
            prompt = f"""USER REQUEST: {task_description}

YOU MUST GENERATE CODE NOW. This is not a planning phase. This is the execution phase.

MANDATORY OUTPUT FORMAT:

📄 File: path/to/file.ext [NEW/MODIFIED]
```language
actual complete code here
```

Include this for EVERY file you need to create or modify.

DO NOT:
- Say "thinking completed" or "no action needed"
- Describe what needs to be done without showing code
- Create a plan or outline - generate the actual code NOW

"""
            if context:
                prompt += f"\nRepository context:\n{context}\n"
            
            prompt += """
Requirements:
- Generate COMPLETE, WORKING code (not stubs or placeholders)
- Include proper imports and dependencies
- Add error handling where appropriate
- Include comments explaining key logic
- Follow best practices and standards

IMPORTANT: 
- DO NOT just describe what to do - show the actual code!
- DO NOT say "thinking completed" - generate the code!
- ALWAYS output the code in the format above!
"""
            
            # Run the SpoonOS agent
            logger.info("Running SpoonOS agent to generate code...")
            response = await self.agent.run(prompt)
            
            logger.info(f"SpoonOS agent response type: {type(response)}")
            
            # Check if AI is just "thinking" instead of generating code
            response_str = str(response)
            response_lower = response_str.lower()
            
            if ("thinking completed" in response_lower or "no action needed" in response_lower) and "```" not in response_str:
                logger.error("SpoonOS returned thinking message instead of code!")
                logger.error(f"Response was: {response_str}")
                return {
                    "success": False,
                    "error": "AI did not generate code. SpoonOS agent timed out or entered thinking mode.",
                    "files": []
                }
            
            # Extract tool calls from agent's execution history
            # This was complex and unreliable
            files = []
            
            # Try to extract from messages
            if hasattr(self.agent, 'messages') and self.agent.messages:
                for msg in self.agent.messages:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            if tc.function.name == 'generate_code':
                                import json
                                args = json.loads(tc.function.arguments)
                                files.append({
                                    "path": args.get('file_path'),
                                    "content": args.get('code_content'),
                                    "description": args.get('description')
                                })
            
            # Fallback: parse text response
            if not files:
                logger.warning("Could not extract tool calls, parsing text response")
                # Would need to include the full parsing logic here
            
            return {
                "success": True if files else False,
                "files": files,
                "raw_response": response_str
            }
            
        except Exception as e:
            logger.error(f"Error generating code with SpoonOS: {e}")
            return {
                "success": False,
                "error": str(e),
                "files": []
            }
    
    def generate_code_sync(self, task_description: str, 
                          context: Optional[str] = None) -> Dict:
        """
        Synchronous wrapper for SpoonOS code generation
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_code_for_task_spoonos(task_description, context)
        )


def get_spoonos_code_generator() -> Optional[SpoonOSCodeGenerator]:
    """
    Get SpoonOS code generator instance (DEPRECATED)
    
    Returns:
        SpoonOSCodeGenerator instance or None if not configured
    """
    if not SPOONOS_AVAILABLE:
        logger.warning("SpoonOS not available.")
        return None
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("OPENAI_API_KEY not found.")
        return None
    
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    
    try:
        return SpoonOSCodeGenerator(llm_provider="openai", model_name=model)
    except Exception as e:
        logger.error(f"Failed to create SpoonOS code generator: {e}")
        return None


# Notes on why we moved away from SpoonOS:
# 
# 1. TIMEOUTS: Tool selection regularly timed out after 25 seconds
#    Error: "coding_agent LLM tool selection timed out after 25.0s"
#
# 2. THINKING MODE: Agent would enter "thinking" mode instead of generating code
#    Response: "Step 2: Thinking completed. No action needed. Task finished."
#
# 3. COMPLEXITY: ToolCallAgent framework added unnecessary complexity
#    - Custom tools that didn't reliably execute
#    - Complex message/tool call extraction logic
#    - Multiple layers of abstraction
#
# 4. UNRELIABILITY: Even with explicit prompts, agent behavior was unpredictable
#    - Sometimes generated code, sometimes didn't
#    - Tool calls not always captured correctly
#    - Parsing fallbacks needed
#
# Direct OpenAI API is simpler, faster, and more reliable:
# - No tool selection timeouts
# - Immediate code generation
# - Simple request/response pattern
# - Predictable behavior
# - Easier to debug

