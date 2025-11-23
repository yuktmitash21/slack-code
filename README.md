# Slack Bot with GitHub Integration and AI Code Generation

A Slack bot that responds to mentions, manages GitHub pull requests, and leverages **SpoonOS's Agentic Operating System** for intelligent, context-aware code generation.

## 🧠 Powered by SpoonOS Agentic OS

This bot is built on top of **SpoonOS**, a cutting-edge agentic operating system that enables autonomous AI agents to perform complex coding tasks. By integrating SpoonOS's agentic framework with GitHub and Slack, we've created a powerful coding assistant that:

- **Understands Intent**: Uses SpoonOS's agentic reasoning to interpret user requests contextually
- **Plans Autonomously**: Leverages SpoonOS's planning capabilities to determine the best approach for code changes
- **Executes Intelligently**: SpoonOS agents analyze entire codebases and generate production-ready code
- **Learns from Feedback**: Iteratively refines code through conversational loops powered by SpoonOS's agent memory

## Features

- 🤖 **Conversational PR Creation**: Discuss code changes in Slack threads before creating PRs
- 📝 **AI Code Generation**: Powered by SpoonOS's CodingAgent for intelligent, agentic code modifications
- 🔄 **Smart Caching**: Single agent call per conversation - preview is reused for PR creation
- 🎯 **Full Codebase Context**: SpoonOS agent has access to entire repository for context-aware generation
- 🧵 **Thread-based Conversations**: All interactions happen in threads for organized discussions
- 👤 **User Tagging**: Bot tags users in replies for better notifications
- ⚡ **No Questions Policy**: SpoonOS agent proposes concrete code changes immediately
- 🚀 **Explicit PR Creation**: PRs only created when user types "make PR" or clicks button
- ♻️ **Consistent Results**: Preview and PR use the same SpoonOS-generated files

## Architecture

### SpoonOS Agentic Workflow

```
User: "Add a login feature"
  ↓
Bot: Invokes SpoonOS Agentic OS
  ↓
SpoonOS Agent: 
  1. Analyzes full codebase context
  2. Plans implementation strategy
  3. Generates production-ready code
  4. Returns structured changeset
  ↓
Bot: Parse agent output → Format for Slack → Cache files
  ↓
Preview shown with "Make PR" button
  ↓
User: "make PR" (text or button)
  ↓
Bot: Use cached files → Create branch → Commit → Open PR
     (NO second agent call!)
```

### Why SpoonOS Agentic OS?

✅ **Autonomous Planning**: SpoonOS agents autonomously decide how to implement features  
✅ **Context-Aware**: Agents analyze entire codebases before generating code  
✅ **Multi-Step Reasoning**: Complex tasks broken down by agent planning layer  
✅ **Perfect Consistency**: Preview and PR are guaranteed identical  
✅ **Faster PR Creation**: No second agent invocation needed  
✅ **Cost Effective**: Single agent call per iteration  
✅ **Reliable**: SpoonOS's structured output ensures parsing consistency

## Setup

### Prerequisites

- Python 3.8+
- Slack workspace with admin access
- GitHub repository
- OpenAI API key (SpoonOS uses OpenAI's models as the LLM backbone for its agents)

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install SpoonOS from GitHub
pip install git+https://github.com/YourOrg/spoonos.git
```

### 2. Set Up Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Enable **Socket Mode** in Settings → Socket Mode
3. Add the following **Bot Token Scopes** under OAuth & Permissions:
   - `app_mentions:read` - Read mention events
   - `channels:history` - Read channel messages
   - `chat:write` - Send messages
   - `users:read` - Read user info
   - `channels:read` - View channels

4. **Subscribe to Events** under Event Subscriptions:
   - `app_mention` - When bot is mentioned
   - `message.channels` - Required for thread replies
   - `message.groups` - For private channels
   - `message.im` - For direct messages

5. **Install the app** to your workspace
6. Copy the following tokens from the Slack app settings:
   - **Bot Token** (starts with `xoxb-`) from OAuth & Permissions
   - **App Token** (starts with `xapp-`) from Basic Information → App-Level Tokens
     - When generating, enable `connections:write` scope

### 3. Set Up GitHub

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (full control)
   - `write:packages`
3. Copy the token

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_token
GITHUB_REPO=username/repository-name

# SpoonOS Agentic OS Configuration
# SpoonOS uses OpenAI's models as the LLM foundation for its autonomous agents
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o  # SpoonOS agent backbone model

# SpoonOS Provider
SPOONOS_PROVIDER=openai  # Agent orchestration via OpenAI
```

### 5. Run the Bot

```bash
python slack_bot.py
```

You should see:
```
⚡️ Bolt app is running!
INFO - SpoonOS Agentic OS initialized successfully
INFO - Autonomous coding agents ready for GitHub integration
```

## Usage

### Creating Pull Requests

1. **Start a conversation** by mentioning the bot:
   ```
   @bot Create a login page with email and password
   ```

2. **Bot responds with proposed changes** (concrete code, no questions):
   ```
   📝 PROPOSED CHANGESET
   ━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   📄 File: login.html [NEW]
   <html>
   ...
   
   📄 File: auth.py [MODIFIED]
   def login(username, password):
   ...
   ```

3. **Refine the changes** in the thread:
   ```
   Add a "Remember Me" checkbox
   ```
   
   Bot responds with updated changeset.

4. **Create the PR** when ready:
   ```
   make PR
   ```
   Or click the "🚀 Make PR with These Changes" button

5. **PR is created** using the exact cached code from the preview!

### Managing Pull Requests

**Merge a PR:**
```
@bot merge PR 123
```

**Revert a merged PR:**
```
@bot revert PR 123
```

## How It Works

### Conversational Flow with SpoonOS Agents

1. **Initial Request**: User mentions bot with a task
2. **Codebase Analysis**: Bot fetches and caches entire repository for agent context
3. **Agent Invocation**: SpoonOS Agentic OS receives task and full codebase
4. **Autonomous Planning**: SpoonOS agent reasons about the best implementation approach
5. **Code Generation**: Agent generates code with full repository awareness
6. **Cache Results**: Agent-generated files stored in conversation state
7. **Preview**: Formatted changeset shown to user
8. **Refinement**: User can request changes; agent iterates on previous context
9. **PR Creation**: Cached files used directly (no second agent invocation)

### File Operations

The bot can:
- ✅ **Create** new files (`[NEW]` tag)
- ✅ **Modify** existing files (`[MODIFIED]` tag)
- ✅ **Delete** files (`[DELETED]` tag)

### Message Chunking

Long AI responses are automatically split into 2900-character chunks to comply with Slack's 3000-character limit.

## Troubleshooting

### Bot not responding in threads

**Symptom**: Bot responds to initial mention but not follow-up messages

**Solution**: 
1. Go to Slack App Settings → Event Subscriptions
2. Add these events:
   - `message.channels`
   - `message.groups`
   - `message.im`
3. **Reinstall the app** to your workspace (important!)

### SpoonOS Agents not generating code

**Symptom**: Bot shows "AI not available" message

**Solutions**:
1. Check SpoonOS Agentic OS installation: `pip show spoon-ai`
2. Verify OpenAI API key in `.env` (required for SpoonOS agent backbone)
3. Check logs for SpoonOS agent initialization errors
4. Ensure `SPOONOS_PROVIDER=openai` is set correctly

### Dependency conflicts

**Symptom**: Errors during `pip install`

**Solution**:
```bash
# Start fresh
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### "Conversation not found" error

**Symptom**: Clicking "Make PR" button shows error

**Cause**: Button was from an old message before PR was created via text

**Solution**: Start a new conversation - the old one was already completed

## Development

### Project Structure

```
slack-bot/
├── slack_bot.py           # Main bot application
├── github_helper.py       # GitHub API integration
├── ai_agent.py           # SpoonOS wrapper for code generation
├── requirements.txt      # Python dependencies
└── .env                 # Configuration (not in git)
```

### Key Components

**`slack_bot.py`**:
- Handles Slack events and commands
- Manages conversation state
- Coordinates preview and PR creation
- **Invokes SpoonOS agents** with full context
- **Caches agent-generated files** from preview

**`github_helper.py`**:
- GitHub API operations (branch, commit, PR)
- **Accepts cached files** to skip agent re-invocation
- Handles file creation/modification/deletion
- Provides codebase context to SpoonOS agents

**`ai_agent.py`**:
- **SpoonOS Agentic OS Integration Layer**
- Wraps SpoonOS's autonomous coding agents
- Provides repository context to agents
- Parses agent output into file operations
- Supports multiple agent response formats
- Handles vision-based wireframe-to-code via SpoonOS

## License

MIT License - Feel free to use and modify!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review logs in terminal
3. Check Slack app configuration
4. Verify environment variables
