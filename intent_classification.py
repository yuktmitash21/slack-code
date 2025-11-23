"""
Intent Classification Module

Uses AI to intelligently classify user intent for conversational PR creation.
Determines whether user wants to SUBMIT a PR or REFINE the changeset.
"""

import os
import logging
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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