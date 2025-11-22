#!/bin/bash
# Script to install SpoonOS for AI code generation

set -e  # Exit on error

echo "🤖 Installing SpoonOS for AI Code Generation"
echo "==========================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Please run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Installing core dependencies..."
pip install -r requirements.txt
echo "✅ Core dependencies installed"
echo ""

echo "Step 2: Installing SpoonOS from GitHub..."
# Try direct install first
if pip install git+https://github.com/XSpoonAi/xspoonai.github.io.git; then
    echo "✅ SpoonOS installed successfully!"
else
    echo "❌ Direct install failed. Trying clone method..."
    
    # Clone and install manually
    if [ -d "spoonos" ]; then
        echo "Removing old spoonos directory..."
        rm -rf spoonos
    fi
    
    git clone https://github.com/xspoonai/spoonos.git
    cd spoonos
    pip install -e .
    cd ..
    echo "✅ SpoonOS installed via clone method"
fi
echo ""

echo "Step 3: Installing OpenAI..."
pip install openai
echo "✅ OpenAI installed"
echo ""

echo "Step 4: Verifying installation..."
python -c "
try:
    from spoon_ai.agents.toolcall import ToolCallAgent
    from spoon_ai.chat import ChatBot
    print('✅ SpoonOS modules imported successfully!')
except ImportError as e:
    print('❌ SpoonOS import failed:', e)
    exit(1)

try:
    import openai
    print('✅ OpenAI module imported successfully!')
except ImportError as e:
    print('❌ OpenAI import failed:', e)
    exit(1)
"

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "Next steps:"
echo "1. Make sure your .env file has OPENAI_API_KEY set"
echo "2. Set USE_AI_CODE_GENERATION=true in .env"
echo "3. Run: python slack_bot.py"
echo ""
echo "You should see: 'AI code generation enabled'"

