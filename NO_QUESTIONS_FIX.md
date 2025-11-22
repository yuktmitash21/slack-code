# No Questions Mode - Immediate Changesets

## Problem

The bot was asking clarifying questions like "What would you like me to build?" or "Can you provide more details?" instead of immediately proposing concrete code changes (changesets).

## User's Requirement

> "It should just respond with changesets each time. No questions, it should just share diffset and change them based on user feedback. Finally the 'Make a PR' button should be there on each message to force the current changes into PR."

## Solution

### 1. Updated AI Prompts

**Changed the planning prompt from:**
```python
"Analyze this task and respond with:
1. What you understand the user wants
2. What files/changes you would create
3. Any clarifying questions (if needed)

DO NOT create code yet. Just discuss the plan with the user.
If you have questions, ask them."
```

**To:**
```python
"IMPORTANT: Propose CONCRETE CODE CHANGES immediately. Do NOT ask clarifying questions.

Respond with a CHANGESET in this format:

📝 PROPOSED CHANGESET
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
[One-line summary]

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: path/to/file.py [NEW/MODIFIED/DELETED]

```language
[Complete file content]
```

Rules:
- Propose changes immediately, don't ask questions
- Make reasonable assumptions about what the user wants"
```

### 2. Added "Make PR" Button

Every response now includes a Slack Block Kit button that allows instant PR creation:

```python
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": ai_response}
    },
    {
        "type": "actions",
        "elements": [{
            "type": "button",
            "text": {"type": "plain_text", "text": "🚀 Make PR with These Changes"},
            "style": "primary",
            "action_id": "make_pr_button"
        }]
    }
]
```

### 3. Updated System Prompt

**System prompt now explicitly states:**
```python
"You are an expert software engineer. Propose concrete code changes in changeset format. 
Do NOT ask clarifying questions - make reasonable assumptions and propose specific changes 
immediately. The user will refine them through conversation if needed."
```

### 4. Changed Initial Message

**From:**
```
"Hi! I'll help you create a PR for: <task>

Let me understand what you need..."
```

**To:**
```
"I'll propose code changes for: <task>

📚 Reading codebase..."
```

## Workflow Now

### Old Flow (❌ Asking Questions)
```
You: @bot add authentication
Bot: I understand you want to add authentication. 
     Can you clarify:
     - What type of authentication? (JWT, OAuth, etc.)
     - Which files should I modify?
     - Should I create new files?
```

### New Flow (✅ Immediate Changesets)
```
You: @bot add authentication

Bot: 📝 PROPOSED CHANGESET
     ━━━━━━━━━━━━━━━━━━━━━━━━━━
     📋 CHANGESET SUMMARY
     Add JWT authentication middleware
     
     ━━━━━━━━━━━━━━━━━━━━━━━━━━
     📄 File: src/auth/jwt.py [NEW]
     
     ```python
     import jwt
     from datetime import datetime, timedelta
     
     def generate_token(user_id):
         payload = {
             'user_id': user_id,
             'exp': datetime.utcnow() + timedelta(hours=24)
         }
         return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
     ```
     
     ━━━━━━━━━━━━━━━━━━━━━━━━━━
     📄 File: src/middleware/auth.py [NEW]
     
     ```python
     from flask import request, jsonify
     import jwt
     
     def require_auth(f):
         def decorated(*args, **kwargs):
             token = request.headers.get('Authorization')
             if not token:
                 return jsonify({'error': 'No token'}), 401
             try:
                 jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                 return f(*args, **kwargs)
             except:
                 return jsonify({'error': 'Invalid token'}), 401
         return decorated
     ```
     
     ━━━━━━━━━━━━━━━━━━━━━━━━━━
     📊 Summary: 2 file(s) in this changeset
     📝 Files: src/auth/jwt.py, src/middleware/auth.py
     
     [🚀 Make PR with These Changes] <- Button
     
     _Reply in thread to refine the changes, or click the button above to create the PR now_

You: Add token refresh
Bot: [Shows updated changeset with refresh token logic]
     [🚀 Make PR with These Changes] <- Button

You: [Click button]
Bot: ✅ PR #42 created successfully!
```

## Benefits

### ✅ Faster Iteration
- No back-and-forth clarification questions
- Immediate concrete proposals
- User can see actual code right away

### ✅ Easy Refinement
- User replies with feedback in thread
- Bot updates the changeset based on feedback
- Each message has a "Make PR" button

### ✅ User Control
- User decides when to create the PR
- Can refine changes as many times as needed
- Button provides clear action point

### ✅ Better UX
- Clear, actionable proposals
- Visual button for PR creation
- Formatted changesets easy to read

## Testing

### Test 1: Simple Request

```bash
You: @bot add a hello world function to utils.py
```

**Expected:**
- ✅ Immediate changeset showing complete utils.py with new function
- ✅ "Make PR" button visible
- ❌ No questions like "What should the function do?"

### Test 2: Refinement

```bash
You: @bot add authentication
Bot: [Shows JWT auth changeset with 2 files]

You: use bcrypt for password hashing
Bot: [Shows updated changeset with bcrypt added]
     [Make PR button]

You: [Clicks button]
Bot: ✅ PR #42 created!
```

### Test 3: Complex Request

```bash
You: @bot refactor the API to use async/await
```

**Expected:**
- ✅ Changeset showing modified files with async syntax
- ✅ Makes reasonable assumptions about what to change
- ❌ Doesn't ask "Which endpoints should be async?"

## Files Modified

1. **slack_bot.py**
   - Updated `planning_prompt` to demand immediate changesets
   - Updated system prompt to prohibit questions
   - Changed initial message to be action-oriented
   - Added Slack Block Kit button to responses
   - Added `@app.action("make_pr_button")` handler
   - Removed references to Aider (old AI integration)

## Key Changes

### Prompt Engineering
```python
# OLD: Encourages discussion
"If you have questions, ask them."

# NEW: Demands action
"Do NOT ask clarifying questions - make reasonable assumptions"
```

### Response Format
```python
# OLD: Text-only response
say(text=f"{ai_response}\n\nReply or say 'make PR'")

# NEW: Rich blocks with button
say(
    text="Changeset ready!",
    blocks=[section, divider, actions, context],
    thread_ts=thread_ts
)
```

### Button Handler
```python
@app.action("make_pr_button")
def handle_make_pr_button_click(ack, body, client, logger):
    # Acknowledges click
    # Gets conversation data
    # Creates PR immediately
    # Sends result with link
    # Cleans up conversation
```

## Important Notes

### AI Makes Assumptions
The AI will now make reasonable assumptions based on:
- The task description
- The existing codebase context
- Common patterns and best practices

If assumptions are wrong, the user can:
- Reply with corrections
- Bot will update the changeset
- Still hasn't created a PR yet (until button clicked)

### Button State
- Button value contains `thread_ts`
- Used to look up conversation in `pr_conversations` dict
- Only works while conversation is active
- After PR creation, conversation is cleaned up

### Fallback
If user types "make PR" in thread (instead of clicking button), the message handler will detect it and trigger PR creation (existing logic).

## Common Issues

### Issue: Bot still asking questions

**Cause:** Using old code or prompt not updated
**Solution:** Restart bot to load new prompts

### Issue: No button appears

**Cause:** Slack app doesn't have interactive components enabled
**Solution:** Check Slack app settings for "Interactivity & Shortcuts"

### Issue: Button doesn't work

**Cause:** Action handler not registered or conversation not found
**Solution:** 
- Check logs for "Make PR button clicked"
- Verify `pr_conversations` contains the thread_ts
- Restart bot to register the action handler

## Summary

The bot now operates in "changeset-first" mode:
1. ✅ Proposes concrete changes immediately (no questions)
2. ✅ Shows complete code in formatted changesets
3. ✅ Includes "Make PR" button on every response
4. ✅ Allows refinement through conversation
5. ✅ Creates PR only when user clicks button or says "make PR"

**The conversational flow is now focused on refining proposed changes, not gathering requirements!** 🎉

