"""
GitHub Helper Module for Creating Pull Requests
"""

import os
import random
import tempfile
import shutil
import hashlib
import re
from datetime import datetime
from github import Github, GithubException
from git import Repo, GitCommandError
import logging

logger = logging.getLogger(__name__)

# Try to import AI agent (SpoonOS)
try:
    from ai_agent import get_ai_code_generator
    AI_AGENT_AVAILABLE = True
    logger.info("Using SpoonOS AI agent for code generation")
except ImportError:
    AI_AGENT_AVAILABLE = False
    logger.info("AI agent not available. Using placeholder code generation.")


class GitHubPRHelper:
    """Helper class for GitHub PR operations"""
    
    def __init__(self, github_token, repo_name, use_ai=True):
        """
        Initialize GitHub PR Helper
        
        Args:
            github_token: GitHub Personal Access Token
            repo_name: Repository name in format 'owner/repo'
            use_ai: Whether to use AI agent for code generation (default: True)
        """
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.repo = self.github.get_repo(repo_name)
        self.use_ai = use_ai and AI_AGENT_AVAILABLE
        
        # Initialize AI agent if available
        self.ai_generator = None
        if self.use_ai:
            try:
                self.ai_generator = get_ai_code_generator()
                if self.ai_generator:
                    logger.info("AI code generation enabled")
                else:
                    logger.info("AI code generation disabled (no API key)")
                    self.use_ai = False
            except Exception as e:
                logger.warning(f"Failed to initialize AI generator: {e}")
                self.use_ai = False
    
    def _get_full_codebase_context(self, branch_name="main", user_prompt=None):
        """
        Fetch codebase context using GitHub API (fast, no cloning)
        Intelligently selects files based on user's prompt
        
        Args:
            branch_name: Branch to read files from (default: main)
            user_prompt: User's request to determine which files to load
            
        Returns:
            String containing relevant file contents
        """
        try:
            logger.info(f"Building smart codebase context from branch: {branch_name}")
            if user_prompt:
                logger.info(f"User prompt: {user_prompt[:100]}...")
            
            # Extract keywords from user prompt for smart file selection
            prompt_keywords = set()
            task_type = "general"
            
            if user_prompt:
                prompt_lower = user_prompt.lower()
                
                # Extract filename mentions (e.g., "auth.py", "user_service")
                import re
                explicit_files = re.findall(r'[\w_/\-]+\.[\w]+', user_prompt)
                for f in explicit_files:
                    prompt_keywords.add(f.lower())
                
                # Extract likely module/component names
                words = re.findall(r'\b[\w_]+\b', prompt_lower)
                for word in words:
                    if len(word) > 3:  # Skip short words
                        prompt_keywords.add(word)
                
                # Determine task type for extension priorities
                if any(kw in prompt_lower for kw in ['test', 'unit test', 'testing', 'pytest', 'jest']):
                    task_type = "testing"
                elif any(kw in prompt_lower for kw in ['ui', 'frontend', 'page', 'component', 'html', 'css', 'react', 'vue']):
                    task_type = "frontend"
                elif any(kw in prompt_lower for kw in ['api', 'endpoint', 'route', 'handler', 'controller']):
                    task_type = "api"
                elif any(kw in prompt_lower for kw in ['database', 'db', 'model', 'schema', 'migration', 'sql']):
                    task_type = "database"
                elif any(kw in prompt_lower for kw in ['auth', 'login', 'authentication', 'authorization', 'user']):
                    task_type = "auth"
                
                logger.info(f"Task type: {task_type}, Keywords: {list(prompt_keywords)[:10]}")
            
            # Build context using GitHub API (much faster than cloning)
            context_parts = [
                f"Repository: {self.repo_name}",
                f"Branch: {branch_name}",
                f"Language: {self.repo.language or 'Multiple'}",
                f"Description: {self.repo.description or 'No description'}",
                ""
            ]
            
            # File extensions to include (prioritized)
            priority_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.rs', '.java'}
            secondary_extensions = {'.cpp', '.c', '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala'}
            config_extensions = {'.json', '.yaml', '.yml', '.toml', '.md', '.txt', '.sh', '.bash'}
            
            # Directories to skip
            skip_dirs = {
                'node_modules', '__pycache__', '.git', 'venv', '.venv',
                'dist', 'build', 'target', '.idea', '.vscode', 'vendor',
                'bin', 'obj', '.next', '.nuxt', 'coverage', 'test', 'tests',
                '__tests__', 'spec', 'docs', '.github'
            }
            
            # Get repository tree using GitHub API (fast!)
            try:
                tree = self.repo.get_git_tree(branch_name, recursive=True)
            except:
                # Fallback to default branch
                tree = self.repo.get_git_tree(self.repo.default_branch, recursive=True)
            
            # Collect and score files based on relevance
            scored_files = []
            
            for item in tree.tree:
                if item.type == "blob":  # It's a file
                    path = item.path
                    path_lower = path.lower()
                    
                    # Skip if in excluded directory or hidden
                    if any(f'/{skip_dir}/' in f'/{path}/' or path.startswith(skip_dir) for skip_dir in skip_dirs):
                        continue
                    if path.startswith('.') and path != '.env.example':
                        continue
                    
                    # Check file size (skip large files)
                    if item.size and item.size > 100 * 1024:  # Skip files > 100KB
                        continue
                    
                    # Calculate relevance score
                    score = 0
                    _, ext = os.path.splitext(path)
                    
                    # Base score by extension relevance
                    if ext in priority_extensions:
                        score += 10
                    elif ext in secondary_extensions:
                        score += 5
                    elif ext in config_extensions:
                        score += 3
                    
                    # Boost score based on task type
                    if task_type == "testing" and ('test' in path_lower or 'spec' in path_lower):
                        score += 20
                    elif task_type == "frontend" and any(x in path_lower for x in ['component', 'page', 'view', 'ui', 'client', 'frontend']):
                        score += 20
                    elif task_type == "api" and any(x in path_lower for x in ['api', 'route', 'handler', 'controller', 'endpoint']):
                        score += 20
                    elif task_type == "database" and any(x in path_lower for x in ['model', 'schema', 'migration', 'database', 'db']):
                        score += 20
                    elif task_type == "auth" and any(x in path_lower for x in ['auth', 'login', 'user', 'session', 'token']):
                        score += 20
                    
                    # Boost score if filename/path contains keywords from prompt
                    if prompt_keywords:
                        path_parts = path_lower.replace('/', ' ').replace('_', ' ').replace('-', ' ').split()
                        matches = sum(1 for keyword in prompt_keywords if keyword in path_parts or keyword in path_lower)
                        score += matches * 15
                    
                    # Always include certain key files
                    if path in ['README.md', 'package.json', 'requirements.txt', 'setup.py']:
                        score += 8
                    
                    # Prefer smaller files (usually more focused)
                    size_penalty = (item.size or 0) // 10000  # -1 per 10KB
                    score -= size_penalty
                    
                    if score > 0:
                        scored_files.append((path, item.size or 0, score))
            
            # Sort by score (highest first), then by size (smaller first)
            scored_files.sort(key=lambda x: (-x[2], x[1]))
            
            # Select only top 2 most relevant files for speed
            files_to_fetch = scored_files[:2]
            
            logger.info(f"Top 2 most relevant files:")
            for path, size, score in files_to_fetch:
                logger.info(f"  {score:3d} | {path} ({size} bytes)")
            
            logger.info(f"Fetching {len(files_to_fetch)} files via GitHub API")
            
            # Fetch actual file contents (only 2 files for speed)
            total_chars = 0
            max_total_chars = 50000  # ~12k tokens (reduced since we only fetch 2 files)
            files_added = 0
            
            for filepath, size, score in files_to_fetch:
                # Stop if we're approaching token limit
                if total_chars > max_total_chars:
                    logger.info(f"Reached token limit, stopping at {files_added} files")
                    break
                
                try:
                    file_content = self.repo.get_contents(filepath, ref=branch_name)
                    content = file_content.decoded_content.decode('utf-8', errors='ignore')
                    
                    # Add to context
                    context_parts.append(f"--- FILE: {filepath} ---")
                    context_parts.append(content)
                    context_parts.append(f"--- END FILE: {filepath} ---")
                    context_parts.append("")
                    
                    total_chars += len(content)
                    files_added += 1
                    
                except Exception as e:
                    logger.debug(f"Could not read {filepath}: {e}")
                    continue
            
            full_context = "\n".join(context_parts)
            
            logger.info(f"Built context: {files_added} files, {total_chars} chars (~{total_chars // 4} tokens)")
            
            return full_context
        
        except Exception as e:
            logger.error(f"Error getting codebase context: {e}")
            return f"Repository: {self.repo_name}\nBranch: {branch_name}\n\nError reading structure: {str(e)}"
        
    def _generate_branch_name(self, task_description, thread_context=None):
        """
        Generate a unique branch name based on thread context and task description
        
        Args:
            task_description: Task description from Slack
            thread_context: Optional thread context (thread_ts or conversation hash)
            
        Returns:
            Unique branch name
        """
        # Extract a meaningful slug from the task description
        def create_slug(text, max_length=30):
            """Create a URL-friendly slug from text"""
            # Remove bot mentions and common words
            text = re.sub(r'<@[A-Z0-9]+>', '', text)
            text = re.sub(r'\b(create|make|open|submit|generate|a|an|the|pr|pull request|for|to)\b', '', text, flags=re.IGNORECASE)
            
            # Convert to lowercase and replace spaces/special chars with hyphens
            slug = re.sub(r'[^\w\s-]', '', text.lower())
            slug = re.sub(r'[-\s]+', '-', slug)
            slug = slug.strip('-')
            
            # Truncate to max_length
            if len(slug) > max_length:
                slug = slug[:max_length].rstrip('-')
            
            # Ensure it's not empty
            if not slug:
                slug = "task"
            
            return slug
        
        # Create slug from task description
        task_slug = create_slug(task_description)
        
        # Create a hash from the full context (task + thread context if available)
        hash_input = task_description
        if thread_context:
            hash_input += str(thread_context)
        
        # Generate a short hash (first 8 characters)
        context_hash = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
        
        # Combine: bot-{slug}-{hash}
        branch_name = f"bot-{task_slug}-{context_hash}"
        
        # Ensure branch name is valid (GitHub has restrictions)
        # Remove any invalid characters
        branch_name = re.sub(r'[^a-z0-9\-_]', '', branch_name.lower())
        # Ensure it doesn't start with a dot or hyphen
        branch_name = branch_name.lstrip('.-')
        # Limit total length (GitHub allows up to 255, but keep it reasonable)
        if len(branch_name) > 100:
            branch_name = branch_name[:100].rstrip('-')
        
        # Check if branch exists and append counter if needed
        counter = 0
        original_branch_name = branch_name
        while counter < 100:  # Safety limit
            try:
                # Try to get the branch - if it exists, this will succeed
                self.repo.get_branch(branch_name)
                # Branch exists, try with counter
                counter += 1
                branch_name = f"{original_branch_name}-{counter}"
            except GithubException:
                # Branch doesn't exist, we can use this name
                break
        
        logger.info(f"Generated branch name: {branch_name} (from task: {task_description[:50]})")
        return branch_name
    
    def create_random_pr(self, task_description="", thread_context=None, codebase_context=None, cached_files=None):
        """
        Create a random pull request to the repository
        
        Args:
            task_description: Description of the task from Slack (can be full conversation history)
            thread_context: Optional thread context (thread_ts) for unique branch naming
            codebase_context: Full codebase context (all files) for AI to understand existing code
            cached_files: Pre-parsed files from preview (avoids second AI call)
            
        Returns:
            dict with PR details or error
        """
        try:
            # Generate unique branch name based on thread context
            branch_name = self._generate_branch_name(task_description, thread_context)
            
            # Get the default branch
            default_branch = self.repo.default_branch
            base_sha = self.repo.get_branch(default_branch).commit.sha
            
            logger.info(f"Creating branch {branch_name} from {default_branch}")
            
            # Create a new branch
            ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            
            # Extract the actual task from conversation history if it's a multi-line conversation
            # Look for the original task description (usually in the first user message)
            actual_task = task_description
            if "\n\n" in task_description or "user:" in task_description.lower():
                # This is a conversation history, extract the task
                lines = task_description.split("\n")
                for line in lines:
                    line_lower = line.lower()
                    if ("user:" in line_lower or "create" in line_lower or "make" in line_lower) and ("pr" in line_lower or "delete" in line_lower or "remove" in line_lower):
                        # Extract the task part
                        if ":" in line:
                            actual_task = line.split(":", 1)[1].strip()
                        else:
                            actual_task = line.strip()
                        break
                # Also search the full text for deletion patterns
                files_to_delete = self._detect_file_deletion(task_description)
                if files_to_delete:
                    # Use the full conversation for context, but prioritize deletion
                    logger.info(f"Found deletion request in conversation: {files_to_delete}")
            
            # Make a random change to a file (use cached files if available)
            change_result = self._make_random_change(branch_name, task_description, codebase_context, cached_files)
            
            if not change_result["success"]:
                return {
                    "success": False,
                    "error": change_result["error"]
                }
            
            # Create the pull request
            # Clean up task description for PR title (remove newlines, limit length)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            clean_task = (task_description[:50].replace('\n', ' ').strip() if task_description else f"Bot Generated PR - {timestamp}")
            pr_title = f"🤖 Bot Task: {clean_task}"
            pr_body = self._generate_pr_description(task_description, change_result)
            
            logger.info(f"Creating PR with title: {pr_title[:100]}")
            logger.info(f"Change result: {change_result}")
            
            try:
                pr = self.repo.create_pull(
                    title=pr_title,
                    body=pr_body,
                    head=branch_name,
                    base=default_branch
                )
                
                logger.info(f"Pull request created: {pr.html_url}")
                
                return {
                    "success": True,
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                    "branch_name": branch_name,
                    "changes": change_result.get("changes", "Changes made")
                }
            except GithubException as pr_error:
                logger.error(f"Failed to create PR: {pr_error}")
                # Return error but note that changes were made
                return {
                    "success": False,
                    "error": f"Changes made but PR creation failed: {pr_error.data.get('message', str(pr_error))}",
                    "branch_name": branch_name,
                    "changes": change_result.get("changes", "Changes made")
                }
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_file_deletion(self, task_description):
        """
        Detect if the task is asking to delete/remove a file
        
        Args:
            task_description: Task description from Slack (may include conversation history)
            
        Returns:
            List of file paths to delete, or empty list
        """
        import re
        files_to_delete = []
        
        # More flexible patterns to detect file deletion requests
        # These patterns are more lenient to handle conversation formats
        deletion_patterns = [
            # Match "delete/remove [the] [file] <filename>"
            r'(?:delete|remove)\s+(?:the\s+)?(?:file\s+)?([a-zA-Z0-9_/.-]+\.(?:py|js|ts|tsx|jsx|java|go|rs|md|txt|json|yaml|yml|xml|html|css|sh|bat|rb|php|cpp|c|h|hpp))',
            # Match "<filename>" in quotes after delete/remove
            r'(?:delete|remove)\s+["\']([a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+)["\']',
            # Match file paths with directory
            r'(?:delete|remove)\s+(?:the\s+)?(?:file\s+)?([a-zA-Z0-9_/-]+/[a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+)',
        ]
        
        # Process each line of the task description (in case it's multi-line conversation)
        lines = task_description.split('\n')
        logger.info(f"🔍 Checking {len(lines)} lines for file deletion patterns")
        
        for line in lines:
            line_lower = line.lower()
            
            # Skip lines that don't contain delete/remove keywords
            if 'delete' not in line_lower and 'remove' not in line_lower:
                continue
            
            logger.info(f"🔍 Found delete/remove keyword in line: {line[:150]}")
            
            for pattern in deletion_patterns:
                matches = re.findall(pattern, line_lower, re.IGNORECASE)
                if matches:
                    logger.info(f"Pattern '{pattern[:50]}...' matched: {matches}")
                for match in matches:
                    file_path = match.strip()
                    # Remove quotes if present
                    file_path = file_path.strip('"\'')
                    # Remove any trailing punctuation
                    file_path = file_path.rstrip('.,;:!?')
                    if file_path and file_path not in files_to_delete:
                        files_to_delete.append(file_path)
                        logger.info(f"✅ Detected file to delete: '{file_path}'")
        
        if not files_to_delete:
            logger.info("ℹ️  No files detected for deletion")
        else:
            logger.info(f"✅ Total files to delete: {files_to_delete}")
        
        return files_to_delete
    
    def _delete_files(self, branch_name, task_description, files_to_delete):
        """
        Delete files from the repository
        
        Args:
            branch_name: Name of the branch
            task_description: Task description
            files_to_delete: List of file paths to delete
            
        Returns:
            dict with deletion result
        """
        logger.info(f"🗑️  Starting file deletion on branch '{branch_name}'")
        logger.info(f"Files to delete: {files_to_delete}")
        
        deleted_files = []
        errors = []
        
        for file_path in files_to_delete:
            try:
                logger.info(f"Attempting to delete: {file_path}")
                # Check if file exists
                try:
                    existing_file = self.repo.get_contents(file_path, ref=branch_name)
                    logger.info(f"File found on branch, SHA: {existing_file.sha}")
                    
                    # Delete the file
                    self.repo.delete_file(
                        path=file_path,
                        message=f"🤖 Delete {file_path}: {task_description[:50]}",
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                    deleted_files.append(file_path)
                    logger.info(f"✅ Successfully deleted {file_path}")
                except GithubException as e:
                    if e.status == 404:
                        logger.warning(f"❌ File {file_path} not found on branch {branch_name}")
                        errors.append(f"{file_path} (not found)")
                    else:
                        logger.error(f"❌ GitHub API error deleting {file_path}: {e}")
                        errors.append(f"{file_path} ({str(e)})")
            except Exception as e:
                logger.error(f"❌ Unexpected error deleting {file_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                errors.append(f"{file_path} ({str(e)})")
        
        if deleted_files:
            return {
                "success": True,
                "changes": f"Deleted files: {', '.join(deleted_files)}" + (f" | Errors: {', '.join(errors)}" if errors else "")
            }
        else:
            return {
                "success": False,
                "error": f"Could not delete files: {', '.join(errors) if errors else ', '.join(files_to_delete)}"
            }
    
    def _make_random_change(self, branch_name, task_description, codebase_context=None, cached_files=None):
        """
        Make changes using AI or fallback to random changes
        
        Args:
            branch_name: Name of the branch to commit to
            task_description: Task description from Slack
            codebase_context: Full codebase context for AI to understand existing code
            cached_files: Pre-parsed files from preview (avoids second AI call)
            
        Returns:
            dict with change details
        """
        try:
            # FIRST: If we have cached files from preview, use them directly!
            if cached_files:
                logger.info(f"✅ Using cached files from preview: {len(cached_files)} file(s)")
                result = self._create_ai_generated_code(
                    branch_name, 
                    task_description, 
                    codebase_context, 
                    cached_files
                )
                if result["success"]:
                    return result
                else:
                    logger.warning(f"Cached files failed: {result.get('error')}, generating fresh")
            
            # SECOND: Check if this is a file deletion request
            files_to_delete = self._detect_file_deletion(task_description)
            
            if files_to_delete:
                logger.info(f"✅ Detected file deletion request: {files_to_delete}")
                logger.info(f"Task description: {task_description[:200]}")
                deletion_result = self._delete_files(branch_name, task_description, files_to_delete)
                logger.info(f"Deletion result: {deletion_result}")
                return deletion_result
            
            # THIRD: Try AI-generated code
            if self.use_ai and self.ai_generator:
                logger.info("Attempting AI code generation...")
                try:
                    result = self._create_ai_generated_code(branch_name, task_description, codebase_context)
                    if result["success"]:
                        return result
                    else:
                        logger.warning(f"AI generation failed: {result.get('error')}, falling back to placeholder")
                except Exception as e:
                    logger.warning(f"AI generation error: {e}, falling back to placeholder")
            
            # Fallback to random placeholder changes
            logger.info("Using placeholder code generation")
            change_options = [
                self._add_comment_to_readme,
                self._create_task_log_file,
                self._update_bot_stats,
            ]
            
            # Pick a random change type
            change_func = random.choice(change_options)
            return change_func(branch_name, task_description)
            
        except Exception as e:
            logger.error(f"Error making change: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_ai_generated_code(self, branch_name, task_description, codebase_context=None, cached_files=None):
        """
        Create code using AI agent or cached files
        
        Args:
            branch_name: Name of the branch to commit to
            task_description: Task description from Slack
            codebase_context: Full codebase context (all files) for AI to understand existing code
            cached_files: Pre-parsed files from preview (skips AI generation)
            
        Returns:
            dict with change details
        """
        try:
            # If we have cached files, use them directly!
            if cached_files:
                logger.info(f"✅ Using {len(cached_files)} cached file(s) from preview - NO AI CALL NEEDED")
                result = {
                    "success": True,
                    "files": cached_files
                }
            else:
                # Build comprehensive context for AI
                if codebase_context:
                    # Use the full codebase context provided
                    repo_context = f"""Repository: {self.repo_name}
Branch: {branch_name}

FULL CODEBASE CONTEXT:
{codebase_context}

IMPORTANT: You have access to ALL existing files above.
- You can MODIFY existing files (provide complete updated content)
- You can CREATE new files
- You can DELETE code from existing files
- Preserve existing functionality unless explicitly told to remove it
"""
                    logger.info(f"Using full codebase context: {len(codebase_context)} characters")
                else:
                    # Fallback to minimal context
                    repo_context = f"Repository: {self.repo_name}\nLanguage: Python\nBranch: {branch_name}"
                    logger.warning("No codebase context provided - AI will have limited visibility")
                
                # Generate code using AI
                logger.info(f"Generating code with AI for: {task_description}")
                logger.info(f"Total context size: {len(repo_context)} characters")
                
                result = self.ai_generator.generate_code_sync(
                    task_description=task_description,
                    context=repo_context
                )
            
            if not result.get("success") or not result.get("files"):
                return {
                    "success": False,
                    "error": result.get("error", "No files generated")
                }
            
            # Create files in the repository
            logger.info(f"Creating {len(result['files'])} file(s) on GitHub")
            
            files_created = []
            for i, file_info in enumerate(result["files"]):
                file_path = file_info["path"]
                file_content = file_info["content"]
                file_desc = file_info.get("description", "AI-generated code")
                file_action = file_info.get("action", "NEW").upper()
                
                # Fix escaped newlines if they exist (\\n -> \n)
                # This handles cases where the AI output has literal \n strings
                if isinstance(file_content, str):
                    # Only replace if we detect escaped newlines
                    if '\\n' in file_content and '\n' not in file_content:
                        file_content = file_content.replace('\\n', '\n')
                        logger.info(f"  Fixed escaped newlines in {file_path}")
                
                logger.info(f"File {i+1}/{len(result['files'])}: {file_path} [{file_action}]")
                logger.info(f"  Content length: {len(file_content)} chars")
                logger.info(f"  Content preview (first 200 chars): {file_content[:200]}")
                
                try:
                    # Handle file deletion
                    if file_action == "DELETED":
                        logger.info(f"  🗑️  Deleting file: {file_path}")
                        try:
                            existing_file = self.repo.get_contents(file_path, ref=branch_name)
                            self.repo.delete_file(
                                path=file_path,
                                message=f"🤖 Delete {file_path}: {task_description[:50]}",
                                sha=existing_file.sha,
                                branch=branch_name
                            )
                            files_created.append(f"Deleted {file_path}")
                            logger.info(f"  ✅ Deleted file: {file_path}")
                        except Exception as e:
                            if "404" in str(e) or "Not Found" in str(e):
                                logger.warning(f"  ⚠️  File not found, skipping: {file_path}")
                            else:
                                raise
                        continue
                    
                    # Handle file creation/update
                    try:
                        existing_file = self.repo.get_contents(file_path, ref=branch_name)
                        
                        # Update existing file with AI-generated content
                        self.repo.update_file(
                            path=file_path,
                            message=f"🤖 Update {file_path}: {task_description[:50]}",
                            content=file_content,
                            sha=existing_file.sha,
                            branch=branch_name
                        )
                        files_created.append(f"Updated {file_path}")
                        logger.info(f"  ✅ Updated existing file: {file_path}")
                    except:
                        # Create new file
                        self.repo.create_file(
                            path=file_path,
                            message=f"🤖 Create {file_path}: {task_description[:50]}",
                            content=file_content,
                            branch=branch_name
                        )
                        files_created.append(f"Created {file_path}")
                        logger.info(f"  ✅ Created new file: {file_path}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to process {file_path}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info(f"File operations complete: {len(files_created)} file(s)")
            
            if files_created:
                return {
                    "success": True,
                    "changes": f"AI-generated code: {', '.join(files_created)}"
                }
            else:
                logger.error("No files were successfully created!")
                return {
                    "success": False,
                    "error": "Failed to create any files"
                }
                
        except Exception as e:
            logger.error(f"Error in AI code generation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _add_comment_to_readme(self, branch_name, task_description):
        """Add a timestamped comment to README"""
        try:
            # Get README file
            readme = self.repo.get_contents("README.md", ref=branch_name)
            
            # Add a comment at the end
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_content = readme.decoded_content.decode('utf-8')
            comment = f"\n\n<!-- Bot task executed: {task_description[:100]} at {timestamp} -->"
            new_content += comment
            
            # Update the file
            self.repo.update_file(
                path="README.md",
                message=f"🤖 Add bot task comment: {task_description[:50]}",
                content=new_content,
                sha=readme.sha,
                branch=branch_name
            )
            
            return {
                "success": True,
                "changes": f"Added comment to README.md"
            }
            
        except Exception as e:
            logger.error(f"Error updating README: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_task_log_file(self, branch_name, task_description):
        """Create a new task log file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"bot_tasks/task_{timestamp}.txt"
            
            content = f"""Bot Task Log
================

Task: {task_description}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: Pending Implementation

Description:
{task_description}

---
This file was automatically generated by the Slack bot.
The actual implementation logic will be added in future iterations.
"""
            
            # Create the file
            self.repo.create_file(
                path=filename,
                message=f"🤖 Create task log: {task_description[:50]}",
                content=content,
                branch=branch_name
            )
            
            return {
                "success": True,
                "changes": f"Created new file: {filename}"
            }
            
        except Exception as e:
            logger.error(f"Error creating task file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_bot_stats(self, branch_name, task_description):
        """Update or create a bot statistics file"""
        try:
            filename = "BOT_STATS.md"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to get existing file
            try:
                stats_file = self.repo.get_contents(filename, ref=branch_name)
                existing_content = stats_file.decoded_content.decode('utf-8')
                
                # Parse task count
                if "Total Tasks:" in existing_content:
                    # Extract current count
                    import re
                    match = re.search(r'Total Tasks: (\d+)', existing_content)
                    count = int(match.group(1)) + 1 if match else 1
                else:
                    count = 1
                
                # Append new task
                new_entry = f"\n- [{timestamp}] {task_description}"
                new_content = existing_content.replace(
                    "## Task History",
                    f"## Task History\n{new_entry}"
                ).replace(
                    f"Total Tasks: {count-1}",
                    f"Total Tasks: {count}"
                )
                
                # Update file
                self.repo.update_file(
                    path=filename,
                    message=f"🤖 Update bot stats: task #{count}",
                    content=new_content,
                    sha=stats_file.sha,
                    branch=branch_name
                )
                
            except GithubException:
                # File doesn't exist, create it
                content = f"""# Bot Statistics

Total Tasks: 1
Last Updated: {timestamp}

## Task History
- [{timestamp}] {task_description}

---
*This file is automatically maintained by the Slack bot.*
"""
                self.repo.create_file(
                    path=filename,
                    message=f"🤖 Create bot stats file",
                    content=content,
                    branch=branch_name
                )
            
            return {
                "success": True,
                "changes": f"Updated bot statistics in {filename}"
            }
            
        except Exception as e:
            logger.error(f"Error updating bot stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_pr_description(self, task_description, change_result):
        """Generate a formatted PR description"""
        description = f"""## 🤖 Automated Pull Request

**Task Description:**
{task_description if task_description else "No specific task provided"}

**Changes Made:**
{change_result.get('changes', 'Various changes')}

**Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

### Note:
This PR was automatically generated by the Slack bot. The actual coding logic for the task will be implemented in future iterations.

Currently, this PR demonstrates the bot's ability to:
- Create branches
- Make commits
- Generate pull requests
- Integrate with GitHub API

**Next Steps:**
- Review the changes
- Merge if acceptable
- The bot will learn to implement actual code changes based on task descriptions

---

*Generated automatically by Slack Bot 🚀*
"""
        return description
    
    def merge_pr(self, pr_number, merge_method="merge"):
        """
        Merge a pull request
        
        Args:
            pr_number: PR number to merge (int or str)
            merge_method: Merge method - "merge", "squash", or "rebase" (default: "merge")
            
        Returns:
            dict with merge result or error
        """
        try:
            pr_number = int(pr_number)
            
            # Get the pull request
            pr = self.repo.get_pull(pr_number)
            
            # Check if PR is already merged
            if pr.merged:
                return {
                    "success": False,
                    "error": f"PR #{pr_number} is already merged"
                }
            
            # Check if PR is closed
            if pr.state == "closed":
                return {
                    "success": False,
                    "error": f"PR #{pr_number} is closed and cannot be merged"
                }
            
            # Check if PR is mergeable
            if pr.mergeable is False:
                return {
                    "success": False,
                    "error": f"PR #{pr_number} has merge conflicts and cannot be merged automatically"
                }
            
            # Get PR details before merging
            pr_title = pr.title
            pr_branch = pr.head.ref
            pr_url = pr.html_url
            
            # Merge the PR
            merge_result = pr.merge(
                commit_title=f"Merge pull request #{pr_number}",
                merge_method=merge_method
            )
            
            logger.info(f"PR #{pr_number} merged successfully: {merge_result.sha}")
            
            return {
                "success": True,
                "pr_number": pr_number,
                "pr_title": pr_title,
                "pr_url": pr_url,
                "branch_name": pr_branch,
                "merge_sha": merge_result.sha,
                "merge_method": merge_method
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error merging PR: {e}")
            error_message = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            return {
                "success": False,
                "error": f"GitHub API error: {error_message}"
            }
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid PR number: {pr_number}"
            }
        except Exception as e:
            logger.error(f"Error merging PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pr_info(self, pr_number):
        """
        Get information about a pull request
        
        Args:
            pr_number: PR number to get info for
            
        Returns:
            dict with PR info or error
        """
        try:
            pr_number = int(pr_number)
            pr = self.repo.get_pull(pr_number)
            
            return {
                "success": True,
                "pr_number": pr_number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "url": pr.html_url,
                "branch": pr.head.ref,
                "base": pr.base.ref,
                "user": pr.user.login,
                "created_at": pr.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "body": pr.body or "No description provided"
            }
            
        except GithubException as e:
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_revert_pr(self, pr_number):
        """
        Create a revert PR for an existing merged PR using actual git revert
        
        Args:
            pr_number: PR number to revert (must be merged)
            
        Returns:
            dict with revert PR details or error
        """
        temp_dir = None
        try:
            pr_number = int(pr_number)
            
            # Get the original pull request
            original_pr = self.repo.get_pull(pr_number)
            
            # Check if PR is merged
            if not original_pr.merged:
                return {
                    "success": False,
                    "error": f"PR #{pr_number} is not merged yet. Only merged PRs can be reverted."
                }
            
            # Get the merge commit
            merge_commit_sha = original_pr.merge_commit_sha
            
            if not merge_commit_sha:
                return {
                    "success": False,
                    "error": f"Could not find merge commit for PR #{pr_number}"
                }
            
            # Get the default branch
            default_branch = self.repo.default_branch
            
            # Create a new branch name for the revert
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            revert_branch_name = f"revert-pr-{pr_number}-{timestamp}"
            
            logger.info(f"Creating revert branch {revert_branch_name} to revert {merge_commit_sha}")
            
            # Clone the repository to a temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Cloning repository to {temp_dir}")
            
            # Clone with authentication
            github_token = self.github._Github__requester.auth.token if hasattr(self.github._Github__requester.auth, 'token') else None
            
            if github_token:
                # Use token authentication in clone URL
                repo_url = f"https://{github_token}@github.com/{self.repo_name}.git"
            else:
                repo_url = f"https://github.com/{self.repo_name}.git"
            
            # Clone the repo
            local_repo = Repo.clone_from(repo_url, temp_dir, branch=default_branch)
            
            # Configure git user for the commit
            with local_repo.config_writer() as git_config:
                git_config.set_value('user', 'email', 'slack-bot@automated.local')
                git_config.set_value('user', 'name', 'Slack Bot')
            
            # Create and checkout the new revert branch
            new_branch = local_repo.create_head(revert_branch_name)
            new_branch.checkout()
            
            logger.info(f"Checked out branch {revert_branch_name}")
            
            # Perform the git revert
            # Use -m 1 to specify the mainline parent (important for merge commits)
            try:
                local_repo.git.revert(merge_commit_sha, m=1, no_edit=True)
                logger.info(f"Successfully reverted commit {merge_commit_sha}")
            except GitCommandError as e:
                logger.error(f"Git revert failed: {e}")
                # Try with a custom commit message
                try:
                    local_repo.git.revert(
                        merge_commit_sha, 
                        m=1, 
                        no_commit=True
                    )
                    
                    # Check if there are any changes to commit
                    status = local_repo.git.status('--porcelain')
                    if not status.strip():
                        # No changes to commit - the revert had no effect
                        logger.warning(f"Revert had no effect - nothing to commit")
                        return {
                            "success": False,
                            "error": f"PR #{pr_number} cannot be reverted - no changes were made. The PR may be empty or already reverted."
                        }
                    
                    # Manually commit the changes
                    local_repo.git.commit(
                        '-m', 
                        f"Revert PR #{pr_number}: {original_pr.title}\n\nThis reverts pull request #{pr_number}."
                    )
                    logger.info(f"Successfully reverted with manual commit")
                except GitCommandError as e2:
                    logger.error(f"Manual revert also failed: {e2}")
                    raise
            
            # Push the branch to GitHub
            logger.info(f"Pushing branch {revert_branch_name} to GitHub")
            origin = local_repo.remote(name='origin')
            origin.push(revert_branch_name)
            
            logger.info(f"Successfully pushed revert branch")
            
            # Create the revert pull request
            revert_pr_title = f"Revert PR #{pr_number}: {original_pr.title}"
            revert_pr_body = f"""## 🔄 Revert Pull Request

This PR reverts the changes from PR #{pr_number} using `git revert`.

### Original PR Details
- **Title:** {original_pr.title}
- **PR #:** {pr_number}
- **URL:** {original_pr.html_url}
- **Merged at:** {original_pr.merged_at.strftime("%Y-%m-%d %H:%M:%S") if original_pr.merged_at else "Unknown"}
- **Merge commit:** `{merge_commit_sha}`

### Reason for Revert
Changes need to be undone as requested via Slack bot.

### What This PR Does
This PR contains a revert commit created with:
```bash
git revert -m 1 {merge_commit_sha}
```

This undoes all changes introduced by PR #{pr_number}.

---

*Generated automatically by Slack Bot 🤖*
"""
            
            revert_pr = self.repo.create_pull(
                title=revert_pr_title,
                body=revert_pr_body,
                head=revert_branch_name,
                base=default_branch
            )
            
            logger.info(f"Revert PR created: {revert_pr.html_url}")
            
            return {
                "success": True,
                "revert_pr_number": revert_pr.number,
                "revert_pr_url": revert_pr.html_url,
                "revert_branch_name": revert_branch_name,
                "original_pr_number": pr_number,
                "original_pr_title": original_pr.title,
                "original_pr_url": original_pr.html_url,
                "merge_commit_reverted": merge_commit_sha
            }
            
        except GitCommandError as e:
            logger.error(f"Git command error: {e}")
            return {
                "success": False,
                "error": f"Git revert failed: {str(e)}"
            }
        except GithubException as e:
            logger.error(f"GitHub API error creating revert PR: {e}")
            error_message = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            return {
                "success": False,
                "error": f"GitHub API error: {error_message}"
            }
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid PR number: {pr_number}"
            }
        except Exception as e:
            logger.error(f"Error creating revert PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")

