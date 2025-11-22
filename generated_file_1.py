"""
GitHub Helper Module for Creating Pull Requests
"""

import os
import random
import tempfile
import shutil
from datetime import datetime
from github import Github, GithubException
from git import Repo, GitCommandError
import logging

logger = logging.getLogger(__name__)

# Try to import AI agent
try:
    from ai_agent import get_ai_code_generator
    AI_AGENT_AVAILABLE = True
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

    def create_delete_all_files_pr(self):
        """
        Create a pull request to delete all files in the repository
        
        Returns:
            dict with PR details or error
        """
        try:
            # Generate unique branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"delete-all-files-{timestamp}"
            
            # Get the default branch
            default_branch = self.repo.default_branch
            base_sha = self.repo.get_branch(default_branch).commit.sha
            
            logger.info(f"Creating branch {branch_name} from {default_branch}")
            
            # Create a new branch
            ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            
            # Delete all files in the repository
            contents = self.repo.get_contents("", ref=branch_name)
            deleted_files = []
            
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(self.repo.get_contents(file_content.path, ref=branch_name))
                else:
                    self.repo.delete_file(
                        path=file_content.path,
                        message=f"Delete {file_content.path}",
                        sha=file_content.sha,
                        branch=branch_name
                    )
                    deleted_files.append(file_content.path)
            
            # Create the pull request
            pr_title = "Delete all files in the repository"
            pr_body = f"""## 🗑️ Delete All Files Pull Request

This pull request deletes all files in the repository.

**Files Deleted:**
{', '.join(deleted_files)}

**Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

*Generated automatically by Slack Bot 🚀*
"""
            
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
                "changes": f"Deleted files: {', '.join(deleted_files)}"
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Error creating delete all files PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }