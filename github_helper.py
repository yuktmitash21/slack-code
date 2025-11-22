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
        Make changes using AI or fallback to random changes
        
        Args:
            branch_name: Name of the branch to commit to
            task_description: Task description from Slack
            
        Returns:
            dict with change details
        """
        try:
            # Try AI-generated code first
            if self.use_ai and self.ai_generator:
                logger.info("Attempting AI code generation...")
                try:
                    result = self._create_ai_generated_code(branch_name, task_description)
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
    
    def _create_ai_generated_code(self, branch_name, task_description):
        """
        Create code using AI agent
        
        Args:
            branch_name: Name of the branch to commit to
            task_description: Task description from Slack
            
        Returns:
            dict with change details
        """
        try:
            # Get repository context
            repo_context = f"Repository: {self.repo_name}\nLanguage: Python\nBranch: {branch_name}"
            
            # Generate code using AI
            logger.info(f"Generating code with AI for: {task_description}")
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
            files_created = []
            for file_info in result["files"]:
                file_path = file_info["path"]
                file_content = file_info["content"]
                file_desc = file_info.get("description", "AI-generated code")
                
                try:
                    # Check if file exists
                    try:
                        existing_file = self.repo.get_contents(file_path, ref=branch_name)
                        # Update existing file
                        self.repo.update_file(
                            path=file_path,
                            message=f"🤖 Update {file_path}: {task_description[:50]}",
                            content=file_content,
                            sha=existing_file.sha,
                            branch=branch_name
                        )
                        files_created.append(f"Updated {file_path}")
                    except:
                        # Create new file
                        self.repo.create_file(
                            path=file_path,
                            message=f"🤖 Create {file_path}: {task_description[:50]}",
                            content=file_content,
                            branch=branch_name
                        )
                        files_created.append(f"Created {file_path}")
                    
                    logger.info(f"Successfully created/updated {file_path}")
                except Exception as e:
                    logger.error(f"Failed to create {file_path}: {e}")
                    continue
            
            if files_created:
                return {
                    "success": True,
                    "changes": f"AI-generated code: {', '.join(files_created)}"
                }
            else:
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
                    # Manually commit
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

