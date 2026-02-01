"""
Slack Bot that responds to mentions with full channel context
and can create GitHub pull requests
"""

import os
import logging
import re
import time
import asyncio
import threading
import json
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables FIRST (before importing modules that need them)
load_dotenv()

from flask import Flask, request
from flask_cors import CORS
from stats_tracker import log_pr_creation, mark_pr_merged
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from github_helper import GitHubPRHelper
from intent_classification import is_ready_to_create_pr, classify_command
from github_oauth import auth_manager

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

# Initialize Flask app for OAuth callbacks and API
flask_app = Flask(__name__)
CORS(flask_app)  # Enable CORS for API access

# Register API endpoints
from api_server import register_api
register_api(flask_app)

# Store ongoing conversations for PR creation
# Format: {thread_ts: conversation_data}
# Persistent storage file path
PR_CONVERSATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "pr_conversations.json")


def _load_pr_conversations() -> dict:
    """Load pr_conversations from persistent storage."""
    try:
        if os.path.exists(PR_CONVERSATIONS_FILE):
            with open(PR_CONVERSATIONS_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"📂 Loaded {len(data)} PR conversations from storage")
                return data
    except Exception as e:
        logger.error(f"Error loading pr_conversations: {e}")
    return {}


def _save_pr_conversations():
    """Save pr_conversations to persistent storage."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(PR_CONVERSATIONS_FILE), exist_ok=True)
        with open(PR_CONVERSATIONS_FILE, "w") as f:
            json.dump(pr_conversations, f, indent=2)
        logger.debug(f"💾 Saved {len(pr_conversations)} PR conversations to storage")
    except Exception as e:
        logger.error(f"Error saving pr_conversations: {e}")


# Load conversations from persistent storage on startup
pr_conversations = _load_pr_conversations()


def _generate_changeset_preview(prompt: str, context: str, github_helper_instance, image_data=None, stream_callback=None) -> dict:
    """
    Generate a changeset preview using direct OpenAI API
    This shows proposed changes to the user before PR creation
    
    Args:
        prompt: The prompt for code generation
        context: Repository context
        github_helper_instance: GitHub helper with AI generator
        image_data: Optional image data for vision models
        stream_callback: Optional callback(current_text, is_complete) for streaming updates
    
    Returns both the formatted response AND parsed files for caching
    """
    try:
        logger.info("Generating changeset preview with OpenAI...")
        logger.info(f"📸 Image data received in _generate_changeset_preview: {image_data is not None}")
        
        # Use the same AI generator as PR creation
        if not github_helper_instance or not github_helper_instance.use_ai or not github_helper_instance.ai_generator:
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
        result = github_helper_instance.ai_generator.generate_code_sync(
            task_description=full_prompt,
            context=context,
            image_data=image_data,  # Pass image for vision API
            stream_callback=stream_callback  # Pass streaming callback
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Code generation failed")
            }
        
        # Get the raw response and parsed files
        raw_response = result.get("raw_response", "")
        parsed_files = result.get("files", [])
        was_truncated = result.get("truncated", False)
        
        logger.info(f"SpoonOS preview generated: {len(parsed_files)} file(s)")
        
        if was_truncated:
            logger.warning("⚠️  AI response was truncated during preview generation")
        
        # Format the response as a changeset for Slack with GitHub-style diff
        if parsed_files:
            formatted_response = ""
            
            # Add truncation warning at the top if needed
            if was_truncated:
                formatted_response += "⚠️ **WARNING**: Response truncated - last file may be incomplete. Consider smaller tasks.\n\n"
            
            formatted_response += "📝 PROPOSED CHANGESET\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
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
                    formatted_response += f"```diff\n"
                    # Show deleted lines with - prefix (red in diff)
                    preview_lines = lines[:20] if len(lines) > 20 else lines
                    for line in preview_lines:
                        formatted_response += f"- {line}\n"
                    if len(lines) > 20:
                        formatted_response += f"... ({len(lines) - 20} more lines)\n"
                    formatted_response += f"```\n\n"
                elif action == "NEW":
                    formatted_response += f"🟢 `{filepath}` *[NEW]* `+{line_count}`\n\n"
                    formatted_response += f"```diff\n"
                    # Show new lines with + prefix (green in diff)
                    preview_lines = lines[:20] if len(lines) > 20 else lines
                    for line in preview_lines:
                        formatted_response += f"+ {line}\n"
                    if len(lines) > 20:
                        formatted_response += f"... ({len(lines) - 20} more lines)\n"
                    formatted_response += f"```\n\n"
                else:  # MODIFIED
                    # For modified files, we don't have the old content to compare
                    # So we just show the new content with + prefix
                    formatted_response += f"🟡 `{filepath}` *[MODIFIED]* `~{line_count}`\n\n"
                    formatted_response += f"```diff\n"
                    preview_lines = lines[:20] if len(lines) > 20 else lines
                    for line in preview_lines:
                        formatted_response += f"+ {line}\n"
                    if len(lines) > 20:
                        formatted_response += f"... ({len(lines) - 20} more lines)\n"
                    formatted_response += f"```\n\n"
                
                formatted_response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            formatted_response += f"📊 Summary: {len(parsed_files)} file(s) in this changeset"
        else:
            formatted_response = str(raw_response)
        
        return {
            "success": True,
            "raw_response": formatted_response,
            "parsed_files": parsed_files,  # Cache these for PR creation!
            "truncated": was_truncated  # Flag if response was truncated
        }
        
    except Exception as e:
        logger.error(f"Error generating preview with SpoonOS: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


def format_changeset_response(ai_response, is_initial=False):
    """
    Format AI response as a clear changeset
    
    Args:
        ai_response: Raw AI response
        is_initial: Whether this is the initial response
        
    Returns:
        Formatted changeset string
    """
    import re
    
    # Add header
    if is_initial:
        header = "📝 **PROPOSED CHANGESET**\n\n"
    else:
        header = "📝 **UPDATED CHANGESET**\n\n"
    
    # Ensure response is string
    response_text = str(ai_response)
    
    # Count files
    file_patterns = [
        r'File:\s+([\w/\.-]+)',  # File: path/to/file.py
        r'📄\s+\*\*File:\s+([\w/\.-]+)',  # 📄 **File: path/to/file.py**
        r'`([\w/\.-]+\.(?:py|js|ts|java|go|rs|cpp|c|h|rb|php))`'  # `file.py`
    ]
    
    files_found = set()
    for pattern in file_patterns:
        matches = re.findall(pattern, response_text)
        files_found.update(matches)
    
    file_count = len(files_found)
    
    # Build formatted response
    formatted = header + response_text
    
    # Add summary footer
    footer = f"\n\n{'━'*40}\n📊 **Summary**: {file_count} file(s) in this changeset"
    if file_count > 0:
        footer += f"\n📝 Files: {', '.join(sorted(files_found))}"
    formatted += footer
    
    return formatted, file_count

# Per-user GitHub helper instances (cached)
_user_github_helpers = {}


def get_user_github_helper(slack_user_id: str, channel_id: Optional[str] = None) -> Optional[GitHubPRHelper]:
    """
    Get or create a GitHubPRHelper instance for a specific user and channel
    
    Args:
        slack_user_id: Slack user ID
        channel_id: Optional channel ID for channel-specific repo configuration
        
    Returns:
        GitHubPRHelper instance or None if user not authenticated/configured
    """
    # Check if user is authenticated
    if not auth_manager.is_user_authenticated(slack_user_id):
        logger.warning(f"User {slack_user_id} not authenticated with GitHub")
        return None
    
    # Check if user has set a repo (channel-specific or global)
    user_repo = auth_manager.get_user_repo(slack_user_id, channel_id)
    if not user_repo or user_repo == "Not set":
        logger.warning(f"User {slack_user_id} has not set a repository for channel {channel_id}")
        return None
    
    # Use cache key that includes channel-specific repo
    cache_key = f"{slack_user_id}:{user_repo}"
    
    # Return cached instance if available for this user+repo combo
    if cache_key in _user_github_helpers:
        return _user_github_helpers[cache_key]
    
    # Create new instance
    try:
        user_token = auth_manager.get_user_token(slack_user_id)
        use_ai = os.environ.get("USE_AI_CODE_GENERATION", "true").lower() == "true"
        
        helper = GitHubPRHelper(
            github_token=user_token,
            repo_name=user_repo,
            use_ai=use_ai
        )
        
        _user_github_helpers[cache_key] = helper
        logger.info(f"Created GitHub helper for user {slack_user_id} (repo: {user_repo}, channel: {channel_id})")
        return helper
        
    except Exception as e:
        logger.error(f"Failed to create GitHub helper for user {slack_user_id}: {e}")
        return None


# Legacy support: Try to create a global github_helper if old env vars exist
# This allows gradual migration - remove once all users are on OAuth
github_helper = None
if os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"):
    try:
        use_ai = os.environ.get("USE_AI_CODE_GENERATION", "true").lower() == "true"
        github_helper = GitHubPRHelper(
            github_token=os.environ.get("GITHUB_TOKEN"),
            repo_name=os.environ.get("GITHUB_REPO"),
            use_ai=use_ai
        )
        logger.info(f"⚠️ Using legacy shared GitHub token (consider migrating to OAuth)")
    except Exception as e:
        logger.warning(f"GitHub integration failed to initialize: {e}")


def get_channel_context(client, channel_id, limit=50):
    """
    Fetch recent messages from the channel to provide context.
    
    Args:
        client: Slack client instance
        channel_id: The ID of the channel
        limit: Number of recent messages to fetch (default: 50)
    
    Returns:
        List of formatted message strings with context
    """
    try:
        # Fetch conversation history
        result = client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        
        messages = result.get("messages", [])
        context_messages = []
        
        for msg in reversed(messages):  # Reverse to get chronological order
            # Skip bot messages and system messages if needed
            if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                continue
                
            user_id = msg.get("user", "Unknown")
            text = msg.get("text", "")
            timestamp = msg.get("ts", "")
            
            # Format timestamp
            try:
                ts_float = float(timestamp)
                dt = datetime.fromtimestamp(ts_float)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = "Unknown time"
            
            # Get user info
            try:
                user_info = client.users_info(user=user_id)
                username = user_info["user"]["real_name"] or user_info["user"]["name"]
            except:
                username = f"User {user_id}"
            
            context_messages.append(f"[{time_str}] {username}: {text}")
        
        return context_messages
    
    except Exception as e:
        logger.error(f"Error fetching channel context: {e}")
        return []


def get_thread_context(client, channel_id, thread_ts):
    """
    Fetch all messages from a thread to provide thread context.
    
    Args:
        client: Slack client instance
        channel_id: The ID of the channel
        thread_ts: The timestamp of the parent message
    
    Returns:
        List of formatted thread message strings
    """
    try:
        result = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        
        messages = result.get("messages", [])
        thread_messages = []
        
        for msg in messages:
            user_id = msg.get("user", "Unknown")
            text = msg.get("text", "")
            timestamp = msg.get("ts", "")
            
            # Format timestamp
            try:
                ts_float = float(timestamp)
                dt = datetime.fromtimestamp(ts_float)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = "Unknown time"
            
            # Get user info
            try:
                user_info = client.users_info(user=user_id)
                username = user_info["user"]["real_name"] or user_info["user"]["name"]
            except:
                username = f"User {user_id}"
            
            thread_messages.append(f"[{time_str}] {username}: {text}")
        
        return thread_messages
    
    except Exception as e:
        logger.error(f"Error fetching thread context: {e}")
        return []


# Old command detection functions removed - now using AI-powered classify_command() from intent_classification.py


def is_ai_asking_question(response_text):
    """
    Detect if the AI is asking for more information
    
    Args:
        response_text: AI response text
        
    Returns:
        bool: True if AI is asking a question
    """
    # Look for question indicators
    question_indicators = [
        "need more",
        "please provide",
        "can you provide",
        "could you clarify",
        "what kind of",
        "which",
        "specify",
        "additional information",
        "more details",
        "tell me more",
        "?",  # Ends with question mark
    ]
    
    text_lower = response_text.lower()
    return any(indicator in text_lower for indicator in question_indicators)


def extract_image_from_message(event, client, logger):
    """Extract image URL and file info from Slack message event"""
    try:
        files = event.get("files", [])
        for file in files:
            if file.get("mimetype", "").startswith("image/"):
                image_url = file.get("url_private")
                if image_url:
                    logger.info(f"Found image: {file.get('name')} ({file.get('mimetype')})")
                    logger.info(f"🔗 Initial image URL from event: {image_url}")
                    return image_url, file
        return None, None
    except Exception as e:
        logger.error(f"Error extracting image: {e}")
        return None, None


def download_slack_image(image_url, client, file_info=None):
    """Download image from Slack, validate format, and encode to base64"""
    try:
        import requests
        import base64
        # Use file ID to get fresh download URL via SDK
        if file_info and file_info.get('id'):
            try:
                file_id = file_info.get('id')
                logger.info(f"🔗 File ID: {file_id}")
                
                # Get fresh file info with current download URLs
                file_response = client.files_info(file=file_id)
                file_data = file_response.get('file', {})
                
                # Get the download URL - prefer url_private_download
                download_url = file_data.get('url_private_download')
                if not download_url:
                    download_url = file_data.get('url_private')
                if not download_url:
                    logger.error(f"No download URL found in file info")
                    return None
                
                logger.info(f"🔗 Download URL: {download_url}")
            except Exception as e:
                logger.error(f"Could not get file info via SDK: {e}")
                return None
        else:
            logger.error(f"No file_info provided, cannot download image")
            return None
        
        bot_token = os.environ.get("SLACK_BOT_TOKEN")
        if not bot_token:
            logger.error("SLACK_BOT_TOKEN not found in environment!")
            return None
        
        headers = {"Authorization": f"Bearer {bot_token}"}
        
        logger.info(f"🌐 Attempting download from: {download_url}")
        response = requests.get(download_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        raw_bytes = response.content
        logger.info(f"Downloaded image bytes: {len(raw_bytes)} bytes")
        
        # Check if we got HTML instead of an image
        if raw_bytes.startswith(b'<!DOCTYPE') or raw_bytes.startswith(b'<html') or raw_bytes.startswith(b'<?xml'):
            logger.error(f"Received HTML/XML instead of image data")
            return None
        
        # Detect format from magic bytes
        if raw_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            image_format = 'png'
        elif raw_bytes.startswith(b'\xff\xd8\xff'):
            image_format = 'jpeg'
        elif raw_bytes.startswith(b'GIF87a') or raw_bytes.startswith(b'GIF89a'):
            image_format = 'gif'
        elif raw_bytes.startswith(b'RIFF') and b'WEBP' in raw_bytes[:12]:
            image_format = 'webp'
        else:
            # Default to PNG if unknown
            image_format = 'png'
        
        # Encode to base64
        image_data = base64.b64encode(raw_bytes).decode('utf-8')
        logger.info(f"Image downloaded successfully: {image_format}, {len(raw_bytes)} bytes")
        
        # Get filename from file_info if available
        filename = file_info.get('name', 'unknown_image') if file_info else 'unknown_image'
        logger.info(f"Filename: {filename}")
        
        return {
            "data": image_data,
            "format": image_format,
            "url": image_url,
            "filename": filename
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error downloading image: {e.response.status_code}")
        if e.response.status_code == 403:
            logger.error("Bot lacks 'files:read' permission")
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def _get_channel_display_name(client, channel_id):
    """
    Resolve a human-friendly channel name (e.g. #backend, DM @alice)
    """
    name = channel_id
    try:
        info = client.conversations_info(channel=channel_id)
        channel = info.get("channel", {})
        if not channel:
            return channel_id

        if channel.get("is_im"):
            user_id = channel.get("user")
            if user_id:
                try:
                    user_info = client.users_info(user=user_id)
                    user = user_info.get("user", {})
                    display = user.get("real_name") or user.get("name") or user_id
                    return f"DM @{display}"
                except Exception:
                    return f"DM {user_id}"
            return "Direct Message"

        if channel.get("is_mpim"):
            return channel.get("name") or channel.get("name_normalized") or channel_id

        channel_name = (
            channel.get("name")
            or channel.get("name_normalized")
            or channel.get("id")
            or channel_id
        )
        if channel_name.startswith("#"):
            return channel_name
        return f"#{channel_name}"
    except Exception as e:
        logger.warning(f"Could not resolve channel name for {channel_id}: {e}")
        return name


def handle_pr_conversation(
    user_id,
    message_text,
    say,
    thread_ts,
    client=None,
    channel_id=None,
    is_initial=False,
    image_data=None,
    channel_name=None,
):
    """
    Handle conversational PR planning - discuss requirements before creating PR
    
    Args:
        user_id: Slack user ID
        message_text: User's message
        say: Slack say function
        thread_ts: Thread timestamp
        client: Slack client
        channel_id: Channel ID
        is_initial: True if this is the initial "create PR" command
        image_data: Optional dict holding base64 encoded image for vision models
        channel_name: Optional Slack channel name (for analytics/dashboard)
    """
    logger.info("=" * 80)
    logger.info("💬 HANDLE_PR_CONVERSATION FUNCTION ENTERED")
    logger.info("=" * 80)
    logger.info(f"   User ID: {user_id}")
    logger.info(f"   Message Text: {message_text}")
    logger.info(f"   Thread TS: {thread_ts}")
    logger.info(f"   Channel ID: {channel_id}")
    logger.info(f"   Is Initial: {is_initial}")
    logger.info(f"   Current Conversations: {list(pr_conversations.keys())}")
    logger.info("=" * 80)
    
    # Get per-user GitHub helper (channel-specific repo)
    user_github_helper = get_user_github_helper(user_id, channel_id)
    if not user_github_helper:
        say(
            text=f"<@{user_id}> ❌ GitHub helper not available. Please check your connection and set a repo for this channel.",
            thread_ts=thread_ts
        )
        return
    
    logger.info(f"   User GitHub Helper: {user_github_helper.repo_name}")
    
    # Check if this is a file deletion request - skip AI planning for deletions
    if user_github_helper and hasattr(user_github_helper, '_detect_file_deletion'):
        files_to_delete = user_github_helper._detect_file_deletion(message_text)
        if files_to_delete:
            # For deletion tasks, create PR immediately without AI planning
            logger.info(f"Detected deletion request in conversation: {files_to_delete}, creating PR directly")
            say(
                text=f"<@{user_id}> 🗑️ Detected file deletion request. Creating PR to delete: {', '.join(files_to_delete)}...",
                thread_ts=thread_ts
            )
            
            # Fetch codebase context for deletion verification (with user prompt for smart loading)
            try:
                default_branch = user_github_helper.repo.default_branch
                codebase_context = user_github_helper._get_full_codebase_context(default_branch, user_prompt=message_text)
            except Exception as e:
                logger.error(f"Error fetching codebase context for deletion: {e}")
                codebase_context = None
            
            # Create PR directly with the deletion task, passing thread_ts for unique branch naming
            start_time = time.time()
            result = user_github_helper.create_random_pr(
                message_text, 
                thread_context=thread_ts,
                codebase_context=codebase_context
            )
            processing_time_ms = int((time.time() - start_time) * 1000)
            if result.get("success"):
                _record_pr_creation(thread_ts, result.get("pr_number"), processing_time_ms)
            _send_pr_result(result, message_text, say, thread_ts, user_id)
            return
    
    # Initialize or get conversation state
    conversation_key = thread_ts
    
    if conversation_key not in pr_conversations:
        pr_conversations[conversation_key] = {
            "messages": [],
            "initial_task": message_text if is_initial else "",
            "user_id": user_id,
            "thread_ts": thread_ts,
            "channel_id": channel_id,
            "channel_name": channel_name or channel_id,
            "plan": None,
            "codebase_context": None,  # Will be fetched once and cached
            "cached_files": [],  # Parsed files from preview (for PR creation)
            "image_data": image_data  # Store image for vision API
        }
        _save_pr_conversations()  # Save new conversation
    else:
        if image_data:
            # Update image data if provided in follow-up message
            pr_conversations[conversation_key]["image_data"] = image_data
            logger.info("📸 Updated image data in conversation")
        if channel_name:
            pr_conversations[conversation_key]["channel_name"] = channel_name
    
    # Always use the stored user_id to tag
    stored_user_id = pr_conversations[conversation_key]["user_id"]
    
    # Add user message to history
    pr_conversations[conversation_key]["messages"].append({
        "role": "user",
        "content": message_text
    })
    _save_pr_conversations()  # Save after user message
    
    # Check if user wants to create the PR now
    if is_ready_to_create_pr(message_text) and not is_initial:
        say(
            text=f"<@{stored_user_id}> ✅ Perfect! Creating the pull request now...",
            thread_ts=thread_ts
        )
        
        # Get all conversation history
        all_messages = "\n\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in pr_conversations[conversation_key]["messages"]
        ])
        
        # Get the cached codebase context and files
        codebase_context = pr_conversations[conversation_key].get("codebase_context")
        cached_files = pr_conversations[conversation_key].get("cached_files", [])
        
        # Pass thread_ts as context for unique branch naming AND codebase context
        start_time = time.time()
        result = user_github_helper.create_random_pr(
            all_messages, 
            thread_context=thread_ts,
            codebase_context=codebase_context,
            cached_files=cached_files  # Use cached result from preview!
        )
        processing_time_ms = int((time.time() - start_time) * 1000)
        if result.get("success"):
            _record_pr_creation(conversation_key, result.get("pr_number"), processing_time_ms)
        _send_pr_result(result, pr_conversations[conversation_key]["initial_task"], say, thread_ts, stored_user_id)
        
        # Only mark as complete on SUCCESS - allow retries on failure
        if result.get("success"):
            pr_conversations[conversation_key]["pr_created"] = True
            pr_conversations[conversation_key]["pr_result"] = result
            _save_pr_conversations()  # Save after successful PR creation
        else:
            # Keep conversation for retry, but save the error
            pr_conversations[conversation_key]["last_error"] = result.get("error")
            _save_pr_conversations()
        return
    
    # Send initial message for new conversations
    if is_initial:
        say(
            text=f"<@{stored_user_id}> 🤖 I'll propose code changes for: *{message_text}*\n\n📚 Reading codebase...\n\n💡 _Tip: I'll show you a changeset. Reply to refine it (\"add tests\", \"use one file\", etc), or say **'make pr'** / click the button when ready to submit!_",
            thread_ts=thread_ts
        )
    
    # Check if AI is available
    if not user_github_helper.use_ai or not user_github_helper.ai_generator:
        say(
            text=f"<@{stored_user_id}> SpoonOS agents not available. Say **'make PR'** when you want me to create a placeholder PR.",
            thread_ts=thread_ts
        )
        return
    
    # Get AI response
    loading_ts = None  # Initialize to track loading message
    try:
        # Use direct OpenAI for both preview and PR creation (with caching for consistency)
        
        # Fetch codebase context once and cache it (for conversation preview)
        # Safety check: add codebase_context if it doesn't exist (for old conversations)
        if "codebase_context" not in pr_conversations[conversation_key]:
            pr_conversations[conversation_key]["codebase_context"] = None
        
        if pr_conversations[conversation_key]["codebase_context"] is None:
            logger.info("Fetching full codebase context for conversation preview...")
            say(
                text=f"<@{stored_user_id}> 📚 Analyzing codebase with Spoon AI...",
                thread_ts=thread_ts
            )
            try:
                # Get the default branch and fetch smart context based on user's task
                default_branch = user_github_helper.repo.default_branch
                # Use the initial task for smart file selection
                user_task = pr_conversations[conversation_key].get("initial_task", message_text)
                codebase_context = user_github_helper._get_full_codebase_context(default_branch, user_prompt=user_task)
                pr_conversations[conversation_key]["codebase_context"] = codebase_context
                logger.info(f"Codebase context cached: {len(codebase_context)} chars")
            except Exception as e:
                logger.error(f"Error fetching codebase context: {e}")
                pr_conversations[conversation_key]["codebase_context"] = f"Repository: {user_github_helper.repo_name}\n\nError reading codebase: {str(e)}"
            _save_pr_conversations()  # Save after caching codebase context
        
        # Build conversation context
        conversation_history = pr_conversations[conversation_key]["messages"]
        full_context = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        
        # Generate changeset preview
        planning_prompt = f"""Task: {full_context}

Context: Repository {user_github_helper.repo_name}

IMPORTANT: Propose CONCRETE CODE CHANGES immediately. Do NOT ask clarifying questions.

Respond with a CHANGESET in this format:

📝 PROPOSED CHANGESET
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
[One-line summary of what this changeset does]

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: path/to/file1.html [NEW]

```html
[Complete file content]
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: path/to/file2.js [NEW]

```javascript
[Complete file content]
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: 2 file(s) in this changeset
📝 Files: path/to/file1.html, path/to/file2.js

Rules:
- Propose changes immediately, don't ask questions
- For MULTIPLE files, create SEPARATE file sections (each with 📄 File: header)
- Use the EXACT filename the user specified (e.g., snake.html not snake.md)
- For MODIFIED files, show the COMPLETE updated file
- For NEW files, show the complete new file
- For DELETED files, use [DELETED] tag and list EACH FILE explicitly by name (e.g., "delete all .py files" means list each one: test.py [DELETED], utils.py [DELETED], etc.)
- DO NOT create files describing deletions - use the [DELETED] tag to actually delete files
- Base changes on the full codebase context provided
- Make reasonable assumptions about what the user wants
"""
        
        # Use the cached full codebase context for preview
        full_codebase_context = pr_conversations[conversation_key]["codebase_context"]
        stored_image_data = pr_conversations[conversation_key].get("image_data")
        
        logger.info(f"🖼️ Image data in conversation: {stored_image_data is not None}")
        if stored_image_data:
            logger.info(f"   Image format: {stored_image_data.get('format')}")
            logger.info(f"   Image data length: {len(stored_image_data.get('data', ''))}")
        
        # Send loading message while AI generates
        loading_msg = say(
            text=f"<@{stored_user_id}> :hourglass_flowing_sand: *Generating changeset...*\n\n_Spoon AI is analyzing your request and crafting code changes..._",
            thread_ts=thread_ts
        )
        loading_ts = loading_msg.get("ts") if loading_msg else None
        
        # Create streaming callback to update Slack message with progress
        last_update_time = [time.time()]  # Use list to allow mutation in closure
        
        def slack_stream_callback(current_text: str, is_complete: bool):
            """Update Slack message with streaming progress"""
            nonlocal loading_ts
            
            # Rate limit updates to every 2 seconds (avoid Slack API limits)
            current_time = time.time()
            if not is_complete and (current_time - last_update_time[0]) < 2.0:
                return
            
            last_update_time[0] = current_time
            
            if loading_ts and client:
                try:
                    # Show progress indicator with character count
                    char_count = len(current_text)
                    if is_complete:
                        status = "✅ *Generation complete!* Processing response..."
                    else:
                        # Show a preview of what's being generated
                        status = f":hourglass_flowing_sand: *Generating...* ({char_count:,} chars)\n\n"
                        # Show last few lines as preview (truncated)
                        lines = current_text.strip().split('\n')
                        preview_lines = lines[-5:] if len(lines) > 5 else lines
                        preview = '\n'.join(preview_lines)
                        if len(preview) > 500:
                            preview = preview[-500:]
                        status += f"```\n...{preview}\n```"
                    
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_ts,
                        text=f"<@{stored_user_id}> {status}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to update streaming message: {e}")
        
        # Generate changeset preview using SpoonOS with vision if image is available
        ai_result = _generate_changeset_preview(
            prompt=planning_prompt,
            context=full_codebase_context,
            github_helper_instance=user_github_helper,
            image_data=stored_image_data,  # Pass image for vision API
            stream_callback=slack_stream_callback  # Stream updates to Slack
        )
        
        if not ai_result.get("success"):
            error_text = f"<@{stored_user_id}> ❌ AI error: {ai_result.get('error')}"
            
            # Update loading message with error, or send new message
            if loading_ts and client:
                try:
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_ts,
                        text=error_text
                    )
                except Exception:
                    say(text=error_text, thread_ts=thread_ts)
            else:
                say(text=error_text, thread_ts=thread_ts)
            return
        
        ai_response = ai_result.get("raw_response", "")
        parsed_files = ai_result.get("parsed_files", [])
        was_truncated = ai_result.get("truncated", False)
        
        logger.info(f"Caching {len(parsed_files)} parsed files for PR creation")
        
        # Warn user if response was truncated
        if was_truncated:
            logger.warning("⚠️  AI response was truncated - last file may be incomplete")
            ai_response = "⚠️ **WARNING**: Response was truncated due to length. Last file may be incomplete. Consider breaking this into smaller tasks.\n\n" + ai_response
        
        # Store AI response AND parsed files (for PR creation)
        pr_conversations[conversation_key]["messages"].append({
            "role": "assistant",
            "content": ai_response
        })
        pr_conversations[conversation_key]["cached_files"] = parsed_files  # Cache for PR!
        _save_pr_conversations()  # Save after AI response and cached files
        
        # Send response with instructions and Make PR button
        # Split long messages into chunks (Slack limit: 3000 chars per block)
        def split_message_into_chunks(message: str, max_length: int = 2900) -> list:
            """Split message into chunks that fit Slack's block size limit"""
            # Leave room for the user tag and formatting
            chunks = []
            current_chunk = ""
            
            for line in message.split('\n'):
                # If adding this line would exceed limit, start new chunk
                if len(current_chunk) + len(line) + 1 > max_length:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = line
                else:
                    if current_chunk:
                        current_chunk += '\n' + line
                    else:
                        current_chunk = line
            
            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks if chunks else [message[:max_length]]
        
        # Create blocks with message chunks
        full_message = f"<@{stored_user_id}> {ai_response}"
        message_chunks = split_message_into_chunks(full_message, max_length=2900)
        
        blocks = []
        
        # Add message chunks as section blocks
        for i, chunk in enumerate(message_chunks):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chunk
                }
            })
        
        # Add divider and button after all message chunks
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚀 Make PR with These Changes",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": thread_ts,
                        "action_id": "make_pr_button"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "_Reply in thread to refine the changes, or click the button above to create the PR now_"
                    }
                ]
            }
        ])
        
        logger.info(f"Sending response with {len(message_chunks)} message chunk(s)")
        logger.info("=" * 80)
        logger.info("💬 ABOUT TO SEND SLACK MESSAGE")
        logger.info("=" * 80)
        logger.info(f"   User to tag: {stored_user_id}")
        logger.info(f"   Thread TS: {thread_ts}")
        logger.info(f"   Number of blocks: {len(blocks)}")
        logger.info(f"   Number of chunks: {len(message_chunks)}")
        logger.info("=" * 80)
        
        # Update loading message if we sent one, otherwise send new message
        if loading_ts and client:
            try:
                client.chat_update(
                    channel=channel_id,
                    ts=loading_ts,
                    text=f"<@{stored_user_id}> Proposed changeset ready! (see blocks for details)",
                    blocks=blocks
                )
                logger.info("✅ Updated loading message with changeset!")
            except Exception as update_error:
                logger.warning(f"Could not update loading message: {update_error}")
                # Fall back to sending new message
                say(
                    text=f"<@{stored_user_id}> Proposed changeset ready! (see blocks for details)",
                    blocks=blocks,
                    thread_ts=thread_ts
                )
                logger.info("✅ Sent new message instead!")
        else:
            say(
                text=f"<@{stored_user_id}> Proposed changeset ready! (see blocks for details)",
                blocks=blocks,
                thread_ts=thread_ts
            )
            logger.info("✅ Slack message sent successfully!")
        
    except Exception as e:
        logger.error(f"Error in PR conversation: {e}")
        error_text = f"<@{stored_user_id}> ❌ Error: {str(e)}"
        
        # Update loading message with error, or send new message
        if loading_ts and client:
            try:
                client.chat_update(
                    channel=channel_id,
                    ts=loading_ts,
                    text=error_text
                )
            except Exception:
                say(text=error_text, thread_ts=thread_ts)
        else:
            say(text=error_text, thread_ts=thread_ts)


def _record_pr_creation(conversation_key, pr_number, processing_time_ms=None):
    """Persist analytics data for dashboard consumption."""
    if not pr_number:
        return
    try:
        conv = pr_conversations.get(conversation_key, {})
        channel_id = conv.get("channel_id") or conversation_key or "unknown-channel"
        channel_name = conv.get("channel_name") or channel_id
        log_pr_creation(
            pr_number=int(pr_number),
            channel_id=channel_id,
            channel_name=channel_name,
            thread_ts=conversation_key,
            processing_time_ms=processing_time_ms,
        )
    except Exception as e:
        logger.error(f"Failed to record PR creation analytics: {e}")


def _send_pr_result(result, task_description, say, thread_ts, user_id):
    """Helper to send PR creation result"""
    try:
        logger.info(f"=== _send_pr_result called ===")
        logger.info(f"Result: {result}")
        logger.info(f"Task: {task_description}")
        logger.info(f"User ID: {user_id}")
        
        if not isinstance(result, dict):
            raise ValueError(f"Invalid result type: {type(result)}")
        
        if result.get("success", False):
            # Safely get all required fields with defaults
            pr_number = result.get('pr_number', 'N/A')
            branch_name = result.get('branch_name', 'N/A')
            pr_url = result.get('pr_url', 'N/A')
            changes = result.get('changes', 'No changes listed')
            
            logger.info(f"PR Number: {pr_number} (type: {type(pr_number)})")
            
            response = f"""✅ *Pull Request Created Successfully!*

📋 *Task:* {task_description}
🔢 *PR #:* {pr_number}
🌿 *Branch:* `{branch_name}`
🔗 *URL:* {pr_url}

📝 *Changes:* {changes}

The PR is ready for review! 🎉"""

            # Add merge button if PR was created successfully
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                }
            ]
            
            # Add merge button if we have a valid PR number
            if pr_number and pr_number != 'N/A' and pr_number != 'None':
                logger.info(f"Adding Merge PR button for PR #{pr_number}")
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔀 Merge PR",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"merge_pr_{pr_number}",
                            "action_id": f"merge_pr_button_{pr_number}"
                        }
                    ]
                })
                logger.info(f"Blocks with button: {blocks}")
            else:
                logger.warning(f"Not adding Merge button - invalid PR number: {pr_number}")
            
            say(
                text=response,  # Fallback text
                blocks=blocks,
                thread_ts=thread_ts
            )
            logger.info(f"Sent PR result message with {len(blocks)} blocks")
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            response = f"""❌ *Failed to Create Pull Request*

*Task:* {task_description}
*Error:* {error_msg}

You can retry by clicking the button below or saying "make pr" again."""
            
            # Add retry button on failure
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 Retry PR Creation",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": thread_ts,
                            "action_id": "make_pr_button"
                        }
                    ]
                }
            ]
            
            say(
                text=response,
                blocks=blocks,
                thread_ts=thread_ts
            )
    except Exception as e:
        logger.error(f"Error sending PR result: {e}, result: {result}")
        error_msg = str(e) if str(e) else "Unknown error occurred"
        say(
            text=f"<@{user_id}> ❌ Error creating PR: {error_msg}\n\nPlease check the bot logs for details.",
            thread_ts=thread_ts
        )


def handle_pr_merge(user_id, pr_number, merge_method, say, thread_ts, channel_id=None):
    """
    Handle merging a GitHub pull request
    
    Args:
        user_id: Slack user ID
        pr_number: PR number to merge
        merge_method: Method to use for merging (merge, squash, rebase)
        say: Slack say function
        thread_ts: Thread timestamp
        channel_id: Optional channel ID for channel-specific repo
    """
    # Get per-user GitHub helper (channel-specific repo)
    user_github_helper = get_user_github_helper(user_id, channel_id)
    if not user_github_helper:
        say(
            text=f"<@{user_id}> ❌ GitHub helper not available. Please check your connection.",
            thread_ts=thread_ts
        )
        return
    
    # Send acknowledgment
    say(
        text=f"🔄 Got it <@{user_id}>! Merging PR #{pr_number} using {merge_method} method...\n\nPlease wait...",
        thread_ts=thread_ts
    )
    
    # Merge the PR
    result = user_github_helper.merge_pr(pr_number, merge_method)
    
    if result["success"]:
        try:
            mark_pr_merged(result.get('pr_number'))
        except Exception as e:
            logger.error(f"Failed to log merged PR analytics: {e}")
        response = f"""✅ *Pull Request Merged Successfully!*

🔢 *PR #:* {result['pr_number']}
📋 *Title:* {result['pr_title']}
🌿 *Branch:* `{result['branch_name']}`
🔀 *Merge Method:* {result['merge_method']}
🔗 *URL:* {result['pr_url']}

The changes have been merged to master! 🎉"""
        
        # Add unmerge button
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": response
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "↩️ Unmerge PR",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": f"unmerge_pr_{result['pr_number']}",
                        "action_id": f"unmerge_pr_button_{result['pr_number']}"
                    }
                ]
            }
        ]
        
        say(
            text=response,  # Fallback text
            blocks=blocks,
            thread_ts=thread_ts
        )
    else:
        response = f"""❌ *Failed to Merge Pull Request*

*PR #:* {pr_number}
*Error:* {result['error']}

Please check the PR status and try again, or merge it manually on GitHub.
"""
        
        say(
            text=response,
            thread_ts=thread_ts
        )


def handle_pr_unmerge(user_id, pr_number, say, thread_ts, channel_id=None):
    """
    Handle creating a revert PR for a merged pull request
    
    Args:
        user_id: Slack user ID
        pr_number: PR number to revert
        say: Slack say function
        thread_ts: Thread_timestamp
        channel_id: Optional channel ID for channel-specific repo
    """
    # Get per-user GitHub helper (channel-specific repo)
    user_github_helper = get_user_github_helper(user_id, channel_id)
    if not user_github_helper:
        say(
            text=f"<@{user_id}> ❌ GitHub helper not available. Please check your connection.",
            thread_ts=thread_ts
        )
        return
    
    # Send acknowledgment
    say(
        text=f"🔄 Got it <@{user_id}>! Creating a revert PR for #{pr_number}...\n\nPlease wait...",
        thread_ts=thread_ts
    )
    
    # Create the revert PR
    result = user_github_helper.create_revert_pr(pr_number)
    
    if result["success"]:
        response = f"""✅ *Revert Pull Request Created Successfully!*

🔄 *Reverting PR #:* {result['original_pr_number']}
📋 *Original Title:* {result['original_pr_title']}
🔗 *Original PR:* {result['original_pr_url']}

**New Revert PR:**
🔢 *PR #:* {result['revert_pr_number']}
🌿 *Branch:* `{result['revert_branch_name']}`
🔗 *URL:* {result['revert_pr_url']}

The revert PR is ready for review! You can now merge it to undo the original changes."""
        
        # Add merge button for the revert PR
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": response
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔀 Merge Revert PR",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": f"merge_pr_{result['revert_pr_number']}",
                        "action_id": f"merge_pr_button_{result['revert_pr_number']}"
                    }
                ]
            }
        ]
        
        say(
            text=response,  # Fallback text
            blocks=blocks,
            thread_ts=thread_ts
        )
    else:
        response = f"""❌ *Failed to Create Revert PR*

*Original PR #:* {pr_number}
*Error:* {result['error']}

Note: You can only revert PRs that have been merged.
"""
        
        say(
            text=response,
            thread_ts=thread_ts
        )


def handle_repo_create(user_id, repo_name, say, thread_ts, description=None, private=False):
    """
    Handle creating a new GitHub repository
    
    Args:
        user_id: Slack user ID
        repo_name: Name of the repository to create
        say: Slack say function
        thread_ts: Thread timestamp
        description: Optional repository description
        private: Whether the repo should be private (default False)
    """
    from github import Github, GithubException
    
    # Get user's GitHub token
    github_token = auth_manager.get_user_token(user_id)
    if not github_token:
        say(
            text=f"<@{user_id}> ❌ GitHub not connected. Please connect your GitHub account first.",
            thread_ts=thread_ts
        )
        return
    
    try:
        # Send acknowledgment
        visibility = "private" if private else "public"
        say(
            text=f"<@{user_id}> 🔧 Creating {visibility} repository `{repo_name}`...",
            thread_ts=thread_ts
        )
        
        # Create the repository using the user's GitHub token
        g = Github(github_token)
        user = g.get_user()
        
        # Create the repo
        new_repo = user.create_repo(
            name=repo_name,
            description=description or f"Repository created via Slack bot",
            private=private,
            auto_init=True  # Initialize with README
        )
        
        # Get user's GitHub username for the full repo path
        github_username = user.login
        full_repo_name = f"{github_username}/{repo_name}"
        
        logger.info(f"✅ Created repository: {full_repo_name}")
        
        # Send success message
        response = f"""<@{user_id}> ✅ *Repository Created Successfully!*

📦 *Name:* `{full_repo_name}`
🔒 *Visibility:* {visibility.capitalize()}
📝 *Description:* {description or "Repository created via Slack bot"}
🔗 *URL:* {new_repo.html_url}

💡 *Next steps:*
• Set this repo for this channel: `@bot set repo {full_repo_name}`
• Clone it: `git clone {new_repo.clone_url}`
• Start coding and create PRs!"""
        
        say(
            text=response,
            thread_ts=thread_ts
        )
        
    except GithubException as e:
        error_message = str(e)
        if "name already exists" in error_message.lower() or e.status == 422:
            say(
                text=f"<@{user_id}> ❌ Repository `{repo_name}` already exists on your account. Please choose a different name.",
                thread_ts=thread_ts
            )
        else:
            logger.error(f"GitHub error creating repo: {e}")
            say(
                text=f"<@{user_id}> ❌ Failed to create repository: {error_message}",
                thread_ts=thread_ts
            )
    except Exception as e:
        logger.error(f"Error creating repository: {e}")
        say(
            text=f"<@{user_id}> ❌ An error occurred while creating the repository: {str(e)}",
            thread_ts=thread_ts
        )


def _handle_general_command(user_id, message_text, say, thread_ts):
    """
    Handle GENERAL commands - conversational responses and help
    
    Args:
        user_id: Slack user ID
        message_text: User's message
        say: Slack say function
        thread_ts: Thread timestamp
    """
    try:
        import openai
        
        client_openai = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Build context about what the bot can do
        bot_capabilities = """You are a helpful Slack bot. Here's what you can do:

🤖 **What I Can Do:**

1. **Write Code for You** - I generate actual code using AI
   - I have full access to your codebase
   - I understand your existing code and can modify it
   - I show you changesets before creating PRs
   - You can iterate: "add tests", "use one file", etc.

2. **Create PRs** - Turn code changes into pull requests
   - Say: "create a PR to add login page"
   - I'll show you the code, you can refine it
   - Then: click "Make PR" button or say "make pr"

3. **Merge PRs** - Merge pull requests to main
   - Say: "merge PR 123"
   - Options: "merge PR 123 with squash" or "using rebase"

4. **Unmerge PRs** - Revert merged pull requests
   - Say: "revert PR 123" or "unmerge PR 45"

5. **Create Repositories** - Create new GitHub repos
   - Say: "create a new repo called my-project"
   - Options: "create a private repo named secret-app"

6. **View Usage** - See your activity and statistics
   - Say: "show my usage" or "dashboard"
   - I'll send you a link to your personal dashboard

I understand natural language and use AI for everything!"""

        response_ai = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a helpful Slack bot assistant. Answer the user's question in a friendly way.

{bot_capabilities}

IMPORTANT: Always include a brief mention of your capabilities in your response, even for casual questions like "how are you" or "hello". 

For example:
- "How are you?" → "I'm doing great! I'm here to help you write code and manage PRs. I can create PRs, merge them, revert them, and show you your usage stats. What can I help you build today?"
- "Hello" → "Hey there! 👋 I'm a bot that writes code for you and manages GitHub PRs. Need help creating something? Or want to see your dashboard?"
- "What's up?" → "Not much! Ready to help you with code. I can create PRs, merge them, revert changes, or show you your activity. What are you working on?"

Always be conversational but make sure to highlight what you can do. Use Slack markdown formatting."""
                },
                {
                    "role": "user",
                    "content": message_text
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        response = f"<@{user_id}> {response_ai.choices[0].message.content}"
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        # Fallback to simple help text
        response = f"""Hi <@{user_id}>! 🤖

*What I Can Do:*

📝 **Write Code for You**
• I generate actual code using AI
• I understand your codebase

🚀 **Create PRs**
• `create a PR to add login page`

✅ **Merge PRs**
• `merge PR 123`

↩️ **Unmerge PRs**
• `revert PR 45`

📦 **Create Repos**
• `create a new repo called my-app`

Try: "create a PR for [your idea]" and I'll show you the code!"""
    
    # Send response in the same thread if applicable
    say(
        text=response,
        thread_ts=thread_ts
    )


@app.event("app_mention")
def handle_app_mention(event, client, say, logger):
    """
    Handle app mention events - responds when the bot is tagged in a message.
    Now includes PR creation functionality.
    """
    try:
        channel_id = event["channel"]
        user_id = event["user"]
        message_text = event["text"]
        thread_ts = event.get("thread_ts", None) or event.get("ts")
        
        logger.info(f"Bot mentioned by user {user_id} in channel {channel_id}")
        
        channel_name = _get_channel_display_name(client, channel_id)
        
        # Check for attached images (wireframes, screenshots, etc.)
        image_url, file_info = extract_image_from_message(event, client, logger)
        image_data = None
        
        if image_url:
            logger.info(f"📸 Image detected! Downloading from Slack...")
            image_data = download_slack_image(image_url, client, file_info=file_info)
            if image_data:
                logger.info(f"✅ Image downloaded successfully: {image_data['format']}")
                message_text += f"\n\n[WIREFRAME IMAGE ATTACHED]"
            else:
                say(
                    text=f"<@{user_id}> ⚠️ I see you attached an image, but I couldn't download it. Please check permissions.",
                    thread_ts=thread_ts
                )
        
        # Get user info
        user_info = client.users_info(user=user_id)
        username = user_info["user"]["real_name"] or user_info["user"]["name"]
        
        # Check if user has authenticated with GitHub
        if not auth_manager.is_user_authenticated(user_id):
            # User needs to authenticate first
            auth_message = auth_manager.get_auth_instructions_message(user_id)
            say(
                **auth_message,
                thread_ts=thread_ts
            )
            return
        
        # Check for GitHub management commands (BEFORE repo check, since these don't need a repo)
        clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip().lower()
        
        # SET REPO command
        if re.search(r'\bset\s+repo\b', clean_text):
            repo_match = re.search(r'set\s+repo\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)', message_text, re.IGNORECASE)
            if repo_match:
                repo = repo_match.group(1)
                
                # Send "checking" message
                say(
                    text=f"<@{user_id}> 🔍 Checking access to `{repo}`...",
                    thread_ts=thread_ts
                )
                
                # Validate repository access before setting
                validation = auth_manager.validate_repo_access(user_id, repo)
                
                if not validation.get("success"):
                    say(
                        text=f"<@{user_id}> ❌ *Cannot set repository*\n\n{validation.get('error')}",
                        thread_ts=thread_ts
                    )
                    return
                
                # Repository is valid and user has write access - set it
                auth_manager.set_user_repo(user_id, repo, channel_id)
                
                # Get repo info for nice confirmation message
                repo_info = validation.get("repo_info", {})
                permissions = validation.get("permissions", {})
                
                permission_level = "Admin" if permissions.get("admin") else "Write"
                repo_type = "🔒 Private" if repo_info.get("private") else "🌐 Public"
                
                say(
                    text=f"<@{user_id}> ✅ *Repository set for this channel!*\n\n"
                         f"📂 *Repo:* `{repo_info.get('full_name', repo)}`\n"
                         f"{repo_type}\n"
                         f"🔑 *Your access:* {permission_level}\n"
                         f"🌿 *Default branch:* `{repo_info.get('default_branch', 'main')}`\n\n"
                         f"💡 *Pro tip:* You can set different repos in different channels!\n\n"
                         f"You're all set! Now you can:\n"
                         f"• Create PRs: _\"create a login page\"_\n"
                         f"• Merge PRs: _\"merge PR 123\"_\n"
                         f"• View stats: _\"show my usage\"_",
                    thread_ts=thread_ts
                )
            else:
                say(
                    text=f"<@{user_id}> ⚠️ Please specify a repository in the format: `owner/repository`\n\nExample: `set repo myusername/my-project`",
                    thread_ts=thread_ts
                )
            return
        
        # GITHUB STATUS command
        elif re.search(r'\bgithub\s+status\b', clean_text) or re.search(r'\bconnection\s+status\b', clean_text):
            user_info = auth_manager.get_user_info(user_id)
            if user_info:
                github_username = user_info.get("github_username", "Unknown")
                github_repo = user_info.get("github_repo", "Not set")
                auth_date = user_info.get("authenticated_at", "Unknown")
                say(
                    text=f"<@{user_id}> 🔗 *GitHub Connection Status*\n\n✅ Connected\n\n🐙 *GitHub User:* `{github_username}`\n📂 *Default Repo:* `{github_repo}`\n📅 *Connected:* {auth_date[:10]}\n\n_To change repo: `set repo owner/repository`_\n_To disconnect: `disconnect github`_",
                    thread_ts=thread_ts
                )
            else:
                say(
                    text=f"<@{user_id}> ❌ Not connected to GitHub",
                    thread_ts=thread_ts
                )
            return
        
        # DISCONNECT GITHUB command
        elif re.search(r'\bdisconnect\s+github\b', clean_text):
            if auth_manager.disconnect_user(user_id):
                say(
                    text=f"<@{user_id}> 👋 Your GitHub account has been disconnected.\n\nTo use the bot again, you'll need to reconnect your GitHub account.",
                    thread_ts=thread_ts
                )
            else:
                say(
                    text=f"<@{user_id}> ⚠️ No GitHub account connected.",
                    thread_ts=thread_ts
                )
            return
        
        # Early command classification to check if repo is needed
        command = classify_command(message_text)
        
        # Handle commands that DON'T require a repo to be set
        if command["command"] == "CREATE_REPO":
            repo_name = command.get("repo_name")
            description = command.get("description")
            private = command.get("private", False)
            logger.info(f"🤖 AI detected CREATE_REPO command: {repo_name} (private={private})")
            handle_repo_create(user_id, repo_name, say, thread_ts, description=description, private=private)
            return
        
        if command["command"] == "VIEW_USAGE":
            logger.info(f"🤖 AI detected VIEW_USAGE command")
            say(
                text=f"<@{user_id}> 📊 *Your Usage Dashboard*\n\nView your activity, stats, and PR history:\n\n🔗 https://100286ffba51.ngrok-free.app/dashboard\n\n_See all your PRs, merge activity, and bot usage statistics_",
                thread_ts=thread_ts
            )
            return
        
        if command["command"] == "GENERAL":
            # Handle GENERAL command without requiring repo
            logger.info(f"🤖 Handling GENERAL command: {message_text}")
            _handle_general_command(user_id, message_text, say, thread_ts)
            return
        
        # Now check if user has set a repository for this channel (required for PR/merge commands)
        user_repo = auth_manager.get_user_repo(user_id, channel_id)
        if not user_repo or user_repo == "Not set":
            user_github_info = auth_manager.get_user_info(user_id)
            github_username = user_github_info.get("github_username", "Unknown")
            say(
                text=f"<@{user_id}> 📂 *Repository Not Set for This Channel*\n\n"
                     f"You're connected as GitHub user `{github_username}`, but you haven't set a repository for this channel yet.\n\n"
                     f"📝 Set your repo for this channel:\n"
                     f"```\n@bot set repo your-username/your-repository\n```\n\n"
                     f"Example: `@bot set repo octocat/Hello-World`\n\n"
                     f"💡 *Pro tip:* You can use different repos in different channels!",
                thread_ts=thread_ts
            )
            return
        
        # Check if this is a continuation of a PR conversation first
        if thread_ts in pr_conversations:
            logger.info(f"Continuing PR conversation in thread {thread_ts}")
            stored_channel_name = pr_conversations[thread_ts].get("channel_name") or channel_name
            handle_pr_conversation(
                user_id,
                message_text,
                say,
                thread_ts,
                client,
                channel_id,
                is_initial=False,
                image_data=image_data,
                channel_name=stored_channel_name,
            )
            return
        
        # Command was already classified early - use that result
        # Treat CREATE_PR and REFINE identically - both start PR conversations
        if command["command"] in ["CREATE_PR", "REFINE"]:
            # Extract task description (for CREATE_PR) or use the message as-is (for REFINE)
            task_description = command.get("task_description", message_text)
            logger.info(f"🤖 AI detected {command['command']} command: {task_description}")
            handle_pr_conversation(
                user_id,
                task_description,
                say,
                thread_ts,
                client,
                channel_id,
                is_initial=True,
                image_data=image_data,
                channel_name=channel_name,
            )
            return
            
        
        elif command["command"] == "MERGE_PR":
            pr_number = command.get("pr_number")
            merge_method = command.get("merge_method", "merge")
            logger.info(f"🤖 AI detected MERGE_PR command: PR #{pr_number} using {merge_method}")
            handle_pr_merge(user_id, pr_number, merge_method, say, thread_ts, channel_id)
            return
        
        elif command["command"] == "REVERT_PR":
            pr_number = command.get("pr_number")
            logger.info(f"🤖 AI detected REVERT_PR command: PR #{pr_number}")
            handle_pr_unmerge(user_id, pr_number, say, thread_ts, channel_id)
            return
        
        # CREATE_REPO, VIEW_USAGE, and GENERAL are handled earlier (before repo check)
        logger.info("Response sent successfully")
        
    except Exception as e:
        logger.error(f"Error handling app mention: {e}")
        say(
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("thread_ts")
        )


@app.action("make_pr_button")
def handle_make_pr_button_click(ack, body, client, logger):
    """
    Handle the Make PR button click
    """
    ack()  # Acknowledge the action
    
    try:
        user_id = body["user"]["id"]
        thread_ts = body["actions"][0]["value"]
        channel_id = body["channel"]["id"]
        
        logger.info(f"Make PR button clicked by {user_id} for thread {thread_ts}")
        
        # Check if conversation exists
        if thread_ts not in pr_conversations:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"<@{user_id}> ❌ Conversation not found. Please start a new PR request."
            )
            return
        
        # Get conversation data
        conv = pr_conversations[thread_ts]
        stored_user_id = conv["user_id"]
        stored_channel_id = conv.get("channel_id", channel_id)
        
        # Get per-user GitHub helper (channel-specific repo)
        user_github_helper = get_user_github_helper(stored_user_id, stored_channel_id)
        if not user_github_helper:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"<@{stored_user_id}> ❌ GitHub helper not available. Please check your connection."
            )
            return
        
        # Check if PR was already created (via text "make PR")
        if conv.get("pr_created"):
            result = conv.get("pr_result", {})
            if result.get("success"):
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=f"<@{stored_user_id}> ℹ️ This PR was already created!\n\n🔢 PR #: {result.get('pr_number')}\n🔗 URL: {result.get('pr_url')}"
                )
            else:
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=f"<@{stored_user_id}> ℹ️ PR creation was already attempted but failed. Please start a new conversation."
                )
            # Clean up now
            del pr_conversations[thread_ts]
            _save_pr_conversations()  # Save after cleanup
            return
        
        # Send acknowledgment
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"<@{stored_user_id}> ✅ Perfect! Creating the pull request now..."
        )
        
        # Get all conversation history
        all_messages = "\n\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conv["messages"]
        ])
        
        # Get the cached codebase context and files
        codebase_context = conv.get("codebase_context")
        cached_files = conv.get("cached_files", [])
        
        # Create the PR using cached files (no second AI call!)
        start_time = time.time()
        result = user_github_helper.create_random_pr(
            all_messages, 
            thread_context=thread_ts,
            codebase_context=codebase_context,
            cached_files=cached_files  # Use cached result from preview!
        )
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("success"):
            _record_pr_creation(thread_ts, result.get("pr_number"), processing_time_ms)
        
        # Send result
        if result["success"]:
            pr_number = result.get('pr_number')
            response = f"""<@{stored_user_id}> ✅ *Pull Request Created Successfully!*

📋 *Task:* {conv['initial_task']}
🔢 *PR #:* {pr_number}
🌿 *Branch:* `{result['branch_name']}`
🔗 *URL:* {result['pr_url']}

**Changes Made:**
{result.get('changes', 'See PR for details')}

You can now review and merge the PR!"""

            # Add merge button
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                }
            ]
            
            if pr_number:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔀 Merge PR",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"merge_pr_{pr_number}",
                            "action_id": f"merge_pr_button_{pr_number}"
                        }
                    ]
                })
                logger.info(f"Added Merge PR button for PR #{pr_number} in button handler")
            
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=response,
                blocks=blocks
            )
        else:
            response = f"""<@{stored_user_id}> ❌ *Failed to Create Pull Request*

*Task:* {conv['initial_task']}
*Error:* {result['error']}

You can retry by clicking the button below."""
            
            # Add retry button on failure
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔄 Retry PR Creation",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": thread_ts,
                            "action_id": "make_pr_button"
                        }
                    ]
                }
            ]
            
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=response,
                blocks=blocks
            )
            
            # DON'T delete conversation on failure - allow retry!
            logger.info(f"PR creation failed for thread {thread_ts}, keeping conversation for retry")
            return
        
        # Clean up the conversation only on SUCCESS
        del pr_conversations[thread_ts]
        _save_pr_conversations()  # Save after cleanup
        logger.info(f"Cleaned up conversation for thread {thread_ts}")
        
    except Exception as e:
        logger.error(f"Error handling Make PR button: {e}")
        try:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=body["actions"][0]["value"],
                text=f"❌ Error creating PR: {str(e)}"
            )
        except:
            pass


@app.action(re.compile("^merge_pr_button_.*"))
def handle_merge_pr_button_click(ack, body, client, say, logger):
    """
    Handle the Merge PR button click
    """
    ack()  # Acknowledge the action
    
    try:
        user_id = body["user"]["id"]
        action_value = body["actions"][0]["value"]
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        thread_ts = body["message"].get("thread_ts", message_ts)
        
        # Extract PR number from action value (format: "merge_pr_{pr_number}")
        pr_number = action_value.replace("merge_pr_", "")
        
        logger.info(f"Merge PR button clicked by {user_id} for PR #{pr_number}")
        
        # Send acknowledgment
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"<@{user_id}> 🔀 Merging PR #{pr_number}..."
        )
        
        # Use the existing merge function with default merge method
        def say_wrapper(text=None, thread_ts=None, blocks=None):
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=text,
                blocks=blocks
            )
        
        handle_pr_merge(user_id, pr_number, "merge", say_wrapper, thread_ts, channel_id)
        
    except Exception as e:
        logger.error(f"Error handling Merge PR button: {e}")
        try:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=body["message"].get("thread_ts", body["message"]["ts"]),
                text=f"<@{user_id}> ❌ Error merging PR: {str(e)}"
            )
        except:
            pass


@app.action(re.compile("^unmerge_pr_button_.*"))
def handle_unmerge_pr_button_click(ack, body, client, say, logger):
    """
    Handle the Unmerge PR button click
    """
    ack()  # Acknowledge the action
    
    try:
        user_id = body["user"]["id"]
        action_value = body["actions"][0]["value"]
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]
        thread_ts = body["message"].get("thread_ts", message_ts)
        
        # Extract PR number from action value (format: "unmerge_pr_{pr_number}")
        pr_number = action_value.replace("unmerge_pr_", "")
        
        logger.info(f"Unmerge PR button clicked by {user_id} for PR #{pr_number}")
        
        # Send acknowledgment
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"<@{user_id}> ↩️ Creating revert PR for #{pr_number}..."
        )
        
        # Use the existing unmerge function
        def say_wrapper(text=None, thread_ts=None, blocks=None):
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=text,
                blocks=blocks
            )
        
        handle_pr_unmerge(user_id, pr_number, say_wrapper, thread_ts, channel_id)
        
    except Exception as e:
        logger.error(f"Error handling Unmerge PR button: {e}")
        try:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                thread_ts=body["message"].get("thread_ts", body["message"]["ts"]),
                text=f"<@{user_id}> ❌ Error unmerging PR: {str(e)}"
            )
        except:
            pass


@app.event("message")
def handle_message_events(event, say, client, logger):
    """
    Handle message events - check if it's a reply in an active PR conversation thread
    """
    logger.info("=" * 80)
    logger.info("🔔 MESSAGE EVENT HANDLER TRIGGERED")
    logger.info("=" * 80)
    logger.info(f"📨 Full event data: {event}")
    logger.info(f"   Channel: {event.get('channel')}")
    logger.info(f"   Channel Type: {event.get('channel_type')}")
    logger.info(f"   User: {event.get('user')}")
    logger.info(f"   Text: {event.get('text', '')}")
    logger.info(f"   Message TS: {event.get('ts')}")
    logger.info(f"   Thread TS: {event.get('thread_ts')}")
    logger.info(f"   Parent User ID: {event.get('parent_user_id')}")
    logger.info(f"   Subtype: {event.get('subtype')}")
    logger.info(f"   Bot ID: {event.get('bot_id')}")
    logger.info(f"   Bot Profile: {event.get('bot_profile')}")
    logger.info(f"   Event Type: {event.get('type')}")
    logger.info(f"   Event Subtype: {event.get('event_subtype')}")
    logger.info(f"   📚 Active conversations: {list(pr_conversations.keys())}")
    logger.info("=" * 80)
    
    # Ignore bot messages
    if event.get("subtype") == "bot_message" or event.get("bot_id"):
        logger.warning("⏭️  IGNORING: This is a bot message")
        return
    
    # Check if this is in a thread with an active conversation
    thread_ts = event.get("thread_ts")
    
    if not thread_ts:
        logger.warning("⏭️  IGNORING: Not in a thread (thread_ts is None)")
        logger.info(f"   This appears to be a top-level message (ts={event.get('ts')})")
        return
    
    logger.info(f"✅ This IS a thread reply! Thread TS: {thread_ts}")
    
    # Check if this thread has an active PR conversation
    if thread_ts not in pr_conversations:
        logger.warning(f"⏭️  IGNORING: Thread {thread_ts} is NOT in active conversations")
        logger.info(f"   Available conversation threads: {list(pr_conversations.keys())}")
        logger.info(f"   Thread exists but not tracked - this is a reply to some other thread")
        return
    
    logger.info("🎯 MATCH! This is a reply in an ACTIVE PR conversation!")
    logger.info(f"   Conversation data: {pr_conversations[thread_ts]}")
    
    # This is a reply in an active PR conversation!
    user_id = event.get("user")
    message_text = event.get("text", "")
    channel_id = event.get("channel")
    channel_name = pr_conversations[thread_ts].get("channel_name")
    
    logger.info(f"   ✅ Processing message in PR conversation thread!")
    logger.info("=" * 80)
    logger.info("🚀 CALLING handle_pr_conversation")
    logger.info("=" * 80)
    logger.info(f"   User ID: {user_id}")
    logger.info(f"   Message: {message_text}")
    logger.info(f"   Thread TS: {thread_ts}")
    logger.info(f"   Channel: {channel_id}")
    logger.info(f"   Is Initial: False (this is a follow-up)")
    logger.info("=" * 80)
    
    # Handle the conversation
    try:
        handle_pr_conversation(
            user_id,
            message_text,
            say,
            thread_ts,
            client,
            channel_id,
            is_initial=False,
            channel_name=channel_name,
        )
        logger.info("✅ handle_pr_conversation completed successfully")
    except Exception as e:
        logger.error(f"❌ handle_pr_conversation failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())


# Start the app
# ============================================================================
# Flask OAuth Callback Routes
# ============================================================================

@flask_app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return """
        <html>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>❌ Authentication Failed</h1>
                <p>Missing code or state parameter</p>
            </body>
        </html>
        """, 400
    
    # Handle the OAuth callback (synchronous call)
    result = asyncio.run(auth_manager.handle_oauth_callback(code, state))
    
    if result["success"]:
        github_username = result["github_username"]
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px;
                        text-align: center;
                        color: white;
                    }}
                    .container {{
                        background: white;
                        color: #333;
                        padding: 40px;
                        border-radius: 12px;
                        max-width: 500px;
                        margin: 0 auto;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    }}
                    h1 {{ color: #4CAF50; margin-bottom: 10px; }}
                    .username {{ 
                        background: #f0f0f0;
                        padding: 10px 20px;
                        border-radius: 20px;
                        display: inline-block;
                        margin: 20px 0;
                        font-weight: bold;
                    }}
                    .next-steps {{
                        text-align: left;
                        background: #f9f9f9;
                        padding: 20px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }}
                    .next-steps li {{ margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Successfully Connected!</h1>
                    <p>Your GitHub account has been linked to the Slack bot.</p>
                    <div class="username">🐙 {github_username}</div>
                    
                    <div class="next-steps">
                        <h3>📋 Next Steps:</h3>
                        <ol>
                            <li>Go back to Slack</li>
                            <li>Mention the bot: <code>@bot set repo owner/repository</code></li>
                            <li>Start creating PRs: <code>@bot create a login page</code></li>
                        </ol>
                    </div>
                    
                    <p style="margin-top: 30px; color: #888; font-size: 14px;">
                        You can close this window now
                    </p>
                </div>
            </body>
        </html>
        """
    else:
        error = result.get("error", "Unknown error")
        return f"""
        <html>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>❌ Authentication Failed</h1>
                <p>{error}</p>
            </body>
        </html>
        """, 400


@flask_app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "slack-bot-with-oauth"}


def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.environ.get("OAUTH_PORT", 5050))
    logger.info(f"🔐 Starting OAuth callback server on port {port}...")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        # Get the App-Level Token for Socket Mode
        app_token = os.environ.get("SLACK_APP_TOKEN")
        
        if not app_token:
            raise ValueError("SLACK_APP_TOKEN not found in environment variables")
        
        if not os.environ.get("SLACK_BOT_TOKEN"):
            raise ValueError("SLACK_BOT_TOKEN not found in environment variables")
        
        # Start Flask OAuth server in background thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info("=" * 60)
        logger.info("🚀 Slack Bot with GitHub OAuth + REST API")
        logger.info("=" * 60)
        logger.info("📍 OAuth Callback: http://localhost:5050/auth/github/callback")
        logger.info("🏥 Health Check: http://localhost:5050/health")
        logger.info("📡 REST API: http://localhost:5050/api/v1/")
        logger.info("   POST /api/v1/chat - Send message, get AI response")
        logger.info("   POST /api/v1/threads - Create conversation thread")
        logger.info("   GET  /api/v1/threads - List threads")
        logger.info("🔑 API Key: Set BOT_API_KEY env variable for API access")
        logger.info("⚡️ Slack Bot: Starting Socket Mode...")
        logger.info("=" * 60)
            
        # Start the Socket Mode handler
        handler = SocketModeHandler(app, app_token)
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

