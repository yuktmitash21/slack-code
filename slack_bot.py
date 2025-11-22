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
            response += "\n\n💡 *Tip:* You can ask me to `create a PR for [task description]` to generate a pull request!"
        
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

