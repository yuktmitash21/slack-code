#!/usr/bin/env python3
"""
Script to help find and test SpoonOS installation
"""

import sys
import subprocess
import importlib.util
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_import(module_name):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        logger.info(f"Module {module_name} is importable")
        return True
    except ImportError:
        logger.warning(f"Module {module_name} is not importable")
        return False

def try_pip_install(package_name):
    """Try to install a package"""
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Successfully installed {package_name}")
        return True
    except:
        logger.error(f"Failed to install {package_name}")
        return False

logger.info("🔍 Searching for SpoonOS installation methods...")

# Test if already installed
logger.info("1️⃣ Checking if SpoonOS is already installed...")
if test_import('spoon_ai'):
    logger.info("✅ SpoonOS (spoon_ai) is already installed!")
    try:
        from spoon_ai.agents.toolcall import ToolCallAgent
        logger.info("✅ Can import ToolCallAgent")
        from spoon_ai.chat import ChatBot
        logger.info("✅ Can import ChatBot")
        logger.info("🎉 SpoonOS is working! You're all set!")
        sys.exit(0)
    except ImportError as e:
        logger.warning(f"⚠️ SpoonOS found but incomplete: {e}")
else:
    logger.error("❌ SpoonOS not currently installed")

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

logger.warning("⚠️  SPOONOS NOT FOUND")
sys.exit(1)