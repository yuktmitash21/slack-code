# Slack Bot with GitHub Integration and AI Code Generation

This repository contains a highly interactive Slack bot designed to streamline software development processes by integrating with GitHub for PR management and utilizing AI for intelligent code suggestions and generation.

## Key Features

- **Conversational PR Management**: Engage in Slack threads to discuss code changes before creating PRs.
- **AI-Powered Code Suggestions**: Leverages SpoonOS's CodingAgent for smart code generation and modifications.
- **Efficient Caching**: Single AI call per conversation ensures consistent and cost-effective code previews.
- **Comprehensive Codebase Access**: The bot processes the entire repository to ensure context-aware code generation.
- **Organized Threaded Conversations**: All interactions occur within Slack threads, maintaining organized and coherent discussions.
- **User Notifications**: The bot actively tags users to ensure they receive pertinent updates and notifications.
- **Concrete Code Changes**: The bot proposes clear and actionable code changes without requiring additional clarifications.
- **Direct PR Creation**: PRs are generated only upon explicit commands, ensuring user control over the process.
- **Consistency in Preview and PR**: The same AI-generated code is used for both previews and PRs, ensuring reliability.

## Architecture Overview

### Single AI System Approach

1. **User Request**: Initiated via a user mention with a specific task.
2. **AI Code Generation**: SpoonOS generates and formats code for Slack.
3. **Preview and Cache**: Code is previewed and cached for subsequent PR creation.
4. **Explicit PR Command**: Users initiate PR creation through a direct command or button click.

### Benefits

- **Reliability**: Ensures identical preview and PR code, reducing discrepancies.
- **Speed**: Eliminates the need for a second AI call during PR creation.
- **Cost Efficiency**: Minimizes AI usage by limiting calls to one per conversation.

## Setup Instructions

### Prerequisites

- Python 3.8+
- A Slack workspace with admin privileges.
- An existing GitHub repository.
- An active OpenAI API key for SpoonOS functionality.

### Installation and Configuration

1. **Set Up Python Environment**:
   - Create and activate a virtual environment.
   - Install necessary dependencies and SpoonOS from GitHub.

2. **Configure Slack App**:
   - Create a new app and enable Socket Mode.
   - Set up necessary OAuth scopes and event subscriptions.

3. **GitHub Configuration**:
   - Generate a personal access token with the required scopes.
   - Store all sensitive information, including tokens, within a `.env` file.

4. **Running the Bot**:
   - Execute the main script `slack_bot.py` to start the bot.
   - Verify successful startup through terminal messages.

## Usage Guide

### Engaging with the Bot

1. **Initiate a Request**: Mention the bot with a task, e.g., "Create a login page."
2. **Receive Proposals**: The bot responds with a changeset of proposed code modifications.
3. **Refine and Confirm**: Users can request further changes before finalizing the PR.
4. **Create a PR**: Use the command "make PR" or the provided button to initiate PR creation.

### PR Management

- **Merge**: Command the bot to merge a PR by specifying the PR number.
- **Revert**: Similarly, revert merged PRs if needed.

## Developer Information

### Project Structure

- **slack_bot.py**: Manages Slack interactions and conversation states.
- **github_helper.py**: Handles GitHub API operations, including branch management and PR creation.
- **ai_agent.py**: Interfaces with SpoonOS for AI-driven code generation.

### Contribution Guidelines

1. Fork the repository and make changes in a separate branch.
2. Submit a pull request for review.

## Support and Troubleshooting

For any issues or inquiries:
- Refer to the existing troubleshooting guide.
- Verify correct configuration of Slack and environment variables.
- Ensure proper installation of all dependencies.

## License

This project is licensed under the MIT License. Feel free to use and adapt the code as needed.