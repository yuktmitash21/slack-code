"""
GitHub OAuth Authentication for Slack Bot

Handles per-user GitHub authentication so each user connects their own account
instead of using a shared bot token.
"""

import os
import json
import logging
import secrets
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Storage for user GitHub tokens
USER_DATA_FILE = Path("data/user_github_tokens.json")


class GitHubAuthManager:
    """Manages per-user GitHub OAuth authentication"""
    
    def __init__(self):
        """Initialize the auth manager"""
        self.github_client_id = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
        self.github_client_secret = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
        self.oauth_callback_url = os.environ.get("GITHUB_OAUTH_CALLBACK_URL", "http://localhost:5050/auth/github/callback")
        
        # In-memory state storage (now safe since everything's in one process)
        self.oauth_states = {}
        
        # Ensure data directory exists
        USER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing user tokens
        self.user_tokens = self._load_user_tokens()
    
    def _load_user_tokens(self) -> Dict:
        """Load user tokens from disk"""
        try:
            if USER_DATA_FILE.exists():
                with open(USER_DATA_FILE, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} user GitHub tokens")
                return data
            return {}
        except Exception as e:
            logger.error(f"Error loading user tokens: {e}")
            return {}
    
    def _save_user_tokens(self):
        """Save user tokens to disk"""
        try:
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(self.user_tokens, f, indent=2)
            logger.info(f"Saved {len(self.user_tokens)} user GitHub tokens")
        except Exception as e:
            logger.error(f"Error saving user tokens: {e}")
    
    def is_user_authenticated(self, slack_user_id: str) -> bool:
        """Check if a user has connected their GitHub account"""
        return slack_user_id in self.user_tokens
    
    def get_user_token(self, slack_user_id: str) -> Optional[str]:
        """Get a user's GitHub token"""
        user_data = self.user_tokens.get(slack_user_id)
        if user_data:
            return user_data.get("github_token")
        return None
    
    def get_user_repo(self, slack_user_id: str, channel_id: Optional[str] = None) -> Optional[str]:
        """
        Get a user's GitHub repo for a specific channel
        
        Args:
            slack_user_id: Slack user ID
            channel_id: Optional channel ID. If provided, returns channel-specific repo.
                       Falls back to global default if channel repo not set.
        
        Returns:
            Repository in format "owner/repo" or None
        """
        user_data = self.user_tokens.get(slack_user_id)
        if not user_data:
            return None
        
        # Check for channel-specific repo first
        if channel_id:
            channel_repos = user_data.get("channel_repos", {})
            if channel_id in channel_repos:
                return channel_repos[channel_id]
        
        # Fall back to global default repo
        return user_data.get("github_repo")
    
    def generate_auth_url(self, slack_user_id: str) -> str:
        """
        Generate GitHub OAuth URL for a user to authenticate
        
        Args:
            slack_user_id: Slack user ID
            
        Returns:
            OAuth URL to redirect user to
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        self.oauth_states[state] = slack_user_id
        
        # GitHub OAuth scopes needed
        scopes = "repo,user:email"
        
        # Build OAuth URL
        oauth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.github_client_id}"
            f"&redirect_uri={self.oauth_callback_url}"
            f"&scope={scopes}"
            f"&state={state}"
        )
        
        logger.info(f"Generated OAuth URL for user {slack_user_id} with state {state[:8]}... (total states: {len(self.oauth_states)})")
        return oauth_url
    
    def get_auth_instructions_message(self, slack_user_id: str) -> Dict:
        """
        Get a formatted Slack message with authentication instructions
        
        Args:
            slack_user_id: Slack user ID
            
        Returns:
            Slack blocks for auth message
        """
        auth_url = self.generate_auth_url(slack_user_id)
        
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👋 Hi <@{slack_user_id}>! To use the bot, you need to connect your GitHub account."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🔐 Why do I need to authenticate?*\n\n"
                                "• The bot creates PRs on *your behalf* in *your repositories*\n"
                                "• Your code stays private and secure\n"
                                "• Each team member has their own permissions"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✨ What you'll be able to do:*\n\n"
                                "• 🤖 Generate code with AI\n"
                                "• 📝 Create pull requests\n"
                                "• 🔀 Merge and revert PRs\n"
                                "• 📊 View your activity dashboard"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 Connect GitHub Account",
                                "emoji": True
                            },
                            "style": "primary",
                            "url": auth_url
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "_After authenticating, come back here and mention me again!_"
                        }
                    ]
                }
            ]
        }
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict:
        """
        Handle OAuth callback from GitHub
        
        Args:
            code: OAuth authorization code
            state: State parameter for CSRF protection
            
        Returns:
            dict with success status and user info
        """
        try:
            logger.info(f"Verifying state {state[:8]}... (have {len(self.oauth_states)} states)")
            
            # Verify state
            if state not in self.oauth_states:
                logger.error(f"State not found! Available states: {list(self.oauth_states.keys())[:3]}")
                return {
                    "success": False,
                    "error": "Invalid state parameter"
                }
            
            slack_user_id = self.oauth_states.pop(state)
            logger.info(f"State verified! User: {slack_user_id}")
            
            # Exchange code for access token
            import requests
            
            token_response = requests.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.github_client_id,
                    "client_secret": self.github_client_secret,
                    "code": code,
                    "redirect_uri": self.oauth_callback_url
                }
            )
            
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                return {
                    "success": False,
                    "error": f"Failed to get access token: {token_data.get('error_description', 'Unknown error')}"
                }
            
            access_token = token_data["access_token"]
            
            # Get user info from GitHub
            user_response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            
            user_data = user_response.json()
            github_username = user_data.get("login")
            
            # Store user token
            self.user_tokens[slack_user_id] = {
                "github_token": access_token,
                "github_username": github_username,
                "github_repo": None,  # Global default repo (optional)
                "channel_repos": {},  # Per-channel repos: {channel_id: repo}
                "authenticated_at": datetime.now().isoformat()
            }
            
            self._save_user_tokens()
            
            logger.info(f"User {slack_user_id} authenticated as GitHub user {github_username}")
            
            return {
                "success": True,
                "slack_user_id": slack_user_id,
                "github_username": github_username
            }
            
        except Exception as e:
            logger.error(f"Error in OAuth callback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_repo_access(self, slack_user_id: str, repo: str) -> Dict:
        """
        Validate that a user has access to a GitHub repository
        
        Args:
            slack_user_id: Slack user ID
            repo: Repository in format "owner/repo"
            
        Returns:
            Dict with:
                - success: bool
                - error: str (if failed)
                - repo_info: dict with repo details (if success)
                - permissions: dict with user permissions (if success)
        """
        try:
            from github import Github, GithubException
            
            # Get user's token
            token = self.get_user_token(slack_user_id)
            if not token:
                return {
                    "success": False,
                    "error": "You need to connect your GitHub account first. Use `connect github` to get started."
                }
            
            # Try to access the repository
            g = Github(token)
            
            try:
                github_repo = g.get_repo(repo)
                
                # Get permissions
                permissions = {
                    "admin": github_repo.permissions.admin if github_repo.permissions else False,
                    "push": github_repo.permissions.push if github_repo.permissions else False,
                    "pull": github_repo.permissions.pull if github_repo.permissions else False,
                }
                
                # Check if user has at least push (write) access
                if not permissions.get("push"):
                    return {
                        "success": False,
                        "error": f"You don't have write access to `{repo}`. You need push/write permissions to create PRs.\n\n"
                                f"Your permissions: {'Read only' if permissions.get('pull') else 'No access'}\n\n"
                                f"Ask the repository owner to add you as a collaborator with write access."
                    }
                
                # Success - user has write access
                repo_info = {
                    "full_name": github_repo.full_name,
                    "name": github_repo.name,
                    "owner": github_repo.owner.login,
                    "private": github_repo.private,
                    "default_branch": github_repo.default_branch,
                    "url": github_repo.html_url,
                    "description": github_repo.description or "No description",
                }
                
                logger.info(f"User {slack_user_id} validated access to {repo}: permissions={permissions}")
                
                return {
                    "success": True,
                    "repo_info": repo_info,
                    "permissions": permissions
                }
                
            except GithubException as e:
                if e.status == 404:
                    return {
                        "success": False,
                        "error": f"Repository `{repo}` not found.\n\n"
                                f"Please check:\n"
                                f"• The repository name is correct (format: `owner/repository`)\n"
                                f"• The repository exists\n"
                                f"• You have access to it (if it's private)"
                    }
                elif e.status == 401:
                    return {
                        "success": False,
                        "error": "Your GitHub token has expired or is invalid. Please reconnect with `connect github`."
                    }
                elif e.status == 403:
                    return {
                        "success": False,
                        "error": f"Access forbidden to `{repo}`. This could be due to:\n"
                                f"• Repository access restrictions\n"
                                f"• Rate limiting\n"
                                f"• Organization policies\n\n"
                                f"Try again in a few minutes or contact the repository owner."
                    }
                else:
                    return {
                        "success": False,
                        "error": f"GitHub API error: {e.data.get('message', str(e))}"
                    }
                    
        except ImportError:
            logger.error("PyGithub not installed")
            return {
                "success": False,
                "error": "GitHub library not available. Please contact the bot administrator."
            }
        except Exception as e:
            logger.error(f"Error validating repo access: {e}")
            return {
                "success": False,
                "error": f"Error checking repository: {str(e)}"
            }
    
    def set_user_repo(self, slack_user_id: str, repo: str, channel_id: Optional[str] = None):
        """
        Set a user's GitHub repository for a specific channel
        
        Args:
            slack_user_id: Slack user ID
            repo: Repository in format "owner/repo"
            channel_id: Optional channel ID. If provided, sets channel-specific repo.
                       Otherwise sets global default.
        """
        if slack_user_id in self.user_tokens:
            # Initialize channel_repos if it doesn't exist (backward compatibility)
            if "channel_repos" not in self.user_tokens[slack_user_id]:
                self.user_tokens[slack_user_id]["channel_repos"] = {}
            
            if channel_id:
                # Set channel-specific repo
                self.user_tokens[slack_user_id]["channel_repos"][channel_id] = repo
                logger.info(f"Set repo for user {slack_user_id} in channel {channel_id}: {repo}")
            else:
                # Set global default repo
                self.user_tokens[slack_user_id]["github_repo"] = repo
                logger.info(f"Set global default repo for user {slack_user_id}: {repo}")
            
            self._save_user_tokens()
    
    def disconnect_user(self, slack_user_id: str):
        """Disconnect a user's GitHub account"""
        if slack_user_id in self.user_tokens:
            github_username = self.user_tokens[slack_user_id].get("github_username")
            del self.user_tokens[slack_user_id]
            self._save_user_tokens()
            logger.info(f"Disconnected user {slack_user_id} (GitHub: {github_username})")
            return True
        return False
    
    def get_user_info(self, slack_user_id: str) -> Optional[Dict]:
        """Get user's GitHub connection info"""
        return self.user_tokens.get(slack_user_id)


# Global auth manager instance
auth_manager = GitHubAuthManager()

