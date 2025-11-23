# Slack Bot with GitHub Integration and AI Code Generation

This document provides detailed information about the Slack bot designed to respond to mentions, manage GitHub pull requests, and utilize AI for code generation.

## Features

- **Conversational PR Creation**: Enable discussion of code changes within Slack threads before PR creation.
- **AI Code Generation**: Utilizes AI for generating and modifying code, enhancing productivity.
- **Smart Caching**: Reduces redundant AI calls by caching generated previews for PR creation.
- **Full Codebase Context**: The bot accesses the entire repository for informed code generation.
- **Thread-based Conversations**: Organizes interactions within Slack threads.
- **User Tagging**: Notifies users by tagging them in replies.
- **No Questions Policy**: Ensures the bot proposes concrete code changes immediately.
- **Explicit PR Creation**: PRs are created when specified by the user.
- **Consistent Results**: Ensures preview and PRs use the same AI-generated files.

## Architecture

### Single AI System

The bot uses a single AI system to ensure consistency and reliability in code generation.