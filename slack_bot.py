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

# Store ongoing conversations for PR creation
# Format: {thread_ts: conversation_data}
pr_conversations = {}

def is_ready_to_create_pr(message_text):
    """
    Detect if user wants to create the PR now
    
    Args:
        message_text: User's message
        
    Returns:
        bool: True if user wants to create PR
    """
    create_pr_phrases = [
        "make pr",
        "create pr",
        "make the pr",
        "create the pr",
        "go ahead",
        "proceed",
        "looks good",
        "sounds good",
        "let's do it",
        "do it",
        "create it"
    ]
    
    text_lower = message_text.lower()
    return any(phrase in text_lower for phrase in create_pr_phrases)


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

# Initialize GitHub helper (if token is available)
github_helper = None
if os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"):
    try:
        # Check if AI code generation should be enabled
        use_ai = os.environ.get("USE_AI_CODE_GENERATION", "true").lower() == "true"
        
        github_helper = GitHubPRHelper(
            github_token=os.environ.get("GITHUB_TOKEN"),
            repo_name=os.environ.get("GITHUB_REPO"),
            use_ai=use_ai
        )
        logger.info(f"GitHub integration enabled (AI code generation: {use_ai})")
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


def handle_pr_conversation(user_id, message_text, say, thread_ts, client=None, channel_id=None, is_initial=False):
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
    """
    if not github_helper:
        say(
            text=f"Sorry <@{user_id}>, GitHub integration is not configured.",
            thread_ts=thread_ts
        )
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
            "plan": None,
            "codebase_context": None  # Will be fetched once and cached
        }
    
    # Always use the stored user_id to tag
    stored_user_id = pr_conversations[conversation_key]["user_id"]
    
    # Add user message to history
    pr_conversations[conversation_key]["messages"].append({
        "role": "user",
        "content": message_text
    })
    
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
        
        result = github_helper.create_random_pr(all_messages)
        _send_pr_result(result, pr_conversations[conversation_key]["initial_task"], say, thread_ts, stored_user_id)
        
        # Clean up
        del pr_conversations[conversation_key]
        return
    
    # Send initial message for new conversations
    if is_initial:
        say(
            text=f"<@{stored_user_id}> 🤖 I'll propose a changeset for:\n> {message_text}\n\n📚 Reading codebase and generating changes...",
            thread_ts=thread_ts
        )
    
    # Check if AI is available
    if not github_helper.use_ai or not github_helper.ai_generator:
        say(
            text=f"<@{stored_user_id}> AI not available. Say **'make PR'** when you want me to create a placeholder PR.",
            thread_ts=thread_ts
        )
        return
    
    # Get AI response
    try:
        # Fetch codebase context once and cache it
        if pr_conversations[conversation_key]["codebase_context"] is None:
            logger.info("Fetching full codebase context for conversation...")
            say(
                text=f"<@{stored_user_id}> 📚 Reading full codebase...",
                thread_ts=thread_ts
            )
            try:
                # Get the default branch
                default_branch = github_helper.repo.default_branch
                codebase_context = github_helper._get_full_codebase_context(default_branch)
                pr_conversations[conversation_key]["codebase_context"] = codebase_context
                logger.info(f"Codebase context cached: {len(codebase_context)} chars")
            except Exception as e:
                logger.error(f"Error fetching codebase context: {e}")
                pr_conversations[conversation_key]["codebase_context"] = f"Repository: {github_helper.repo_name}\n\nError reading codebase: {str(e)}"
        
        # Build conversation context
        conversation_history = pr_conversations[conversation_key]["messages"]
        full_context = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        
        # Use AI to propose concrete changes
        # Make the prompt very explicit about changeset format
        planning_prompt = f"""You are reviewing the FULL CODEBASE and proposing changes.

CONVERSATION:
{full_context}

YOUR TASK: Output a CONCRETE CHANGESET showing EXACTLY what code you will create or modify.

REQUIRED FORMAT (follow this structure EXACTLY):

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **CHANGESET SUMMARY**
Brief overview of what this changeset accomplishes

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 **File: path/to/file1.py** [NEW] or [MODIFIED]

```python
# Complete, working code here
def example_function():
    # Full implementation, not a stub
    return "actual code"
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 **File: path/to/file2.py** [NEW] or [MODIFIED]

```python
# Complete, working code here
class ExampleClass:
    def __init__(self):
        # Full implementation
        pass
```

━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
1. Show COMPLETE, WORKING CODE - no placeholders like "# implementation here"
2. Use the file paths, imports, and patterns from the CODEBASE CONTEXT you have
3. NO questions - only propose concrete code
4. If you make assumptions, state them in 1 line then show code
5. EVERY file must have complete implementation
6. Match the existing code style from the repository

User will provide feedback to modify this changeset.
"""
        
        # Use the cached full codebase context
        full_codebase_context = pr_conversations[conversation_key]["codebase_context"]
        
        ai_result = github_helper.ai_generator.generate_code_sync(
            task_description=planning_prompt,
            context=full_codebase_context
        )
        
        if not ai_result.get("success"):
            say(
                text=f"<@{stored_user_id}> ❌ AI error: {ai_result.get('error')}",
                thread_ts=thread_ts
            )
            return
        
        ai_response = ai_result.get("raw_response", "")
        
        # Store AI response
        pr_conversations[conversation_key]["messages"].append({
            "role": "assistant",
            "content": ai_response
        })
        
        # Format as a clear changeset
        formatted_response, file_count = format_changeset_response(ai_response, is_initial=is_initial)
        
        # Truncate if too long for Slack (3000 char limit)
        display_response = formatted_response
        if len(formatted_response) > 2800:
            # Find the summary footer
            footer_match = re.search(r'\n━+\n📊.*$', formatted_response, re.DOTALL)
            footer = footer_match.group(0) if footer_match else ""
            
            # Truncate but keep footer
            truncated_length = len(formatted_response) - 2800
            display_response = formatted_response[:2800] + f"\n\n...(truncated, {truncated_length} more chars)\n" + footer
        
        # Send response with button and clear visual structure
        say(
            text=f"<@{stored_user_id}> {display_response}",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{'🆕 ' if is_initial else '🔄 '}Proposed Changeset ({file_count} file{'s' if file_count != 1 else ''})",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{stored_user_id}>\n\n{display_response}"
                    }
                },
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
                            "text": "💬 _Reply with feedback to modify this changeset_ • 🚀 _Click button to create PR_"
                        }
                    ]
                }
            ],
            thread_ts=thread_ts
        )
        
    except Exception as e:
        logger.error(f"Error in PR conversation: {e}")
        say(
            text=f"<@{stored_user_id}> ❌ Error: {str(e)}",
            thread_ts=thread_ts
        )


def _send_pr_result(result, task_description, say, thread_ts, user_id):
    """Helper to send PR creation result"""
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
            logger.info(f"PR conversation started: {pr_check['task_description']}")
            handle_pr_conversation(user_id, pr_check['task_description'], say, thread_ts, client, channel_id, is_initial=True)
            return
        
        # Check if this is a continuation of a PR conversation
        if thread_ts in pr_conversations:
            logger.info(f"Continuing PR conversation in thread {thread_ts}")
            handle_pr_conversation(user_id, message_text, say, thread_ts, client, channel_id, is_initial=False)
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


@app.action("make_pr_button")
def handle_make_pr_button(ack, body, client, logger):
    """
    Handle the Make PR button click
    """
    ack()  # Acknowledge the action
    
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
    
    # Create the PR
    result = github_helper.create_random_pr(all_messages)
    
    # Send result
    if result["success"]:
        response = f"""<@{stored_user_id}> ✅ *Pull Request Created Successfully!*

📋 *Task:* {conv['initial_task']}
🔢 *PR #:* {result['pr_number']}
🌿 *Branch:* `{result['branch_name']}`
🔗 *URL:* {result['pr_url']}

📝 *Changes:* {result['changes']}

The PR is ready for review! 🎉

💡 *Tip:* You can merge it with `@bot merge PR {result['pr_number']}`
"""
    else:
        response = f"""<@{stored_user_id}> ❌ *Failed to Create Pull Request*

*Error:* {result['error']}

Please check the logs and try again.
"""
    
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=response
    )
    
    # Clean up conversation
    del pr_conversations[thread_ts]


@app.event("message")
def handle_message_events(event, say, client, logger):
    """
    Handle message events - check if it's a reply in an active PR conversation thread
    """
    logger.info(f"📨 Message event received: {event}")
    logger.info(f"   User: {event.get('user')}")
    logger.info(f"   Text: {event.get('text', '')[:100]}")
    logger.info(f"   Thread: {event.get('thread_ts')}")
    logger.info(f"   Subtype: {event.get('subtype')}")
    logger.info(f"   Bot ID: {event.get('bot_id')}")
    logger.info(f"   Active conversations: {list(pr_conversations.keys())}")
    
    # Ignore bot messages
    if event.get("subtype") == "bot_message" or event.get("bot_id"):
        logger.info("   ⏭️  Ignoring: bot message")
        return
    
    # Check if this is in a thread with an active conversation
    thread_ts = event.get("thread_ts")
    
    if not thread_ts:
        logger.info("   ⏭️  Ignoring: not in a thread")
        return
    
    # Check if this thread has an active PR conversation
    if thread_ts not in pr_conversations:
        logger.info(f"   ⏭️  Ignoring: thread {thread_ts} not in active conversations")
        return
    
    # This is a reply in an active PR conversation!
    user_id = event.get("user")
    message_text = event.get("text", "")
    channel_id = event.get("channel")
    
    logger.info(f"   ✅ Processing message in PR conversation thread!")
    
    # Handle the conversation
    handle_pr_conversation(user_id, message_text, say, thread_ts, client, channel_id, is_initial=False)


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

