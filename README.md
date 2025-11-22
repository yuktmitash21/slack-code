# Slack Bot with Channel Context & GitHub Integration

A Slack bot that responds to mentions (@bot) and provides full context from the channel conversation. The bot can access recent messages from both the channel and any thread it's mentioned in. It can also create GitHub pull requests on demand!

## Features

- 🤖 Responds when mentioned with `@bot`
- 📚 Accesses and displays recent channel messages (up to 50)
- 🧵 Understands thread context when mentioned in a thread
- 📝 Shows formatted conversation history with timestamps and usernames
- ⚡️ Uses Socket Mode for real-time communication (no public URL needed)
- 🔧 **NEW:** Creates GitHub pull requests when given a task
- 🚀 **NEW:** Integrates with GitHub API for automated PR creation

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have permission to install apps
- (Optional) A GitHub account and repository for PR creation feature

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
3. Under **"Subscribe to bot events"**, add:
   - `app_mention` - When the bot is mentioned
   - `message.channels` - To monitor channel messages (optional, for logging)
   - `message.groups` - To monitor private channels (optional)

4. Click **"Save Changes"**

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
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore file
├── README.md            # This file
├── SETUP_GUIDE.md       # Detailed Slack setup guide
└── GITHUB_SETUP.md      # GitHub integration setup guide
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
- Add AI/LLM integration to generate intelligent code based on context
- Store conversation history in a database
- Add sentiment analysis
- Implement custom commands
- Add support for direct messages
- Parse task descriptions to generate actual code changes
- Add automated testing before PR creation

## License

This project is open source and available under the MIT License.

## Support

For issues with:
- **Slack API**: Check [Slack API Documentation](https://api.slack.com/docs)
- **slack-bolt**: See [Bolt for Python Documentation](https://slack.dev/bolt-python/concepts)
- **This bot**: Open an issue in the repository

---

Happy botting! 🤖

