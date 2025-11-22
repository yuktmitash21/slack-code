"""
GitHub Helper Module for Creating Pull Requests
"""

import os
import random
import tempfile
from datetime import datetime
from github import Github, GithubException
from git import Repo
import logging

logger = logging.getLogger(__name__)


class GitHubPRHelper:
    """Helper class for GitHub PR operations"""
    
    def __init__(self, github_token, repo_name):
        """
        Initialize GitHub PR Helper
        
        Args:
            github_token: GitHub Personal Access Token
            repo_name: Repository name in format 'owner/repo'
        """
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.repo = self.github.get_repo(repo_name)
        
    def create_random_pr(self, task_description=""):
        """
        Create a random pull request to the repository
        
        Args:
            task_description: Description of the task from Slack
            
        Returns:
            dict with PR details or error
        """
        try:
            # Generate unique branch name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"bot-task-{timestamp}"
            
            # Get the default branch
            default_branch = self.repo.default_branch
            base_sha = self.repo.get_branch(default_branch).commit.sha
            
            logger.info(f"Creating branch {branch_name} from {default_branch}")
            
            # Create a new branch
            ref = self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_sha
            )
            
            # Make a random change to a file
            change_result = self._make_random_change(branch_name, task_description)
            
            if not change_result["success"]:
                return {
                    "success": False,
                    "error": change_result["error"]
                }
            
            # Create the pull request
            pr_title = f"🤖 Bot Task: {task_description[:50]}" if task_description else f"🤖 Bot Generated PR - {timestamp}"
            pr_body = self._generate_pr_description(task_description, change_result)
            
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
                "changes": change_result["changes"]
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
    
    def _make_random_change(self, branch_name, task_description):
        """
        Make a random change to demonstrate PR functionality
        
        Args:
            branch_name: Name of the branch to commit to
            task_description: Task description from Slack
            
        Returns:
            dict with change details
        """
        try:
            # Different types of random changes we can make
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

