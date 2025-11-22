# Quick Start Guide

## Get Your Bot Running in 5 Minutes

### 1. Install Dependencies

```bash
cd /Users/yuktmitash/Documents/slack-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create .env File

Create a file named `.env` in the project root:

```bash
# Required: Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Optional: GitHub PR Creation
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_REPO=yuktmitash21/slack-code
```

### 3. Get Slack Tokens

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions, or quick version:

1. Go to https://api.slack.com/apps
2. Create new app → From scratch
3. Get signing secret from Basic Information
4. Enable Socket Mode → Get app token (xapp-)
5. Add bot scopes: `app_mentions:read`, `chat:write`, `channels:history`, `users:read`
6. Subscribe to events: `app_mention`
7. Install to workspace → Get bot token (xoxb-)

### 4. (Optional) Set Up GitHub Integration

See [GITHUB_SETUP.md](GITHUB_SETUP.md) for detailed instructions, or quick version:

1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Check `repo` and `workflow` scopes
4. Copy token (starts with ghp_)
5. Add to `.env` with your repo name

### 5. Run the Bot

```bash
python slack_bot.py
```

You should see:
```
⚡️ Starting Slack bot in Socket Mode...
GitHub integration enabled  # (if configured)
⚡️ Bolt app is running!
```

### 6. Test in Slack

```
# Invite bot to channel
/invite @YourBotName

# Get context
@BotName hello!

# Create a PR (if GitHub configured)
@BotName create a PR for adding user authentication
```

## Common Commands

### Context Queries
```
@BotName what's been discussed?
@BotName give me context
@BotName hello
```

### PR Creation
```
@BotName create a PR for [task]
@BotName make a pull request for [task]
@BotName open a PR to [task]
```

## Troubleshooting

### Bot doesn't start
- Check all three Slack env variables are set
- Verify tokens have no extra spaces
- Make sure venv is activated

### Bot doesn't respond
- Invite bot to the channel: `/invite @BotName`
- Check bot is running in terminal
- Verify event subscriptions are enabled

### GitHub not working
- Check both GITHUB_TOKEN and GITHUB_REPO are set
- Verify token has `repo` scope
- Ensure repo name format is `owner/repo`
- Restart bot after adding GitHub variables

## What's Next?

- ✅ Bot responds with channel context
- ✅ Bot creates placeholder PRs
- 🔜 Implement actual code generation logic
- 🔜 Add AI integration for intelligent responses

Happy botting! 🚀

