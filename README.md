# Slack Bot with Channel Context & GitHub Integration

A Slack bot that responds to mentions (@bot) and provides full context from the channel conversation. The bot can access recent messages from both the channel and any thread it's mentioned in. It can also create GitHub pull requests on demand!

## Features

- 🤖 Responds when mentioned with `@bot`
- 📚 Accesses and displays recent channel messages (up to 50)
- 🧵 Understands thread context when mentioned in a thread
- 📝 Shows formatted conversation history with timestamps and usernames
- ⚡️ Uses Socket Mode for real-time communication (no public URL needed)
- 🔧 **NEW:** Creates GitHub pull requests when given a task
- 🔀 **NEW:** Merges pull requests directly from Slack
- ↩️ **NEW:** Reverts/unmerges PRs by creating revert PRs
- 🤖 **NEW:** AI-powered code generation using OpenAI
- 📖 **NEW:** Full codebase context - AI agent reads entire repository before making changes
- 🎯 **NEW:** Context-aware code generation that integrates seamlessly with existing code
- 📝 **NEW:** Changeset format - every response shows exactly what files/code will be created
- ✏️ **NEW:** File modifications - edits existing files while preserving existing code
- 💬 **NEW:** Iterative refinement - provide feedback to update the changeset before creating PR
- 🚀 **NEW:** Full GitHub API integration for PR lifecycle management

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have permission to install apps
- (Optional) A GitHub account and repository for PR creation feature
- (Optional) OpenAI API key for AI code generation

## Setup Instructions

### 1. Create a Slack App

1. Go to [Slack API Apps page](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Give your app a name (e.g., "Context Bot") and select your workspace
5. Click **"Create App"**

### 2. Configure App Permissions

1. In your app settings, go to **"OAuth & Permissions"** in the sidebar
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Add the following scopes:
   - `app_mentions:read` - To receive mentions
   - `chat:write` - To send messages
   - `channels:history` - To read channel messages
   - `groups:history` - To read private channel messages
   - `im:history` - To read direct messages (optional)
   - `mpim:history` - To read group direct messages (optional)
   - `users:read` - To get user information

### 3. Enable Socket Mode

1. Go to **"Socket Mode"** in the sidebar
2. Toggle **"Enable Socket Mode"** to ON
3. Give your token a name (e.g., "Socket Token")
4. Click **"Generate"**
5. Copy the token (starts with `xapp-`) - this is your `SLACK_APP_TOKEN`

### 4. Subscribe to Events

1. Go to **"Event Subscriptions"** in the sidebar
2. Toggle **"Enable Events"** to ON
3. Under **"Subscribe to bot events"**, add these **REQUIRED** events:

   - `app_mention` - When the bot is mentioned (**REQUIRED**)
   - `message.channels` - To receive replies in threads (**REQUIRED for conversations**)
   - `message.groups` - To work in private channels (optional)
   - `message.im` - To work in DMs (optional)

4. Click **"Save Changes"**

⚠️ **Important**: Without `message.channels`, the bot won't respond to your follow-up messages in threads!

### 5. Install the App to Your Workspace

1. Go to **"Install App"** in the sidebar
2. Click **"Install to Workspace"**
3. Review the permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`) - this is your `SLACK_BOT_TOKEN`

### 6. Get Your Signing Secret

1. Go to **"Basic Information"** in the sidebar
2. Scroll down to **"App Credentials"**
3. Copy the **"Signing Secret"** - this is your `SLACK_SIGNING_SECRET`

### 7. Set Up the Bot Locally

1. Clone or download this repository

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your credentials:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Optional: For GitHub PR creation
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_REPO=username/repository-name
```

**Note:** GitHub integration is optional. See [GITHUB_SETUP.md](GITHUB_SETUP.md) for detailed setup instructions.

4. Run the bot:

```bash
python slack_bot.py
```

You should see:

```
⚡️ Starting Slack bot in Socket Mode...
⚡️ Bolt app is running!
```

## Usage

### Basic Context Responses

In any channel where the bot is invited:

1. Type `@YourBotName hello` (replace with your bot's name)
2. The bot will respond with:
   - Your original message
   - Recent messages from the thread (if in a thread)
   - Recent messages from the channel
   - Total number of messages it has access to

### Example Interaction

```
User: @ContextBot what's the status on the project?

Bot: Hi @User! I've been mentioned and I have context from the channel.

Your message: @ContextBot what's the status on the project?

📚 Recent Channel Messages:
  [2025-11-22 10:15:30] Alice: We finished the design phase
  [2025-11-22 10:20:15] Bob: Starting development next week
  [2025-11-22 10:25:45] Charlie: Budget approved!
  [2025-11-22 10:30:20] User: @ContextBot what's the status on the project?

I have access to the last 25 messages from this channel.

💡 Tip: You can ask me to create a PR for [task description] to generate a pull request!
```

### Creating GitHub Pull Requests

If you've set up GitHub integration (see [GITHUB_SETUP.md](GITHUB_SETUP.md)), you can ask the bot to create pull requests:

```
User: @ContextBot create a PR for adding user authentication

Bot: 🤖 Got it @User! Creating a pull request for: adding user authentication

Please wait...

[A moment later...]

✅ Pull Request Created Successfully!

📋 Task: adding user authentication
🔢 PR #: 42
🌿 Branch: bot-task-20251122-143045
🔗 URL: https://github.com/yuktmitash21/slack-code/pull/42

📝 Changes: Created new file: bot_tasks/task_20251122-143045.txt

The PR is ready for review! 🎉
```

**Other PR command variations:**

- `@BotName make a pull request for bug fix`
- `@BotName open a PR to refactor database code`
- `@BotName submit a PR for new feature`
- `@BotName generate a pull request for documentation updates`

### Merging Pull Requests

Once a PR is created (or if you have existing PRs), you can merge them directly from Slack:

```
User: @ContextBot merge PR 42

Bot: 🔄 Got it @User! Merging PR #42 using merge method...

Please wait...

[A moment later...]

✅ Pull Request Merged Successfully!

🔢 PR #: 42
📋 Title: 🤖 Bot Task: adding user authentication
🌿 Branch: bot-task-20251122-143045
🔀 Merge Method: merge
🔗 URL: https://github.com/yuktmitash21/slack-code/pull/42

The changes have been merged to master! 🎉
```

**Merge command variations:**

- `@BotName merge PR 42` - Standard merge
- `@BotName merge #42` - Using # notation
- `@BotName merge 42` - Simple format
- `@BotName merge PR 42 squash` - Squash and merge
- `@BotName merge PR 42 rebase` - Rebase and merge

**Merge Methods:**

- **merge** (default): Creates a merge commit
- **squash**: Squashes all commits into one
- **rebase**: Rebases and merges commits

### Reverting/Unmerging Pull Requests

If you need to undo a merged PR, you can create a revert PR:

```
User: @ContextBot unmerge PR 42

Bot: 🔄 Got it @User! Creating a revert PR for #42...

Please wait...

[A moment later...]

✅ Revert Pull Request Created Successfully!

🔄 Reverting PR #: 42
📋 Original Title: 🤖 Bot Task: adding user authentication
🔗 Original PR: https://github.com/yuktmitash21/slack-code/pull/42

**New Revert PR:**
🔢 PR #: 45
🌿 Branch: revert-pr-42-20251122-150045
🔗 URL: https://github.com/yuktmitash21/slack-code/pull/45

The revert PR is ready for review! You can now merge it to undo the original changes.

💡 Tip: Merge it with @bot merge PR 45
```

**Unmerge command variations:**

- `@BotName unmerge PR 42` - Create revert PR
- `@BotName revert PR 42` - Same as unmerge
- `@BotName unmerge #42` - Using # notation
- `@BotName revert 42` - Simple format

**How it works:**

1. Clones the repository to a temporary directory
2. Creates a new branch with name `revert-pr-{number}-{timestamp}`
3. Executes `git revert -m 1 <merge_commit_sha>` to create actual revert commits
4. Pushes the revert branch to GitHub
5. Opens a new PR with the actual reverted code
6. You can then merge the revert PR to complete the undo
7. Cleans up temporary directory

**Technical Details:**

- Uses `gitpython` library for git operations
- Properly handles merge commits with `-m 1` flag
- Creates real revert commits that can be merged safely

## How It Works

### Context Gathering

The bot uses two methods to gather context:

1. **Channel Context** (`get_channel_context`):

   - Fetches up to 50 recent messages from the channel
   - Filters out bot messages and system messages
   - Formats messages with timestamps and usernames

2. **Thread Context** (`get_thread_context`):
   - If mentioned in a thread, fetches all messages in that thread
   - Provides focused context for threaded conversations

### Event Handling

- The bot listens for `app_mention` events
- When mentioned, it gathers context and formulates a response
- Responses are sent in the same thread if the mention was in a thread

## Project Structure

```
slack-bot/
├── slack_bot.py          # Main bot application
├── github_helper.py      # GitHub PR creation logic
├── ai_agent.py           # AI code generation (SpoonOS)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore file
├── README.md            # This file
├── SETUP_GUIDE.md       # Detailed Slack setup guide
├── GITHUB_SETUP.md      # GitHub integration setup guide
├── AI_AGENT_SETUP.md    # AI code generation setup
├── COMMANDS.md          # Command reference
└── QUICK_START.md       # Quick start guide
```

## Troubleshooting

### Bot doesn't respond to mentions

- Verify the bot is invited to the channel (`/invite @YourBotName`)
- Check that the bot is running (`python slack_bot.py`)
- Verify all three environment variables are set correctly in `.env`
- Check the app has the required permissions in Slack API settings

### "SLACK_APP_TOKEN not found" error

- Make sure you've enabled Socket Mode in your app settings
- Verify the `.env` file exists and contains `SLACK_APP_TOKEN=xapp-...`

### Bot can't read message history

- Ensure you've added the history scopes: `channels:history`, `groups:history`
- After adding scopes, reinstall the app to your workspace
- The bot must be a member of the channel to read its history

### Merge command fails

- Verify the PR number exists and is correct
- Check that the PR is not already merged or closed
- Ensure the PR has no merge conflicts
- Verify your GitHub token has write access to the repository
- Make sure branch protection rules allow the merge

### Unmerge/revert command fails

- Verify the PR number exists and was merged
- Only merged PRs can be reverted
- Check your GitHub token has write access to create branches and PRs
- If the revert PR is created but empty, you may need to manually add the revert commits

### Connection issues

- Socket Mode requires a stable internet connection
- If the bot disconnects frequently, check your network
- The bot will automatically reconnect in most cases

## Customization

### Adjust Context Length

In `slack_bot.py`, modify the `limit` parameter:

```python
# Fetch last 100 messages instead of 50
channel_context = get_channel_context(client, channel_id, limit=100)
```

### Change Response Format

Modify the response building section in `handle_app_mention`:

```python
response = f"Hi <@{user_id}>! Custom message here.\n\n"
# Add your custom formatting
```

### Add More Event Handlers

Add new event handlers for different Slack events:

```python
@app.event("reaction_added")
def handle_reaction(event, say):
    # Handle reaction events
    pass
```

## Security Notes

- Never commit your `.env` file to version control
- Keep your tokens secure and rotate them if compromised
- Use environment variables for all sensitive data
- The `.env` file is already in `.gitignore` to prevent accidental commits

## GitHub PR Feature

The bot can now create GitHub pull requests! Currently, it creates placeholder PRs with random changes to demonstrate the functionality.

**Current behavior:**

- Creates a new branch
- Makes a random change (adds comment to README, creates task log, or updates bot stats)
- Opens a pull request with your task description

**Future enhancements:**

- Parse task descriptions to generate actual code
- Integrate with AI/LLM for intelligent code generation
- Read existing code and make contextual modifications
- Run tests before creating PRs

See [GITHUB_SETUP.md](GITHUB_SETUP.md) for complete setup instructions.

## Contributing

Feel free to fork this project and customize it for your needs. Some ideas for enhancements:

- ✅ **GitHub PR creation** (implemented!)
- ✅ **AI code generation with SpoonOS** (implemented!)
- Store conversation history in a database
- Add sentiment analysis
- Implement custom commands
- Add support for direct messages
- Enhanced AI with deeper repository analysis
- Add automated testing before PR creation
- Integrate more SpoonOS tools (crypto, DeFi, etc.)

## License

This project is open source and available under the MIT License.

## Support

For issues with:

- **Slack API**: Check [Slack API Documentation](https://api.slack.com/docs)
- **slack-bolt**: See [Bolt for Python Documentation](https://slack.dev/bolt-python/concepts)
- **This bot**: Open an issue in the repository

---

Happy botting! 🤖
