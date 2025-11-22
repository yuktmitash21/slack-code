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

# Initialize GitHub helper (if token is available)
github_helper = None
if os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"):
    try:
        github_helper = GitHubPRHelper(
            github_token=os.environ.get("GITHUB_TOKEN"),
            repo_name=os.environ.get("GITHUB_REPO")
        )
        logger.info("GitHub integration enabled")
    except Exception as e:
        logger.warning(f"GitHub integration failed to initialize: {e}")
else:
    logger.info("GitHub integration disabled (no token/repo configured)")


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


def detect_pr_command(message_text):
    """
    Detect if the message contains a PR creation command
    
    Returns:
        dict with 'is_pr_command' and 'task_description' or None
    """
    # Remove bot mention from text
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip()
    
    # Check for PR-related keywords
    pr_keywords = [
        r'create\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'make\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'open\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'submit\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'generate\s+(?:a\s+)?(?:pull\s+request|pr)',
    ]
    
    for pattern in pr_keywords:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            # Extract task description (everything after the command)
            task_description = clean_text[match.end():].strip()
            
            # Also look for "for" or "to" followed by description
            for_match = re.search(r'(?:for|to)\s+(.+)', task_description, re.IGNORECASE)
            if for_match:
                task_description = for_match.group(1).strip()
            
            return {
                'is_pr_command': True,
                'task_description': task_description or "No specific task description provided"
            }
    
    return {'is_pr_command': False}


def detect_merge_command(message_text):
    """
    Detect if the message contains a merge PR command
    
    Returns:
        dict with 'is_merge_command', 'pr_number', and 'merge_method'
    """
    # Remove bot mention from text
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip()
    
    # Check for merge-related keywords with PR number
    merge_patterns = [
        r'merge\s+(?:pr|pull\s+request|#)\s*(\d+)',
        r'merge\s+(\d+)',
    ]
    
    for pattern in merge_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            pr_number = match.group(1)
            
            # Check for merge method
            merge_method = "merge"  # default
            if re.search(r'\bsquash\b', clean_text, re.IGNORECASE):
                merge_method = "squash"
            elif re.search(r'\brebase\b', clean_text, re.IGNORECASE):
                merge_method = "rebase"
            
            return {
                'is_merge_command': True,
                'pr_number': pr_number,
                'merge_method': merge_method
            }
    
    return {'is_merge_command': False}


def detect_unmerge_command(message_text):
    """
    Detect if the message contains an unmerge/revert PR command
    
    Returns:
        dict with 'is_unmerge_command' and 'pr_number'
    """
    # Remove bot mention from text
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip()
    
    # Check for unmerge/revert-related keywords with PR number
    unmerge_patterns = [
        r'(?:unmerge|revert)\s+(?:pr|pull\s+request|#)\s*(\d+)',
        r'(?:unmerge|revert)\s+(\d+)',
    ]
    
    for pattern in unmerge_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            pr_number = match.group(1)
            
            return {
                'is_unmerge_command': True,
                'pr_number': pr_number
            }
    
    return {'is_unmerge_command': False}


def handle_pr_creation(user_id, task_description, say, thread_ts):
    """
    Handle the creation of a GitHub pull request
    
    Args:
        user_id: Slack user ID
        task_description: Description of the task
        say: Slack say function
        thread_ts: Thread timestamp
    """
    if not github_helper:
        say(
            text=f"Sorry <@{user_id}>, GitHub integration is not configured. Please add GITHUB_TOKEN and GITHUB_REPO to your .env file.",
            thread_ts=thread_ts
        )
        return
    
    # Send acknowledgment
    say(
        text=f"🤖 Got it <@{user_id}>! Creating a pull request for: *{task_description}*\n\nPlease wait...",
        thread_ts=thread_ts
    )
    
    # Create the PR
    result = github_helper.create_random_pr(task_description)
    
    if result["success"]:
        response = f"""✅ *Pull Request Created Successfully!*

📋 *Task:* {task_description}
🔢 *PR #:* {result['pr_number']}
🌿 *Branch:* `{result['branch_name']}`
🔗 *URL:* {result['pr_url']}

📝 *Changes:* {result['changes']}

The PR is ready for review! 🎉

💡 *Tip:* You can merge it with `@bot merge PR {result['pr_number']}`
"""
    else:
        response = f"""❌ *Failed to Create Pull Request*

*Task:* {task_description}
*Error:* {result['error']}

Please check the logs and try again.
"""
    
    say(
        text=response,
        thread_ts=thread_ts
    )


def handle_pr_merge(user_id, pr_number, merge_method, say, thread_ts):
    """
    Handle merging a GitHub pull request
    
    Args:
        user_id: Slack user ID
        pr_number: PR number to merge
        merge_method: Method to use for merging (merge, squash, rebase)
        say: Slack say function
        thread_ts: Thread timestamp
    """
    if not github_helper:
        say(
            text=f"Sorry <@{user_id}>, GitHub integration is not configured. Please add GITHUB_TOKEN and GITHUB_REPO to your .env file.",
            thread_ts=thread_ts
        )
        return
    
    # Send acknowledgment
    say(
        text=f"🔄 Got it <@{user_id}>! Merging PR #{pr_number} using {merge_method} method...\n\nPlease wait...",
        thread_ts=thread_ts
    )
    
    # Merge the PR
    result = github_helper.merge_pr(pr_number, merge_method)
    
    if result["success"]:
        response = f"""✅ *Pull Request Merged Successfully!*

🔢 *PR #:* {result['pr_number']}
📋 *Title:* {result['pr_title']}
🌿 *Branch:* `{result['branch_name']}`
🔀 *Merge Method:* {result['merge_method']}
🔗 *URL:* {result['pr_url']}

The changes have been merged to master! 🎉

💡 *Tip:* If you need to undo this, use `@bot unmerge PR {result['pr_number']}`
"""
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


def handle_pr_unmerge(user_id, pr_number, say, thread_ts):
    """
    Handle creating a revert PR for a merged pull request
    
    Args:
        user_id: Slack user ID
        pr_number: PR number to revert
        say: Slack say function
        thread_ts: Thread timestamp
    """
    if not github_helper:
        say(
            text=f"Sorry <@{user_id}>, GitHub integration is not configured. Please add GITHUB_TOKEN and GITHUB_REPO to your .env file.",
            thread_ts=thread_ts
        )
        return
    
    # Send acknowledgment
    say(
        text=f"🔄 Got it <@{user_id}>! Creating a revert PR for #{pr_number}...\n\nPlease wait...",
        thread_ts=thread_ts
    )
    
    # Create the revert PR
    result = github_helper.create_revert_pr(pr_number)
    
    if result["success"]:
        response = f"""✅ *Revert Pull Request Created Successfully!*

🔄 *Reverting PR #:* {result['original_pr_number']}
📋 *Original Title:* {result['original_pr_title']}
🔗 *Original PR:* {result['original_pr_url']}

**New Revert PR:**
🔢 *PR #:* {result['revert_pr_number']}
🌿 *Branch:* `{result['revert_branch_name']}`
🔗 *URL:* {result['revert_pr_url']}

The revert PR is ready for review! You can now merge it to undo the original changes.

💡 *Tip:* Merge it with `@bot merge PR {result['revert_pr_number']}`
"""
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
        
        # Get user info
        user_info = client.users_info(user=user_id)
        username = user_info["user"]["real_name"] or user_info["user"]["name"]
        
        # Check if this is a PR creation command
        pr_check = detect_pr_command(message_text)
        
        if pr_check['is_pr_command']:
            logger.info(f"PR creation requested: {pr_check['task_description']}")
            handle_pr_creation(user_id, pr_check['task_description'], say, thread_ts)
            return
        
        # Check if this is a merge PR command
        merge_check = detect_merge_command(message_text)
        
        if merge_check['is_merge_command']:
            logger.info(f"PR merge requested: PR #{merge_check['pr_number']} using {merge_check['merge_method']}")
            handle_pr_merge(user_id, merge_check['pr_number'], merge_check['merge_method'], say, thread_ts)
            return
        
        # Check if this is an unmerge/revert PR command
        unmerge_check = detect_unmerge_command(message_text)
        
        if unmerge_check['is_unmerge_command']:
            logger.info(f"PR revert requested: PR #{unmerge_check['pr_number']}")
            handle_pr_unmerge(user_id, unmerge_check['pr_number'], say, thread_ts)
            return
        
        # Regular context response
        # Gather context from the channel
        channel_context = get_channel_context(client, channel_id, limit=50)
        
        # If in a thread, also get thread context
        thread_context = []
        if thread_ts and thread_ts != event.get("ts"):
            thread_context = get_thread_context(client, channel_id, thread_ts)
        
        # Build context summary
        context_summary = []
        
        if thread_context and len(thread_context) > 1:
            context_summary.append("📝 *Thread Context:*")
            # Show last 10 messages from thread
            for msg in thread_context[-10:]:
                context_summary.append(f"  {msg}")
            context_summary.append("")
        
        context_summary.append("📚 *Recent Channel Messages:*")
        # Show last 30 messages from channel
        for msg in channel_context[-30:]:
            context_summary.append(f"  {msg}")
        
        # Create response with help text
        response = f"Hi <@{user_id}>! I've been mentioned and I have context from the channel.\n\n"
        response += f"*Your message:* {message_text}\n\n"
        response += "\n".join(context_summary)
        response += f"\n\n_I have access to the last {len(channel_context)} messages from this channel"
        if thread_context:
            response += f" and {len(thread_context)} messages from this thread"
        response += "._"
        
        # Add GitHub PR help if enabled
        if github_helper:
            response += "\n\n💡 *Tips:*"
            response += "\n• Create a PR: `create a PR for [task description]`"
            response += "\n• Merge a PR: `merge PR [number]`"
            response += "\n• Revert a PR: `unmerge PR [number]`"
        
        # Send response in the same thread if applicable
        say(
            text=response,
            thread_ts=thread_ts
        )
        
        logger.info("Response sent successfully")
        
    except Exception as e:
        logger.error(f"Error handling app mention: {e}")
        say(
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("thread_ts")
        )


@app.event("message")
def handle_message_events(body, logger):
    """
    Handle message events (for logging or additional processing).
    Note: This will capture all messages in channels the bot is in.
    """
    logger.debug(f"Message event received: {body.get('event', {}).get('type')}")


# Start the app
if __name__ == "__main__":
    try:
        # Get the App-Level Token for Socket Mode
        app_token = os.environ.get("SLACK_APP_TOKEN")
        
        if not app_token:
            raise ValueError("SLACK_APP_TOKEN not found in environment variables")
        
        if not os.environ.get("SLACK_BOT_TOKEN"):
            raise ValueError("SLACK_BOT_TOKEN not found in environment variables")
            
        logger.info("⚡️ Starting Slack bot in Socket Mode...")
        
        # Start the Socket Mode handler
        handler = SocketModeHandler(app, app_token)
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

