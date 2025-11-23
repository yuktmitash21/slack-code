"""
Slack Bot that responds to mentions with full channel context
and can create GitHub pull requests
"""

import os
import logging
import re
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from github_helper import GitHubPRHelper
from intent_classification import is_ready_to_create_pr, classify_command

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Store ongoing conversations for PR creation
# Format: {thread_ts: conversation_data}
pr_conversations = {}


def _generate_changeset_preview(prompt: str, context: str, github_helper) -> dict:
    """
    Generate a changeset preview using direct OpenAI API
    This shows proposed changes to the user before PR creation
    
    Returns both the formatted response AND parsed files for caching
    """
    try:
        logger.info("Generating changeset preview with OpenAI...")
        
        # Use the same AI generator as PR creation
        if not github_helper or not github_helper.use_ai or not github_helper.ai_generator:
            logger.error("SpoonOS AI generator not available")
            return {
                "success": False,
                "error": "AI generator not configured"
            }
        
        full_prompt = f"""{prompt}

CONTEXT:
{context}

Remember: This is a PREVIEW. Show the proposed changes as concrete diffs/changesets.
The user can refine these changes through conversation before creating the PR.
"""
        
        # Generate code using SpoonOS (same as PR creation)
        result = github_helper.ai_generator.generate_code_sync(
            task_description=full_prompt,
            context=context
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Code generation failed")
            }
        
        # Get the raw response and parsed files
        raw_response = result.get("raw_response", "")
        parsed_files = result.get("files", [])
        
        logger.info(f"SpoonOS preview generated: {len(parsed_files)} file(s)")
        
        # Format the response as a changeset for Slack with GitHub-style diff
        if parsed_files:
            formatted_response = "📝 PROPOSED CHANGESET\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for file_info in parsed_files:
                filepath = file_info.get("path", "unknown")
                action = file_info.get("action", "NEW")
                content = file_info.get("content", "")
                
                # Calculate line stats
                lines = content.split('\n') if content else []
                line_count = len(lines)
                
                # Format file header with diff stats
                if action == "DELETED":
                    formatted_response += f"🔴 `{filepath}` *[DELETED]* `-{line_count}`\n\n"
                    formatted_response += f"