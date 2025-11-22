# AI Code Generation Setup

## Overview

The bot uses **direct OpenAI integration** for AI-powered code generation. You can optionally use SpoonOS framework for more advanced features.

## Quick Start

### Basic Setup (OpenAI Direct)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Add API key to `.env`**:
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
```

3. **Run the bot**:
```bash
python slack_bot.py
```

The bot will use OpenAI directly for code generation.

## How It Works

### Code Generation Flow

1. **User Request**: `@bot add authentication`
2. **Context Gathering**: Bot reads full codebase from GitHub
3. **AI Generation**: Sends task + codebase to OpenAI
4. **Changeset Preview**: Shows proposed code changes
5. **Refinement**: User can provide feedback
6. **PR Creation**: When user says "make PR", creates actual PR

### What the AI Can Do

✅ **Add new files** with complete implementation
✅ **Modify existing files** (outputs complete updated file)
✅ **Use correct imports** from your existing codebase
✅ **Match your code style** and patterns
✅ **Integrate seamlessly** with existing architecture

### What the AI Cannot Do

❌ **Delete code reliably** (AI generates complete files, may forget to exclude code)
❌ **Make surgical edits** (replaces entire files)
❌ **Generate perfect diffs** (shows complete file, not just changes)

## Optional: SpoonOS Framework

For more advanced features, you can install SpoonOS:

### Installation

SpoonOS is not on PyPI, install from GitHub:

```bash
# Find the correct SpoonOS repository
pip install git+https://github.com/[correct-spoonos-repo].git
```

### Configuration

No configuration needed - the bot will automatically detect and use SpoonOS if available.

### Benefits of SpoonOS

- More structured tool calling
- Better context management
- Memory/conversation tracking
- Multi-turn reasoning

### Known Issues

SpoonOS has had API compatibility issues with OpenAI. If you see errors like:

```
tool_choice is only allowed when tools are specified
```

The bot will automatically fall back to direct OpenAI integration.

## Current Implementation

### ai_agent.py

Contains two approaches:

1. **SpoonOS Integration** (if available)
   - Uses `ToolCallAgent`, `ChatBot`, `ToolManager`
   - Structured tool calling
   - Better for complex multi-step tasks

2. **Direct OpenAI Fallback** (always available)
   - Uses `openai.OpenAI()` client directly
   - Simple chat completions
   - Reliable and fast

### Automatic Fallback

The bot automatically uses the best available option:
1. Try SpoonOS (if installed)
2. Fall back to direct OpenAI
3. If no API key, use placeholder PRs

## Configuration

### Environment Variables

```bash
# Required for AI features
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=gpt-4o           # Default model
USE_AI_CODE_GENERATION=true   # Enable/disable AI

# GitHub (required for PR creation)
GITHUB_TOKEN=ghp_...
GITHUB_REPO=username/repo
```

## Testing

### Test AI Generation

```bash
@bot add a hello world function
```

Expected response:
- Shows changeset with proposed code
- Includes complete implementation
- "Make PR" button appears

### Test PR Creation

```
@bot add authentication
# Bot shows changeset
Make PR
# Bot creates PR with actual code
```

## Troubleshooting

### "AI not available"

**Cause**: No OPENAI_API_KEY in .env

**Fix**:
```bash
echo "OPENAI_API_KEY=sk-..." >> .env
```

### "No files generated"

**Cause**: AI response parsing failed

**Fix**: Check logs for AI response, may need to adjust parsing logic

### SpoonOS errors

**Cause**: SpoonOS framework issues

**Fix**: The bot will automatically fall back to direct OpenAI

## Advanced: Customizing AI Behavior

### System Prompt

Edit `ai_agent.py` to customize the AI's behavior:

```python
system_prompt = """
You are an expert software engineer...
[customize instructions here]
"""
```

### Response Parsing

Edit `_parse_agent_response()` in `ai_agent.py` to customize how code is extracted from AI responses.

## Performance

- **First request**: 5-10 seconds (reads codebase)
- **Follow-up requests**: 2-5 seconds (uses cached context)
- **PR creation**: 5-10 seconds (creates files on GitHub)

## Costs

Using OpenAI GPT-4:
- Small repo (~10 files): ~$0.05 per request
- Medium repo (~50 files): ~$0.20 per request
- Large repo (~200 files): ~$0.80 per request

Context is cached per conversation to reduce costs.

## Summary

The bot uses **OpenAI directly** for code generation:
- ✅ Simple and reliable
- ✅ No complex dependencies
- ✅ Automatic fallback handling
- ✅ Full codebase context
- ✅ Conversational refinement

For most use cases, direct OpenAI integration works great! 🚀

