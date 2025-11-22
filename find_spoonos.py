#!/usr/bin/env python3
"""
Script to help find and test SpoonOS installation
"""

import sys
import subprocess
import importlib.util

def test_import(module_name):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def try_pip_install(package_name):
    """Try to install a package"""
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False

print("🔍 Searching for SpoonOS installation methods...")
print("=" * 60)
print()

# Test if already installed
print("1️⃣ Checking if SpoonOS is already installed...")
if test_import('spoon_ai'):
    print("✅ SpoonOS (spoon_ai) is already installed!")
    try:
        from spoon_ai.agents.toolcall import ToolCallAgent
        print("✅ Can import ToolCallAgent")
        from spoon_ai.chat import ChatBot
        print("✅ Can import ChatBot")
        print()
        print("🎉 SpoonOS is working! You're all set!")
        sys.exit(0)
    except ImportError as e:
        print(f"⚠️ SpoonOS found but incomplete: {e}")
else:
    print("❌ SpoonOS not currently installed")

print()
print("2️⃣ Trying possible PyPI package names...")

# Try different PyPI package names
pypi_names = [
    'spoonos',
    'spoon-ai',
    'spoon_ai',
    'SpoonOS',
    'xspoonai',
]

for name in pypi_names:
    print(f"   Trying: pip install {name}")
    if try_pip_install(name):
        if test_import('spoon_ai'):
            print(f"✅ SUCCESS! Installed via: pip install {name}")
            sys.exit(0)

print("❌ Could not install from PyPI")
print()

print("3️⃣ Trying GitHub repositories...")

# Try different GitHub URLs
github_urls = [
    'git+https://github.com/XSpoonAi/SpoonOS.git',
    'git+https://github.com/XSpoonAi/spoonos.git', 
    'git+https://github.com/XSpoonAi/spoon-ai.git',
    'git+https://github.com/xspoonai/SpoonOS.git',
    'git+https://github.com/xspoonai/spoonos.git',
    'git+https://github.com/xspoonai/spoon-ai.git',
]

for url in github_urls:
    print(f"   Trying: {url}")
    if try_pip_install(url):
        if test_import('spoon_ai'):
            print(f"✅ SUCCESS! Installed from: {url}")
            sys.exit(0)

print("❌ Could not install from GitHub")
print()

print("=" * 60)
print("⚠️  SPOONOS NOT FOUND")
print("=" * 60)
print()
print("Possible solutions:")
print()
print("1. Check the official documentation:")
print("   https://xspoonai.github.io/docs/getting-started/installation/")
print()
print("2. Contact XSpoonAi support:")
print("   - GitHub: https://github.com/xspoonai")
print("   - Check if they have a Discord or support channel")
print()
print("3. SpoonOS might be in private beta:")
print("   - You may need to request access")
print("   - Check if you need an invitation")
print()
print("4. Alternative: Disable AI and use placeholder mode:")
print("   - Set USE_AI_CODE_GENERATION=false in .env")
print("   - Bot will work without AI code generation")
print()

sys.exit(1)

