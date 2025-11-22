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

You have access to the FULL CODEBASE in your context. Use this to:
- Understand the existing code structure and patterns
- Maintain consistency with the current codebase style
- Properly integrate with existing modules and dependencies
- Avoid conflicts with existing code
- Reuse and extend existing utilities

When given a coding task, you should:
1. Review the existing codebase context provided
2. Understand how your changes fit into the overall architecture
3. Generate appropriate code files with proper structure
4. Follow the existing code style and best practices
5. Include necessary imports (based on what exists in the codebase)
6. Add proper error handling and documentation
7. Make your code integrate seamlessly with existing code

Always use the generate_code tool to create code files with:
- Appropriate file paths that match the repository structure
- Complete, functional code
- Imports that match the existing codebase conventions
- Inline comments explaining key logic
- Proper formatting and indentation consistent with the codebase

When modifying existing files:
- Preserve existing functionality unless explicitly asked to change it
- Maintain the same coding style
- Keep existing imports and add new ones as needed

Be specific and practical. Generate actual implementation code, not just stubs.
Propose concrete changes as diffs/changesets that can be directly applied.
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
    """High-level interface for AI code generation using SpoonOS or direct OpenAI"""
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
        """
        Initialize AI Code Generator with SpoonOS or fallback to direct OpenAI
        
        Args:
            llm_provider: LLM provider (openai, anthropic, gemini, deepseek, openrouter)
            model_name: Model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.agent = None
        self.use_direct_openai = False
        
        if not SPOONOS_AVAILABLE:
            logger.warning("SpoonOS not available. Trying direct OpenAI fallback...")
            self.use_direct_openai = True
            return
        
        try:
            self.agent = CodingAgent(llm_provider, model_name)
            logger.info(f"✅ AI Coding Agent initialized with SpoonOS using {llm_provider}/{model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize SpoonOS agent: {e}")
            logger.warning("Falling back to direct OpenAI...")
            self.agent = None
            self.use_direct_openai = True
    
    async def generate_code_for_task(self, task_description: str, 
                                     context: Optional[str] = None) -> Dict:
        """
        Generate code based on task description using SpoonOS or direct OpenAI
        
        Args:
            task_description: Description of the coding task
            context: Optional context about the repository/project
            
        Returns:
            dict with generated code files and descriptions
        """
        # Try direct OpenAI if SpoonOS failed
        if self.use_direct_openai:
            return await self._generate_with_direct_openai(task_description, context)
        
        if not self.agent:
            return {
                "success": False,
                "error": "No AI agent available",
                "files": []
            }
        
        try:
            # Build the prompt for SpoonOS agent
            prompt = f"""Task: {task_description}

"""
            if context:
                prompt += f"""
=== FULL CODEBASE CONTEXT ===
You have access to the complete repository. Review the files below to understand the codebase structure, existing patterns, and conventions.

{context}

=== END CODEBASE CONTEXT ===

"""
            
            prompt += """
Based on the task and the full codebase context above:

1. Review the existing code structure and identify where your changes fit
2. For EXISTING files: Include ALL existing code plus your modifications
3. For NEW files: Create complete new files
4. Maintain consistency with existing code style, imports, and patterns
5. Propose concrete code changes as a CHANGESET

CRITICAL: Output your response as a CHANGESET showing EXACTLY what will be created/modified.

Use this EXACT format for EVERY response:

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **CHANGESET SUMMARY**
Brief description of what this changeset does

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 **File: exact/path/to/file.py** [NEW] or [MODIFIED]

```python
# If [MODIFIED]: Include THE COMPLETE FILE with ALL existing code + your changes
# If [NEW]: Complete new file

# Example for [MODIFIED] file:
# Keep all existing imports
import existing_module
import new_module  # <-- Your addition

# Keep all existing classes/functions
def existing_function():
    pass

# Your new additions
def new_function():  # <-- Your addition
    return "new feature"

# Keep all existing code at the end
class ExistingClass:
    pass
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 **File: exact/path/to/another_file.py** [NEW]

```python
# Complete new file
class NewClass:
    def __init__(self):
        pass
```

━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES FOR [MODIFIED] FILES:
1. Output the COMPLETE file content
2. Include ALL existing code (imports, classes, functions, variables)
3. Add your modifications/additions in the appropriate places
4. Mark your additions with comments like # <-- Added for [task]
5. Preserve all existing functionality unless explicitly asked to change it
6. The output will REPLACE the entire file, so INCLUDE EVERYTHING

CRITICAL RULES FOR [NEW] FILES:
1. Complete, functional code with all necessary imports
2. Follow repository conventions and patterns
3. Integrate properly with existing codebase

NEVER ask clarifying questions. ALWAYS propose concrete code immediately.
If you must make assumptions, state them in ONE line, then show the code.
"""
            
            # Run the SpoonOS agent
            logger.info("Running SpoonOS agent to generate code...")
            response = await self.agent.run(prompt)
            
            logger.info(f"SpoonOS agent response type: {type(response)}")
            logger.info(f"SpoonOS agent response: {str(response)[:500]}...")
            
            # Extract tool calls from agent's execution history
            files = []
            
            # SpoonOS stores tool execution in different places, try all of them
            logger.info("Inspecting agent attributes...")
            logger.info(f"Agent type: {type(self.agent)}")
            logger.info(f"Agent dir: {[attr for attr in dir(self.agent) if not attr.startswith('_')]}")
            
            # Method 1: Check messages attribute (OpenAI format)
            if hasattr(self.agent, 'messages') and self.agent.messages:
                logger.info(f"Agent.messages: {len(self.agent.messages)} messages")
                for i, msg in enumerate(self.agent.messages):
                    logger.info(f"Message {i}: type={type(msg)}, has tool_calls={hasattr(msg, 'tool_calls')}")
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            logger.info(f"Tool call: {tc.function.name}")
                            if tc.function.name == 'generate_code':
                                import json
                                args = json.loads(tc.function.arguments)
                                files.append({
                                    "path": args.get('file_path'),
                                    "content": args.get('code_content'),
                                    "description": args.get('description')
                                })
            
            # Method 2: Check llm attribute and its messages
            if not files and hasattr(self.agent, 'llm') and hasattr(self.agent.llm, 'messages'):
                logger.info(f"Agent.llm.messages: {len(self.agent.llm.messages)} messages")
                for msg in self.agent.llm.messages:
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
            
            # Method 3: Check available_tools executions
            if not files and hasattr(self.agent, 'available_tools'):
                logger.info(f"Checking available_tools...")
                if hasattr(self.agent.available_tools, 'execution_history'):
                    logger.info(f"Found execution_history")
                    for execution in self.agent.available_tools.execution_history:
                        logger.info(f"Execution: {execution}")
            
            # Method 4: Parse the text response
            if not files:
                logger.warning("Could not extract tool calls from agent history")
                logger.info("Parsing text response...")
                files = self._parse_agent_response(str(response))
            
            logger.info(f"Total files extracted: {len(files)}")
            for f in files:
                logger.info(f"  - {f['path']}: {len(f.get('content', ''))} chars")
            
            return {
                "success": True,
                "files": files,
                "raw_response": response
            }
            
        except Exception as e:
            logger.error(f"Error generating code with SpoonOS: {e}")
            return {
                "success": False,
                "error": str(e),
                "files": []
            }
    
    async def _generate_with_direct_openai(self, task_description: str, 
                                           context: Optional[str] = None) -> Dict:
        """
        Generate code using OpenAI directly (fallback when SpoonOS fails)
        
        Args:
            task_description: Description of the coding task
            context: Optional context about the repository/project
            
        Returns:
            dict with generated code files and descriptions
        """
        try:
            import openai
            import os
            
            logger.info("Using direct OpenAI fallback (SpoonOS unavailable)")
            
            # Build the prompt
            prompt = f"""Task: {task_description}

"""
            if context:
                prompt += f"""
=== FULL CODEBASE CONTEXT ===
{context}
=== END CODEBASE CONTEXT ===

"""
            
            prompt += """
Based on the task and codebase context, generate the necessary code files.

Use this EXACT format:

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
Brief description

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: exact/path/to/file.py [NEW] or [MODIFIED]

```python
# Complete working code
def example():
    return "real code"
```

For [MODIFIED] files: Include ALL existing code plus your changes.
For [NEW] files: Complete new file.

Generate complete, working code with proper imports and error handling.
"""
            
            # Call OpenAI directly
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer. Generate complete, production-ready code based on requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content
            
            logger.info(f"Direct OpenAI response received: {len(response_text)} chars")
            
            # Parse the response
            files = self._parse_agent_response(response_text)
            
            return {
                "success": True,
                "files": files,
                "raw_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Error with direct OpenAI: {e}")
            return {
                "success": False,
                "error": f"Direct OpenAI failed: {str(e)}",
                "files": []
            }
    
    def _parse_agent_response(self, response: str) -> List[Dict]:
        """
        Parse SpoonOS agent response to extract generated files
        
        Args:
            response: Raw agent response
            
        Returns:
            List of file dictionaries with path and content
        """
        import re
        import json
        
        files = []
        response_str = str(response)
        
        logger.info("Attempting to parse response text for code blocks...")
        
        # Method 1: Look for markdown code blocks with file paths
        # Pattern: ```python\n# File: path/to/file.py\ncode...```
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response_str, re.DOTALL)
        logger.info(f"Found {len(code_blocks)} code blocks")
        
        for i, code in enumerate(code_blocks):
            if code.strip():
                # Try to extract filename from comments
                filename_match = re.search(r'#\s*(?:File:|Filename:|Path:)\s*(.+)', code)
                if filename_match:
                    filename = filename_match.group(1).strip()
                    # Remove the comment line from content
                    code = re.sub(r'#\s*(?:File:|Filename:|Path:)\s*.+\n', '', code, count=1)
                else:
                    filename = f"generated_file_{i+1}.py"
                
                files.append({
                    "path": filename,
                    "content": code.strip(),
                    "description": f"Code block {i+1}"
                })
                logger.info(f"Extracted: {filename} ({len(code)} chars)")
        
        # Method 2: Look for explicit file mentions with code
        # Pattern: "Here's the code for src/auth.py:" followed by code
        file_patterns = [
            r'(?:Here\'s|Here is|Code for|File)\s+(?:the code for\s+)?([^\s:]+\.(?:py|js|ts|java|go|rs)):\s*```[\w]*\n(.*?)```',
            r'`([^\s]+\.(?:py|js|ts|java|go|rs))`:\s*```[\w]*\n(.*?)```',
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, response_str, re.DOTALL | re.IGNORECASE)
            for filename, code in matches:
                if filename and code.strip():
                    files.append({
                        "path": filename,
                        "content": code.strip(),
                        "description": f"Extracted from {filename}"
                    })
                    logger.info(f"Pattern match: {filename} ({len(code)} chars)")
        
        # Method 3: Look for JSON structure
        try:
            json_match = re.search(r'\{[\s\S]*"files"[\s\S]*\}', response_str)
            if json_match:
                data = json.loads(json_match.group(0))
                if 'files' in data and isinstance(data['files'], list):
                    for file_data in data['files']:
                        if isinstance(file_data, dict):
                            files.append(file_data)
                            logger.info(f"JSON extracted: {file_data.get('path', 'unknown')}")
        except Exception as e:
            logger.debug(f"JSON parsing failed: {e}")
        
        # Remove duplicates (same path)
        seen_paths = set()
        unique_files = []
        for f in files:
            if f['path'] not in seen_paths:
                seen_paths.add(f['path'])
                unique_files.append(f)
        
        # Ultimate fallback - only if nothing else worked
        if not unique_files and response_str and len(response_str) > 50:
            logger.warning("No files extracted, using fallback")
            unique_files.append({
                "path": "ai_generated_code.py",
                "content": f"# Generated by SpoonOS AI Agent\n\n{response_str}",
                "description": "AI-generated code using SpoonOS (fallback)"
            })
        
        logger.info(f"Final file count after deduplication: {len(unique_files)}")
        return unique_files
    
    def generate_code_sync(self, task_description: str, 
                          context: Optional[str] = None) -> Dict:
        """
        Synchronous wrapper for generate_code_for_task
        
        Args:
            task_description: Description of the coding task
            context: Optional context about the repository/project
            
        Returns:
            dict with generated code files and descriptions
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_code_for_task(task_description, context)
        )


def get_ai_code_generator() -> Optional[AICodeGenerator]:
    """
    Get AI code generator instance with configuration from environment
    
    Returns:
        AICodeGenerator instance or None if not configured
    """
    if not SPOONOS_AVAILABLE:
        logger.warning("SpoonOS not available. AI code generation disabled.")
        return None
    
    # Check for LLM API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        logger.info("No LLM API key found. AI code generation disabled.")
        return None
    
    # Determine provider based on SpoonOS supported providers
    if openai_key:
        provider = "openai"
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    elif anthropic_key:
        provider = "anthropic"
        model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    else:
        return None
    
    try:
        return AICodeGenerator(llm_provider=provider, model_name=model)
    except Exception as e:
        logger.error(f"Failed to create AI code generator: {e}")
        return None


# Example usage
if __name__ == "__main__":
    async def test_agent():
        """Test the SpoonOS coding agent"""
        if not SPOONOS_AVAILABLE:
            print("❌ SpoonOS not available. Install it first.")
            return
        
        generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")
        
        if not generator.agent:
            print("❌ Failed to initialize agent")
            return
        
        result = await generator.generate_code_for_task(
            task_description="Create a Python function to validate email addresses using regex",
            context="This is a utility module for a web application"
        )
        
        print("Generation result:")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Generated {len(result['files'])} file(s)")
            for file in result['files']:
                print(f"\nFile: {file['path']}")
                print(f"Description: {file['description']}")
                print(f"Content preview: {file['content'][:200]}...")
        else:
            print(f"Error: {result['error']}")
    
    asyncio.run(test_agent())
