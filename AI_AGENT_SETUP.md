# AI Code Generation Setup with SpoonOS

This guide explains how to set up AI-powered code generation using the [SpoonOS framework](https://xspoonai.github.io/docs/getting-started/quick-start/).

## Overview

The bot can now use AI to generate **actual code** instead of placeholder changes when creating pull requests! It uses SpoonOS, a powerful AI agent framework that supports multiple LLM providers.

### What It Does

When you ask the bot to create a PR:
```
@BotName create a PR for adding user authentication
```

**Without AI (placeholder mode):**
- Creates a random file or adds a comment

**With AI enabled:**
- Analyzes your task description
- Generates actual, functional code
- Creates proper file structures
- Includes imports, error handling, and documentation
- Commits real implementation code to the PR

## Installation

### 1. Install SpoonOS and Dependencies

SpoonOS is currently in development and needs to be installed from GitHub:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Install core dependencies first
pip install -r requirements.txt

# Method 1: Install SpoonOS from GitHub (recommended)
pip install git+https://github.com/xspoonai/spoonos.git

# Method 2: Clone and install manually (if above fails)
git clone https://github.com/xspoonai/spoonos.git
cd spoonos
pip install -e .
cd ..

# Install LLM provider (OpenAI or Anthropic)
pip install openai  # For OpenAI
# OR
pip install anthropic  # For Anthropic
```

**Note**: If SpoonOS installation fails, the bot will still work with placeholder code generation. AI features are completely optional.

### 2. Get an LLM API Key

SpoonOS supports multiple providers. Choose one:

#### Option A: OpenAI (Recommended)

1. Go to: https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

#### Option B: Anthropic (Claude)

1. Go to: https://console.anthropic.com/account/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

#### Option C: Other Providers

SpoonOS also supports:
- **Google Gemini**: Get key at https://makersuite.google.com/app/apikey
- **DeepSeek**: Get key at https://platform.deepseek.com/
- **OpenRouter**: Get key at https://openrouter.ai/keys

### 3. Add to Your .env File

```bash
# Required: GitHub configuration (from before)
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_REPO=yuktmitash21/slack-code

# Enable AI code generation
USE_AI_CODE_GENERATION=true

# Option A: OpenAI (recommended)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Option B: Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
# ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Option C: Other providers
# GEMINI_API_KEY=your-gemini-key-here
# DEEPSEEK_API_KEY=your-deepseek-key-here
# OPENROUTER_API_KEY=your-openrouter-key-here
```

### 4. Restart the Bot

```bash
python slack_bot.py
```

You should see:
```
⚡️ Starting Slack bot in Socket Mode...
GitHub integration enabled (AI code generation: True)
AI code generation enabled
⚡️ Bolt app is running!
```

## Usage

### Creating AI-Generated PRs

Simply create PRs as before, but now with actual code:

```
@BotName create a PR for adding email validation function
@BotName create a PR for implementing JWT authentication
@BotName create a PR for creating a user registration endpoint
```

The AI will:
1. Understand your task description
2. Generate appropriate code files
3. Create a PR with real, functional code
4. Include proper structure, imports, and documentation

### Example: Before and After

**Without AI:**
```
You: @BotName create a PR for user authentication

Bot: ✅ Pull Request Created!
     📝 Changes: Created new file: bot_tasks/task_20251122-143045.txt
     (Just a placeholder file)
```

**With AI:**
```
You: @BotName create a PR for user authentication

Bot: ✅ Pull Request Created!
     📝 Changes: AI-generated code: Created src/auth/authentication.py, 
         Created src/auth/jwt_handler.py, Created tests/test_auth.py
     (Actual implementation code!)
```

## Configuration Options

### Disable AI Code Generation

To temporarily disable AI and use placeholder changes:

```bash
# In .env
USE_AI_CODE_GENERATION=false
```

Or remove/comment out the LLM API key.

### Choose Different Models

#### OpenAI Models:
```bash
OPENAI_MODEL=gpt-4o            # Best quality (default)
OPENAI_MODEL=gpt-4o-mini       # Faster, cheaper
OPENAI_MODEL=gpt-4-turbo       # Alternative
```

#### Anthropic Models:
```bash
ANTHROPIC_MODEL=claude-sonnet-4-20250514    # Latest (default)
ANTHROPIC_MODEL=claude-opus-4-20250514      # Most capable
ANTHROPIC_MODEL=claude-haiku-4-20250514     # Fastest
```

## How It Works Internally

### SpoonOS Integration

The bot uses SpoonOS's `ToolCallAgent` with custom tools:

```python
class CodingAgent(ToolCallAgent):
    """AI agent that generates code"""
    
    system_prompt = """
    You are an expert software engineer...
    Generate high-quality, production-ready code...
    """
    
    available_tools = ToolManager([
        CodeGenerationTool(),
        FileAnalysisTool()
    ])
```

### Code Generation Flow

1. **User creates PR request** in Slack
2. **Bot receives task** description
3. **AI agent analyzes** the task
4. **SpoonOS generates** code using the LLM
5. **Bot creates files** in new GitHub branch
6. **PR is opened** with actual code
7. **User reviews** and merges

### File: `ai_agent.py`

This module contains:
- `CodingAgent`: SpoonOS-based AI coding agent
- `AICodeGenerator`: High-level interface
- `CodeGenerationTool`: Tool for file generation
- `FileAnalysisTool`: Tool for repo analysis

### File: `github_helper.py`

Updated to:
- Check if AI is enabled
- Call AI agent for code generation
- Fallback to placeholder if AI fails
- Commit AI-generated files to branch

## Troubleshooting

### "SpoonOS not installed" Error

SpoonOS must be installed from GitHub:

```bash
# Try this first
pip install git+https://github.com/xspoonai/spoonos.git

# If that fails, clone and install manually
git clone https://github.com/xspoonai/spoonos.git
cd spoonos
pip install -e .
cd ..

# Then install LLM provider
pip install openai
```

**Alternative: Disable AI and use placeholders:**
```bash
# In .env file
USE_AI_CODE_GENERATION=false
```

### "AI agent not available" Message

Check:
1. SpoonOS is installed: `pip list | grep spoon`
2. If not installed, run: `pip install git+https://github.com/xspoonai/spoonos.git`
3. API key is set in `.env`
4. API key is valid and has credits
5. Bot was restarted after adding API key

If SpoonOS installation continues to fail:
- The bot will still work with placeholder PR generation
- Set `USE_AI_CODE_GENERATION=false` in `.env` to suppress warnings

### "AI code generation disabled (no API key)" Log

Add one of these to your `.env`:
```bash
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### AI Generates Poor Quality Code

Try:
1. **Be more specific** in task descriptions:
   - ❌ "add auth"
   - ✅ "create a JWT authentication system with login and registration endpoints"

2. **Use a better model**:
   - Switch to `gpt-4o` or `claude-sonnet-4-20250514`

3. **Provide context** in your message:
   ```
   @BotName create a PR for user authentication
   The project uses FastAPI and PostgreSQL.
   Follow our existing patterns in src/api/
   ```

### API Rate Limits / Costs

- **OpenAI**: gpt-4o costs ~$0.005-0.015 per generation
- **Anthropic**: Claude costs vary by model
- **Monitor usage** in your provider's dashboard
- **Use smaller models** for simple tasks (gpt-4o-mini)
- **Disable AI** for testing: `USE_AI_CODE_GENERATION=false`

## Advanced Configuration

### Custom System Prompt

Edit `ai_agent.py` to customize the agent's behavior:

```python
class CodingAgent(ToolCallAgent):
    system_prompt: str = """
    You are an expert Python/JavaScript/Go developer.
    
    When generating code:
    - Follow PEP 8 for Python
    - Use TypeScript for JavaScript
    - Include comprehensive error handling
    - Add detailed docstrings
    - Follow our company style guide
    - etc...
    """
```

### Repository Context

The bot automatically provides:
- Repository name
- Primary language
- Branch name

You can extend this in `github_helper.py`:

```python
# Add more context
repo_context = f"""
Repository: {self.repo_name}
Language: Python
Branch: {branch_name}
Framework: FastAPI
Database: PostgreSQL
Testing: pytest
"""
```

### Multiple Files

The AI can generate multiple files in one PR. Just ask:

```
@BotName create a PR for user authentication with:
- Authentication service
- JWT handler
- User model
- Unit tests
```

## Benefits of AI Code Generation

✅ **Real Implementation**: Actual working code, not placeholders  
✅ **Time Saving**: Generate boilerplate and structure instantly  
✅ **Best Practices**: AI follows coding standards  
✅ **Documentation**: Includes comments and docstrings  
✅ **Multiple Files**: Can generate full feature sets  
✅ **Consistency**: Maintains style across codebase  

## Limitations

⚠️ **Review Required**: Always review AI-generated code before merging  
⚠️ **May Need Refinement**: Code might need adjustments  
⚠️ **API Costs**: LLM calls cost money (though usually minimal)  
⚠️ **Rate Limits**: Provider rate limits may apply  
⚠️ **Context Size**: Very large tasks may need to be split  

## Cost Estimate

Typical costs per PR:
- **OpenAI gpt-4o**: $0.005 - $0.015 per PR
- **OpenAI gpt-4o-mini**: $0.001 - $0.003 per PR
- **Anthropic Claude**: $0.010 - $0.030 per PR

For 100 PRs/month with gpt-4o: ~$1-2 total cost

## Next Steps

1. ✅ Set up AI code generation
2. ✅ Test with simple tasks
3. 🔜 Customize system prompt for your needs
4. 🔜 Integrate with your development workflow
5. 🔜 Add more sophisticated tools to the agent

## Resources

- **SpoonOS Docs**: https://xspoonai.github.io/docs/
- **OpenAI API**: https://platform.openai.com/docs
- **Anthropic Claude**: https://docs.anthropic.com/
- **GitHub API**: https://docs.github.com/en/rest

---

Questions? Check the main [README.md](README.md) or open an issue! 🤖✨

