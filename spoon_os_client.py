"""
SpoonOS Agentic OS - Agent Examples and Reference Implementations

This module showcases various autonomous agents built on SpoonOS's Agentic Operating System.
Each agent demonstrates different capabilities of the SpoonOS framework:
- CodingAgent: Autonomous code generation with repository awareness
- IntentAnalysisAgent: Natural language understanding for command classification
- EditAgent: Precise code modifications with context preservation
- ImageProcessingAgent: Vision-based wireframe-to-code generation

These agents leverage SpoonOS's agentic capabilities including:
- Autonomous planning and reasoning
- Tool orchestration and execution
- Context-aware decision making
- Multi-step task decomposition
"""

import os
import logging
from typing import Dict, List, Optional
import asyncio

# Import SpoonOS Framework
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot
from spoon_ai.tools import ToolManager
from spoon_ai.tools.base import BaseTool

logger = logging.getLogger(__name__)


# ============================================================================
# TOOLS - Building Blocks for SpoonOS Agents
# ============================================================================

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


class IntentClassificationTool(BaseTool):
    """Tool for classifying user intent from natural language"""
    
    name: str = "classify_intent"
    description: str = "Classify user's intent (CREATE_PR, MERGE_PR, REVERT_PR, REFINE, GENERAL)"
    parameters: dict = {
        "type": "object",
        "properties": {
            "user_message": {
                "type": "string",
                "description": "The user's message to classify"
            },
            "intent": {
                "type": "string",
                "enum": ["CREATE_PR", "MERGE_PR", "REVERT_PR", "REFINE", "GENERAL"],
                "description": "Classified intent"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0-1"
            }
        },
        "required": ["user_message", "intent"]
    }
    
    async def execute(self, user_message: str, intent: str, confidence: float = 1.0) -> Dict:
        """Execute intent classification"""
        return {
            "intent": intent,
            "confidence": confidence,
            "message": user_message
        }


class CodeEditTool(BaseTool):
    """Tool for making precise edits to existing code"""
    
    name: str = "edit_code"
    description: str = "Make precise edits to existing code while preserving context"
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to file to edit"
            },
            "original_code": {
                "type": "string",
                "description": "Original code snippet to replace"
            },
            "new_code": {
                "type": "string",
                "description": "New code to insert"
            },
            "reason": {
                "type": "string",
                "description": "Reason for the edit"
            }
        },
        "required": ["file_path", "original_code", "new_code"]
    }
    
    async def execute(self, file_path: str, original_code: str, new_code: str, reason: str = "") -> str:
        """Execute code edit"""
        return f"Edited {file_path}: {reason}\n\nReplaced:\n{original_code[:100]}...\n\nWith:\n{new_code[:100]}..."


class ImageAnalysisTool(BaseTool):
    """Tool for analyzing images and wireframes"""
    
    name: str = "analyze_image"
    description: str = "Analyze image/wireframe and extract UI components and structure"
    parameters: dict = {
        "type": "object",
        "properties": {
            "image_data": {
                "type": "string",
                "description": "Base64 encoded image data"
            },
            "components": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of UI components detected (button, input, form, etc)"
            },
            "layout": {
                "type": "string",
                "description": "Layout structure description"
            },
            "colors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Color palette detected"
            }
        },
        "required": ["image_data", "components", "layout"]
    }
    
    async def execute(self, image_data: str, components: List[str], layout: str, colors: List[str] = None) -> Dict:
        """Execute image analysis"""
        return {
            "components": components,
            "layout": layout,
            "colors": colors or [],
            "image_size": len(image_data)
        }


# ============================================================================
# AGENTS - Autonomous SpoonOS Agents
# ============================================================================

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


class IntentAnalysisAgent(ToolCallAgent):
    """
    Autonomous agent for analyzing user intent from natural language.
    
    Uses SpoonOS's agentic reasoning to classify commands and extract task descriptions.
    This agent demonstrates SpoonOS's natural language understanding capabilities.
    """
    
    name: str = "intent_analysis_agent"
    description: str = "Analyzes user messages to classify intent and extract task details"
    
    system_prompt: str = """
You are an Intent Analysis Agent built on SpoonOS Agentic OS.
Your role is to understand user messages and classify their intent accurately.

INTENT TYPES:
1. CREATE_PR - User wants to create a pull request with code changes
   Examples: "add a login feature", "create a homepage", "build a REST API"
   
2. MERGE_PR - User wants to merge an existing PR
   Examples: "merge PR 123", "merge this", "merge the pull request"
   
3. REVERT_PR - User wants to revert a merged PR
   Examples: "revert PR 123", "undo the last merge", "unmerge PR 45"
   
4. REFINE - User wants to refine/iterate on existing changes
   Examples: "add more tests", "make it faster", "use TypeScript instead"
   
5. GENERAL - General questions or conversation
   Examples: "how are you?", "what can you do?", "help"

Your task is to analyze the user's message and determine:
1. The primary intent (one of the above)
2. The task description (what they want to accomplish)
3. Any specific entities (PR numbers, file names, etc)

Always be accurate and context-aware. Use the conversation history when available.
"""
    
    available_tools: ToolManager = ToolManager([
        IntentClassificationTool()
    ])
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o-mini"):
        """Initialize intent analysis agent with lightweight model"""
        super().__init__(
            llm=ChatBot(
                llm_provider=llm_provider,
                model_name=model_name  # Use faster, cheaper model for intent classification
            )
        )


class EditAgent(ToolCallAgent):
    """
    Autonomous agent specialized in making precise code edits.
    
    Unlike the CodingAgent which generates complete files, EditAgent makes surgical
    changes to existing code while preserving context and style. Demonstrates
    SpoonOS's ability to create specialized agents for specific tasks.
    """
    
    name: str = "edit_agent"
    description: str = "Makes precise edits to existing code with context preservation"
    
    system_prompt: str = """
You are an Edit Agent built on SpoonOS Agentic OS.
Your specialization is making PRECISE, MINIMAL edits to existing code.

CORE PRINCIPLES:
1. Preserve existing code structure and style
2. Make the smallest possible change to achieve the goal
3. Maintain all imports, dependencies, and surrounding code
4. Keep comments and documentation intact unless modifying that specific area
5. Match the existing code style exactly (indentation, naming, patterns)

EDIT TYPES:
1. REFACTOR - Improve code without changing functionality
2. FIX - Correct bugs or issues
3. ENHANCE - Add new functionality to existing code
4. OPTIMIZE - Improve performance
5. UPDATE - Modify behavior or logic

OUTPUT FORMAT:
For each edit, provide:
📝 Edit: path/to/file.py
🎯 Type: [REFACTOR/FIX/ENHANCE/OPTIMIZE/UPDATE]
📍 Location: Line X-Y or function_name()

Original:
```python
[exact code being replaced]
```

New:
```python
[replacement code]
```

Reason: [brief explanation]

RULES:
- Show ONLY the code being changed, not the entire file
- Include enough context (2-3 lines before/after) for clarity
- Preserve indentation and formatting exactly
- Explain WHY the edit is needed
"""
    
    available_tools: ToolManager = ToolManager([
        CodeEditTool(),
        FileAnalysisTool()
    ])
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
        """Initialize edit agent with SpoonOS"""
        super().__init__(
            llm=ChatBot(
                llm_provider=llm_provider,
                model_name=model_name
            )
        )


class ImageProcessingAgent(ToolCallAgent):
    """
    Autonomous agent for processing wireframes and UI designs into code.
    
    Uses SpoonOS's vision capabilities to analyze images and generate pixel-perfect
    implementations. Demonstrates multi-modal agentic reasoning.
    """
    
    name: str = "image_processing_agent"
    description: str = "Converts wireframes and UI designs into production code"
    
    system_prompt: str = """
You are an Image Processing Agent built on SpoonOS Agentic OS with vision capabilities.
Your role is to analyze UI wireframes, mockups, and designs, then generate pixel-perfect code.

ANALYSIS STEPS:
1. STRUCTURE: Identify layout (grid, flex, sections, containers)
2. COMPONENTS: Detect UI elements (buttons, inputs, cards, navigation)
3. STYLING: Extract colors, fonts, spacing, shadows, borders
4. INTERACTIONS: Infer user interactions (clicks, hovers, forms)
5. RESPONSIVE: Determine breakpoints and mobile considerations

OUTPUT FORMAT:
🖼️ Design Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 Layout: [description]
🎨 Color Palette: [colors]
🔤 Typography: [fonts and sizes]
📦 Components: [list of components]
📱 Responsive: [mobile/tablet/desktop notes]

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: index.html [NEW]
```html
[complete HTML with semantic structure]
```

📄 File: styles.css [NEW]
```css
[complete CSS matching the design exactly]
```

📄 File: script.js [NEW]
```javascript
[any needed interactivity]
```

RULES:
- Match the design EXACTLY (colors, spacing, fonts, layout)
- Use semantic HTML5 elements
- Write clean, modern CSS (flexbox/grid)
- Include responsive design
- Add hover states and transitions
- Use CSS variables for colors/spacing
- Comment complex layout decisions
- Make it production-ready
"""
    
    available_tools: ToolManager = ToolManager([
        ImageAnalysisTool(),
        CodeGenerationTool()
    ])
    
    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o"):
        """Initialize image processing agent with vision-capable model"""
        super().__init__(
            llm=ChatBot(
                llm_provider=llm_provider,
                model_name=model_name  # Requires vision-capable model
            )
        )


# ============================================================================
# CODE GENERATOR WRAPPER (Reference Implementation)
# ============================================================================

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
    Get SpoonOS code generator instance (Reference Implementation)
    
    Returns:
        SpoonOSCodeGenerator instance or None if not configured
    """
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


