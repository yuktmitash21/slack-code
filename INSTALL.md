# Installation Guide

Complete installation instructions for the Slack bot.

## Quick Install (Core Features Only)

For basic Slack bot with GitHub integration but **without AI code generation**:

```bash
cd /Users/yuktmitash/Documents/slack-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt
```

This gives you:
- ✅ Slack bot with channel context
- ✅ GitHub PR creation (placeholder changes)
- ✅ PR merging and reverting
- ❌ AI code generation (disabled)

---

## Full Install (With AI Code Generation)

For the complete experience including AI-powered code generation:

### Step 1: Install Core Dependencies

```bash
cd /Users/yuktmitash/Documents/slack-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt
```

### Step 2: Install SpoonOS (AI Framework)

SpoonOS is currently in development and must be installed from GitHub:

**Method A: Direct Install (Easiest)**
```bash
pip install git+https://github.com/xspoonai/spoonos.git
```

**Method B: Clone and Install (If Method A fails)**
```bash
git clone https://github.com/xspoonai/spoonos.git
cd spoonos
pip install -e .
cd ..
```

### Step 3: Install LLM Provider

Choose one (or both):

**OpenAI (Recommended):**
```bash
pip install openai
```

**Anthropic (Claude):**
```bash
pip install anthropic
```

### Step 4: Verify Installation

```bash
python -c "from spoon_ai.agents.toolcall import ToolCallAgent; print('SpoonOS installed successfully!')"
```

If this prints the success message, you're all set!

---

## Troubleshooting Installation

### Issue: "Could not find a version that satisfies the requirement spoon-ai"

**Solution**: SpoonOS is not on PyPI. Install from GitHub:
```bash
pip install git+https://github.com/xspoonai/spoonos.git
```

### Issue: Git command not found

**Solution**: Install git first:
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows
# Download from: https://git-scm.com/download/win
```

### Issue: SpoonOS install fails with "No module named setuptools"

**Solution**: Update pip and setuptools:
```bash
pip install --upgrade pip setuptools wheel
pip install git+https://github.com/xspoonai/spoonos.git
```

### Issue: Permission denied during pip install

**Solution**: Make sure virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### Issue: SpoonOS GitHub repository not found

**Solution**: The repository might have moved or changed. Check:
1. Visit: https://github.com/xspoonai
2. Find the correct repository name
3. Install with: `pip install git+https://github.com/xspoonai/[correct-repo-name].git`

**Alternative**: Disable AI features and use placeholder mode:
```bash
# In your .env file
USE_AI_CODE_GENERATION=false
```

---

## Platform-Specific Instructions

### macOS

```bash
# Install Python 3.8+ if not installed
brew install python@3.11

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install SpoonOS
pip install git+https://github.com/xspoonai/spoonos.git
pip install openai
```

### Linux (Ubuntu/Debian)

```bash
# Install Python 3.8+ if not installed
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv git

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install SpoonOS
pip install git+https://github.com/xspoonai/spoonos.git
pip install openai
```

### Windows

```powershell
# Create and activate venv
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install SpoonOS
pip install git+https://github.com/xspoonai/spoonos.git
pip install openai
```

---

## Verify Your Installation

Run this test script:

```bash
python -c "
import sys
print('Python version:', sys.version)

# Check core packages
try:
    import slack_bolt
    print('✅ slack-bolt installed')
except ImportError:
    print('❌ slack-bolt NOT installed')

try:
    import github
    print('✅ PyGithub installed')
except ImportError:
    print('❌ PyGithub NOT installed')

try:
    import git
    print('✅ gitpython installed')
except ImportError:
    print('❌ gitpython NOT installed')

# Check AI packages (optional)
try:
    from spoon_ai.agents.toolcall import ToolCallAgent
    print('✅ SpoonOS installed (AI enabled)')
except ImportError:
    print('ℹ️  SpoonOS NOT installed (AI disabled, using placeholders)')

try:
    import openai
    print('✅ OpenAI installed')
except ImportError:
    print('ℹ️  OpenAI NOT installed')
"
```

Expected output:
```
Python version: 3.x.x
✅ slack-bolt installed
✅ PyGithub installed
✅ gitpython installed
✅ SpoonOS installed (AI enabled)
✅ OpenAI installed
```

---

## What If SpoonOS Installation Fails?

**The bot will still work!** It just won't have AI code generation:

- ✅ Slack bot functionality: Works
- ✅ Channel context: Works
- ✅ GitHub integration: Works
- ✅ PR creation: Works (with placeholder changes)
- ✅ PR merging: Works
- ✅ PR reverting: Works
- ❌ AI code generation: Disabled

To suppress AI-related warnings:
```bash
# Add to .env
USE_AI_CODE_GENERATION=false
```

---

## Next Steps

After installation:

1. **Configure Slack**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **Configure GitHub**: See [GITHUB_SETUP.md](GITHUB_SETUP.md)
3. **Configure AI** (optional): See [AI_AGENT_SETUP.md](AI_AGENT_SETUP.md)
4. **Test the bot**: See [QUICK_START.md](QUICK_START.md)

---

## Getting Help

- **Installation issues**: Open an issue in this repository
- **SpoonOS issues**: Check https://github.com/xspoonai or their docs
- **General questions**: See [README.md](README.md)

Happy coding! 🚀

