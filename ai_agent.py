"""
AI Agent Module using Direct OpenAI API
Generates code based on task descriptions

Note: Old SpoonOS implementation moved to spoon_os_client.py for reference
"""

import os
import logging
from typing import Dict, List, Optional
import asyncio

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
        import os
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
```language
complete actual code here
```

For EVERY file, use this format. For deletions, omit the code block:
📄 File: path/to/delete.py [DELETED]

RULES:
- Generate COMPLETE, WORKING code (not stubs or TODOs)
- Include proper imports and dependencies
- Add error handling where appropriate
- Include comments explaining key logic
- Follow best practices and standards
- For MODIFIED files, provide the ENTIRE file with all existing code preserved
- For DELETED files, just mark with [DELETED] tag

DO NOT:
- Just describe what to do without showing code
- Say "thinking completed" or "no action needed"
- Create plans or outlines - generate actual code immediately
"""

            user_prompt = f"""USER REQUEST: {task_description}

"""
            if context:
                user_prompt += f"REPOSITORY CONTEXT:\n{context}\n\n"
            
            user_prompt += """Generate the code NOW using this EXACT format for each file:

📄 File: path/to/file.ext [NEW/MODIFIED/DELETED]
```language
actual complete code here
```

GENERATE THE CODE IMMEDIATELY. Do not describe, just show the code."""

            logger.info("Generating code with direct OpenAI API...")
            
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI response length: {len(response_text)} chars")
            
            # Parse the response directly
            logger.info("Parsing OpenAI response...")
            files = self._parse_agent_response(response_text)
            
            logger.info(f"Total files extracted: {len(files)}")
            for f in files:
                logger.info(f"  - {f['path']}: {len(f.get('content', ''))} chars")
            
            return {
                "success": True,
                "files": files,
                "raw_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Error generating code with OpenAI: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
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
        extracted_code_contents = set()  # Track code content we've already extracted
        
        logger.info("Attempting to parse response text for code blocks...")
        
        # Method 0: Look for changeset format with file markers
        # Pattern: 📄 File: path/to/file.py [NEW/MODIFIED/DELETED]
        # Capture the tag to know if it's a deletion
        
        # First, find ALL file markers with tags (including deletions without code blocks)
        file_marker_pattern = r'📄\s*File:\s*([^\s\[]+(?:\.[a-zA-Z0-9]+)?)\s*\[(NEW|MODIFIED|DELETED)\]'
        file_markers = re.findall(file_marker_pattern, response_str)
        
        # Then for each marker, try to find associated code block (optional)
        changeset_matches = []
        for filepath, tag in file_markers:
            # Look for code block after this file marker
            # Make code block optional (for DELETED files)
            code_pattern = rf'📄\s*File:\s*{re.escape(filepath)}\s*\[{tag}\][\s\S]*?```[\w]*\n(.*?)```'
            code_match = re.search(code_pattern, response_str, re.DOTALL)
            
            if code_match:
                code = code_match.group(1)
            else:
                # No code block found (probably a DELETED file)
                code = ""
            
            changeset_matches.append((filepath, tag, code))
        
        # Method 0b: Also look for SpoonOS format without emoji/tags
        # Pattern: File: path/to/file.py (followed by code block)
        # More flexible pattern to handle various spacing
        spoonos_pattern = r'File:\s*([^\s\n]+\.[a-zA-Z0-9]+)[\s\n]+```[\w]*\n(.*?)```'
        spoonos_matches = re.findall(spoonos_pattern, response_str, re.DOTALL)
        
        # Also try without "File:" prefix - just filename before code block
        # Pattern: filename.ext\n```
        filename_only_pattern = r'(?:^|\n)([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)[\s\n]+```[\w]*\n(.*?)```'
        filename_only_matches = re.findall(filename_only_pattern, response_str, re.DOTALL | re.MULTILINE)
        
        logger.info(f"Searching for changeset format files...")
        logger.info(f"Response length: {len(response_str)} chars")
        logger.info(f"Found {len(file_markers)} file markers with tags")
        logger.info(f"Found {len(changeset_matches)} changeset matches (with emoji, code optional)")
        logger.info(f"Found {len(spoonos_matches)} SpoonOS format matches (File: filename)")
        logger.info(f"Found {len(filename_only_matches)} filename-only matches")
        
        # Normalize matches to include tag info
        # changeset_matches have 3 groups: (filepath, tag, code)
        # other matches have 2 groups: (filepath, code)
        normalized_matches = []
        
        if changeset_matches:
            logger.info(f"=== CHANGESET FORMAT DETECTED (with emoji) ===")
            for filepath, tag, code in changeset_matches:
                normalized_matches.append((filepath, code, tag))
        
        if spoonos_matches:
            logger.info(f"=== SPOONOS FORMAT DETECTED (File: filename) ===")
            for filepath, code in spoonos_matches:
                normalized_matches.append((filepath, code, "NEW"))  # Default to NEW
        
        # Only use filename-only matches if no other format was found
        if not normalized_matches and filename_only_matches:
            logger.info(f"=== FILENAME-ONLY FORMAT DETECTED ===")
            for filepath, code in filename_only_matches:
                normalized_matches.append((filepath, code, "NEW"))  # Default to NEW
        
        if normalized_matches:
            for i, (filepath, code, tag) in enumerate(normalized_matches):
                filepath = filepath.strip()
                code_stripped = code.strip()
                tag = tag.upper()
                
                logger.info(f"Match {i+1}:")
                logger.info(f"  Filepath: '{filepath}'")
                logger.info(f"  Tag: [{tag}]")
                logger.info(f"  Code length: {len(code_stripped)} chars")
                logger.info(f"  Code preview: {code_stripped[:100]}...")
                
                if filepath:
                    file_info = {
                        "path": filepath,
                        "content": code_stripped,
                        "description": f"AI-generated file: {filepath}",
                        "action": tag  # NEW, MODIFIED, or DELETED
                    }
                    
                    if tag == "DELETED":
                        logger.info(f"  🗑️  File marked for DELETION")
                        file_info["content"] = ""  # Empty content for deletions
                    
                    files.append(file_info)
                    # Track this code content so we don't duplicate it
                    if code_stripped:
                        extracted_code_contents.add(code_stripped)
                    logger.info(f"  ✅ Added to files list")
                else:
                    logger.warning(f"  ❌ Skipped (empty filepath)")
            
            # If we found files with explicit filenames, skip other methods to avoid duplicates
            logger.info("Explicit file format found, skipping generic code block extraction")
            # Remove duplicates and return
            seen_paths = set()
            unique_files = []
            for f in files:
                if f['path'] not in seen_paths:
                    seen_paths.add(f['path'])
                    unique_files.append(f)
            logger.info(f"Returning {len(unique_files)} unique files")
            return unique_files
        
        # Method 1: Look for markdown code blocks with file paths
        # Pattern: ```python\n# File: path/to/file.py\ncode...```
        # Only run this if NO changeset format was found
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response_str, re.DOTALL)
        logger.info(f"Found {len(code_blocks)} code blocks")
        
        for i, code in enumerate(code_blocks):
            code_stripped = code.strip()
            if not code_stripped:
                continue
            
            # Skip if we already extracted this code
            if code_stripped in extracted_code_contents:
                continue
                
            # Try to extract filename from comments
            filename_match = re.search(r'#\s*(?:File:|Filename:|Path:)\s*(.+)', code)
            if filename_match:
                filename = filename_match.group(1).strip()
                # Remove the comment line from content
                code_stripped = re.sub(r'#\s*(?:File:|Filename:|Path:)\s*.+\n', '', code_stripped, count=1).strip()
            else:
                # No filename found, use generic name
                filename = f"generated_file_{i+1}.py"
            
            # Don't add duplicate paths
            if not any(f['path'] == filename for f in files):
                files.append({
                    "path": filename,
                    "content": code_stripped,
                    "description": f"Code block {i+1}"
                })
                extracted_code_contents.add(code_stripped)
                logger.info(f"Extracted: {filename} ({len(code_stripped)} chars)")
        
        # Method 2: Look for explicit file mentions with code
        # Pattern: "Here's the code for src/auth.py:" followed by code
        file_patterns = [
            # Match: "Here's the code for src/auth.py:"
            r'(?:Here\'s|Here is|Code for|File)\s+(?:the code for\s+)?([^\s:]+\.[a-zA-Z0-9]+):\s*```[\w]*\n(.*?)```',
            # Match: "`src/auth.py`:"
            r'`([^\s]+\.[a-zA-Z0-9]+)`:\s*```[\w]*\n(.*?)```',
            # Match: "File: src/auth.py" or "Filename: src/auth.py"
            r'(?:File|Filename):\s*([^\s\n]+\.[a-zA-Z0-9]+)[\s\n]+```[\w]*\n(.*?)```',
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, response_str, re.DOTALL | re.IGNORECASE)
            for filename, code in matches:
                filename = filename.strip()
                code_stripped = code.strip()
                
                # Skip if already extracted
                if code_stripped in extracted_code_contents:
                    continue
                    
                if filename and code_stripped:
                    # Don't add duplicate paths
                    if not any(f['path'] == filename for f in files):
                        files.append({
                            "path": filename,
                            "content": code_stripped,
                            "description": f"Extracted from {filename}"
                        })
                        extracted_code_contents.add(code_stripped)
                        logger.info(f"Pattern match: {filename} ({len(code_stripped)} chars)")
        
        # Method 3: Look for JSON structure
        try:
            json_match = re.search(r'\{[\s\S]*"files"[\s\S]*\}', response_str)
            if json_match:
                data = json.loads(json_match.group(0))
                if 'files' in data and isinstance(data['files'], list):
                    for file_data in data['files']:
                        if isinstance(file_data, dict):
                            content = file_data.get('content', '').strip()
                            # Skip if already extracted
                            if content and content not in extracted_code_contents:
                                files.append(file_data)
                                extracted_code_contents.add(content)
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
    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not openai_key:
        logger.warning("OPENAI_API_KEY not found. AI code generation disabled.")
        return None
    
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    
    try:
        return AICodeGenerator(llm_provider="openai", model_name=model)
    except Exception as e:
        logger.error(f"Failed to create AI code generator: {e}")
        return None


# Example usage
if __name__ == "__main__":
    async def test_agent():
        """Test the OpenAI coding agent"""
        if not os.environ.get("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not found. Set it first.")
            return
        
        generator = AICodeGenerator(llm_provider="openai", model_name="gpt-4o")
        
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
                print(f"Content preview: {file['content'][:200]}...")
        else:
            print(f"Error: {result['error']}")
    
    asyncio.run(test_agent())
