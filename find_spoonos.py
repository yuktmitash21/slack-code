#!/usr/bin/env python3
"""
Script to help find and test SpoonOS installation
"""

import sys
import subprocess
import importlib.util
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_import(module_name):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        logger.info(f"Module {module_name} imported successfully")
        return True
    except ImportError as e:
        logger.error(f"ImportError: {e}")
        return False

def try_pip_install(package_name):
    """Try to install a package"""
    try:
        logger.info(f"Attempting to install package: {package_name}")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Package {package_name} installed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to install package {package_name}: {e}")
        return False

logger.info("🔍 Searching for SpoonOS installation methods...")
logger.info("=" * 60)
logger.info()

# Test if already installed
logger.info("1️⃣ Checking if SpoonOS is already installed...")
if test_import('spoon_ai'):
    logger.info("✅ SpoonOS (spoon_ai) is already installed!")
    try:
        from spoon_ai.agents.toolcall import ToolCallAgent
        logger.info("✅ Can import ToolCallAgent")
        from spoon_ai.chat import ChatBot
        logger.info("✅ Can import ChatBot")
        logger.info()
        logger.info("🎉 SpoonOS is working! You're all set!")
        sys.exit(0)
    except ImportError as e:
        logger.error(f"⚠️ SpoonOS found but incomplete: {e}")
else:
    logger.error("❌ SpoonOS not currently installed")

logger.info()
logger.info("2️⃣ Trying possible PyPI package names...")

# Try different PyPI package names
pypi_names = [
    'spoonos',
    'spoon-ai',
    'spoon_ai',
    'SpoonOS',
    'xspoonai',
]

for name in pypi_names:
    logger.info(f"   Trying: pip install {name}")
    if try_pip_install(name):
        if test_import('spoon_ai'):
            logger.info(f"✅ SUCCESS! Installed via: pip install {name}")
            sys.exit(0)

logger.error("❌ Could not install from PyPI")
logger.info()

logger.info("3️⃣ Trying GitHub repositories...")

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
    logger.info(f"   Trying: {url}")
    if try_pip_install(url):
        if test_import('spoon_ai'):
            logger.info(f"✅ SUCCESS! Installed from: {url}")
            sys.exit(0)

logger.error("❌ Could not install from GitHub")
logger.info()

logger.info("=" * 60)
logger.error("⚠️  SPOONOS NOT FOUND")
logger.info("=" * 60)
logger.info()
logger.info("Possible solutions:")
logger.info()
logger.info("1. Check the official documentation:")
logger.info("   https://xspoonai.github.io/docs/getting-started/installation/")
logger.info()
logger.info("2. Contact XSpoonAi support:")
logger.info("   - GitHub: https://github.com/xspoonai")
logger.info("   - Check if they have a Discord or support channel")
logger.info()
logger.info("3. SpoonOS might be in private beta:")
logger.info("   - You may need to request access")
logger.info("   - Check if you need an invitation")
logger.info()
logger.info("4. Alternative: Disable AI and use placeholder mode:")
logger.info("   - Set USE_AI_CODE_GENERATION=false in .env")
logger.info("   - Bot will work without AI code generation")
logger.info()

sys.exit(1)