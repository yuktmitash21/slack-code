"""
Intent Classification Module

Uses AI to intelligently classify user intent for all bot commands.
Handles PR creation, merging, reverting, and conversational refinement.
"""

import os
import logging
import re
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def classify_user_intent(message_text: str) -> str:
    """
    Use AI to intelligently classify user intent
    
    Args:
        message_text: User's message
        
    Returns:
        str: "SUBMIT" if user wants to create PR, "REFINE" if they want to iterate
    """
    try:
        import openai
        
        # Use a small, fast model for intent classification
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for classification
            messages=[
                {
                    "role": "system",
                    "content": """You are an intent classifier for a coding assistant bot.

Your task: Determine if the user wants to SUBMIT/CREATE a Pull Request NOW, or if they want to REFINE/ITERATE on the proposed code changes.

Respond with EXACTLY one word:
- "SUBMIT" if they want to create the PR now (e.g., "make pr", "create pr", "submit it", "go ahead", "looks good let's merge")
- "REFINE" if they want to change/improve the code (e.g., "add tests", "do it in one file", "make it faster", "can you change X")

Examples:
User: "make pr" → SUBMIT
User: "create the pr" → SUBMIT
User: "looks good, submit it" → SUBMIT
User: "go ahead" → SUBMIT
User: "Can you do it all in one file?" → REFINE
User: "Add error handling" → REFINE
User: "looks good but add tests" → REFINE
User: "make it use TypeScript instead" → REFINE"""
                },
                {
                    "role": "user",
                    "content": f"User message: \"{message_text}\"\n\nIntent:"
                }
            ],
            temperature=0,
            max_tokens=5
        )
        
        intent = response.choices[0].message.content.strip().upper()
        logger.info(f"🤖 Intent classification: '{message_text}' → {intent}")
        
        return intent
        
    except Exception as e:
        logger.error(f"Error in AI intent classification: {e}")
        # Fallback to regex patterns if AI fails
        return classify_with_regex_fallback(message_text)


def classify_with_regex_fallback(message_text: str) -> str:
    """
    Fallback to regex patterns if AI classification fails
    
    Args:
        message_text: User's message
        
    Returns:
        str: "SUBMIT" or "REFINE"
    """
    create_pr_patterns = [
        r'\bmake\s+(?:the\s+)?pr\b',
        r'\bcreate\s+(?:the\s+)?pr\b',
        r'\bopen\s+(?:the\s+)?pr\b',
        r'\bsubmit\s+(?:the\s+)?pr\b',
    ]
    
    text_lower = message_text.lower().strip()
    for pattern in create_pr_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"🔁 Fallback regex matched: {pattern}")
            return "SUBMIT"
    
    return "REFINE"


def is_ready_to_create_pr(message_text: str) -> bool:
    """
    Determine if user wants to create the PR now
    
    Args:
        message_text: User's message
        
    Returns:
        bool: True if user wants to create PR
    """
    intent = classify_user_intent(message_text)
    return intent == "SUBMIT"


def classify_command(message_text: str) -> Dict:
    """
    Use AI to classify the command type and extract parameters
    
    Args:
        message_text: User's message (cleaned, without bot mention)
        
    Returns:
        dict with command type and parameters:
        {
            "command": "CREATE_PR" | "MERGE_PR" | "REVERT_PR" | "CREATE_REPO" | "VIEW_USAGE" | "REFINE" | "GENERAL",
            "task_description": str (for CREATE_PR),
            "pr_number": str (for MERGE_PR, REVERT_PR),
            "merge_method": "merge" | "squash" | "rebase" (for MERGE_PR),
            "repo_name": str (for CREATE_REPO),
            "description": str (for CREATE_REPO, optional),
            "private": bool (for CREATE_REPO, default False)
        }
    """
    try:
        import openai
        
        # Clean text (remove bot mentions)
        clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip()
        
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a command classifier for a GitHub/Slack bot.

Classify user commands into these categories and extract parameters:

1. CREATE_PR - User explicitly asks to create a pull request with specific task
   Examples: "create a PR to add login", "make pr for auth feature"
   Extract: task_description

2. REFINE - User describes a coding task without explicitly saying "PR" (treated same as CREATE_PR)
   Examples: "add a login page", "create authentication", "add tests", "make it faster"
   This is for any request to write/modify code
   No extraction needed (the whole message is the task)

3. MERGE_PR - User wants to merge an existing PR
   Examples: "merge PR 123", "merge #45 using squash", "merge 12"
   Extract: pr_number (just the number), merge_method ("merge", "squash", or "rebase")

4. REVERT_PR - User wants to revert/undo a merged PR
   Examples: "revert PR 123", "unmerge #45", "revert 12"
   Extract: pr_number (just the number)

5. CREATE_REPO - User wants to create a new GitHub repository
   Examples: "create a new repo called my-app", "make a repository named test-project", "new repo my-project", "create empty repo foo-bar", "spin up a new repository", "initialize a repo called demo"
   Extract: repo_name (the name of the repository to create), description (optional description), private (boolean, true if user says private)
   
6. VIEW_USAGE - User wants to view their usage statistics or dashboard
   Examples: "show my usage", "view stats", "dashboard", "my activity", "usage report"
   No parameters needed

7. GENERAL - General question or conversation (NOT a coding task)
   Examples: "what can you do?", "help", "hello", "how are you"
   No parameters needed

Respond with ONLY valid JSON in this format:
{
    "command": "CREATE_PR" | "MERGE_PR" | "REVERT_PR" | "CREATE_REPO" | "VIEW_USAGE" | "REFINE" | "GENERAL",
    "task_description": "extracted description" (only for CREATE_PR),
    "pr_number": "123" (only for MERGE_PR or REVERT_PR, number as string),
    "merge_method": "merge" | "squash" | "rebase" (only for MERGE_PR, default "merge"),
    "repo_name": "my-repo-name" (only for CREATE_REPO),
    "description": "optional description" (only for CREATE_REPO, optional),
    "private": true | false (only for CREATE_REPO, default false)
}

Examples:
"create a PR to add login page" → {"command": "CREATE_PR", "task_description": "add login page"}
"add a login page" → {"command": "REFINE"}
"create authentication system" → {"command": "REFINE"}
"add error handling" → {"command": "REFINE"}
"merge PR 123" → {"command": "MERGE_PR", "pr_number": "123", "merge_method": "merge"}
"merge #45 with squash" → {"command": "MERGE_PR", "pr_number": "45", "merge_method": "squash"}
"revert PR 12" → {"command": "REVERT_PR", "pr_number": "12"}
"create a new repo called my-app" → {"command": "CREATE_REPO", "repo_name": "my-app", "private": false}
"make a private repository named secret-project" → {"command": "CREATE_REPO", "repo_name": "secret-project", "private": true}
"new repo test-project for testing stuff" → {"command": "CREATE_REPO", "repo_name": "test-project", "description": "for testing stuff", "private": false}
"show my usage" → {"command": "VIEW_USAGE"}
"dashboard" → {"command": "VIEW_USAGE"}
"what can you do?" → {"command": "GENERAL"}
"hello" → {"command": "GENERAL"}"""
                },
                {
                    "role": "user",
                    "content": f"User message: \"{clean_text}\"\n\nClassify and extract:"
                }
            ],
            temperature=0,
            max_tokens=100
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        result = json.loads(result_text)
        logger.info(f"🤖 Command classification: '{clean_text}' → {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in AI command classification: {e}")
        # Fallback to regex-based detection
        return classify_command_with_regex(message_text)


def classify_command_with_regex(message_text: str) -> Dict:
    """
    Fallback regex-based command classification
    
    Args:
        message_text: User's message
        
    Returns:
        dict with command type and parameters
    """
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', message_text).strip()
    
    # Check for MERGE_PR
    merge_patterns = [
        r'merge\s+(?:pr|pull\s+request|#)?\s*(\d+)',
    ]
    for pattern in merge_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            pr_number = match.group(1)
            merge_method = "merge"
            if re.search(r'\bsquash\b', clean_text, re.IGNORECASE):
                merge_method = "squash"
            elif re.search(r'\brebase\b', clean_text, re.IGNORECASE):
                merge_method = "rebase"
            logger.info(f"🔁 Fallback: MERGE_PR detected - PR #{pr_number}")
            return {
                "command": "MERGE_PR",
                "pr_number": pr_number,
                "merge_method": merge_method
            }
    
    # Check for REVERT_PR
    revert_patterns = [
        r'(?:unmerge|revert)\s+(?:pr|pull\s+request|#)?\s*(\d+)',
    ]
    for pattern in revert_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            pr_number = match.group(1)
            logger.info(f"🔁 Fallback: REVERT_PR detected - PR #{pr_number}")
            return {
                "command": "REVERT_PR",
                "pr_number": pr_number
            }
    
    # Check for CREATE_PR
    pr_keywords = [
        r'create\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'make\s+(?:a\s+)?(?:pull\s+request|pr)',
        r'open\s+(?:a\s+)?(?:pull\s+request|pr)',
    ]
    for pattern in pr_keywords:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            task_description = clean_text[match.end():].strip()
            for_match = re.search(r'(?:for|to)\s+(.+)', task_description, re.IGNORECASE)
            if for_match:
                task_description = for_match.group(1).strip()
            logger.info(f"🔁 Fallback: CREATE_PR detected")
            return {
                "command": "CREATE_PR",
                "task_description": task_description or "No specific task description provided"
            }
    
    # Check for CREATE_REPO
    repo_patterns = [
        r'(?:create|make|new|spin\s+up|initialize|init)\s+(?:a\s+)?(?:new\s+)?(?:empty\s+)?(?:repo(?:sitory)?)\s+(?:called\s+|named\s+)?([a-zA-Z0-9_-]+)',
        r'(?:new|create)\s+(?:a\s+)?(?:github\s+)?repo(?:sitory)?\s+([a-zA-Z0-9_-]+)',
    ]
    for pattern in repo_patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            repo_name = match.group(1)
            is_private = bool(re.search(r'\bprivate\b', clean_text, re.IGNORECASE))
            logger.info(f"🔁 Fallback: CREATE_REPO detected - {repo_name}")
            return {
                "command": "CREATE_REPO",
                "repo_name": repo_name,
                "private": is_private
            }
    
    # Check for VIEW_USAGE
    usage_keywords = [
        r'\busage\b',
        r'\bstats\b',
        r'\bstatistics\b',
        r'\bdashboard\b',
        r'\bactivity\b',
        r'\bmy\s+usage\b',
        r'\bshow\s+usage\b',
        r'\bview\s+stats\b',
    ]
    for pattern in usage_keywords:
        if re.search(pattern, clean_text, re.IGNORECASE):
            logger.info(f"🔁 Fallback: VIEW_USAGE detected")
            return {"command": "VIEW_USAGE"}
    
    # Default to GENERAL
    logger.info(f"🔁 Fallback: GENERAL command")
    return {"command": "GENERAL"}

