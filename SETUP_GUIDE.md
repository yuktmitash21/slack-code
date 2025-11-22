# Quick Setup Guide

## Part 1: Create Python Virtual Environment

### On macOS/Linux:

1. **Navigate to your project folder:**
```bash
cd /Users/yuktmitash/Documents/slack-bot
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
```

3. **Activate the virtual environment:**
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **When you're done working, deactivate:**
```bash
deactivate
```

### On Windows:

1. **Create virtual environment:**
```cmd
python -m venv venv
```

2. **Activate:**
```cmd
venv\Scripts\activate
```

3. **Install dependencies:**
```cmd
pip install -r requirements.txt
```

---

## Part 2: Get Slack Environment Variables

### Step-by-Step Guide to Get Your Tokens

### 1️⃣ Create Your Slack App

1. Go to: https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter app name: `ContextBot` (or any name you like)
5. Choose your workspace
6. Click **"Create App"**

---

### 2️⃣ Get SLACK_SIGNING_SECRET

**While still on the app page:**

1. You should be on **"Basic Information"** page (if not, click it in the left sidebar)
2. Scroll down to **"App Credentials"** section
3. Find **"Signing Secret"**
4. Click **"Show"** and copy the value
5. ✅ This is your `SLACK_SIGNING_SECRET`

---

### 3️⃣ Enable Socket Mode & Get SLACK_APP_TOKEN

1. In the left sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to **ON**
3. A popup will appear asking for a token name
4. Enter: `Socket Token` (or any name)
5. Click **"Generate"**
6. **Copy the token** (starts with `xapp-...`)
7. ✅ This is your `SLACK_APP_TOKEN`
8. Click **"Done"**

---

### 4️⃣ Add Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
4. Add these scopes one by one:
   - `app_mentions:read`
   - `chat:write`
   - `channels:history`
   - `groups:history`
   - `users:read`

---

### 5️⃣ Subscribe to Events

1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. Scroll down to **"Subscribe to bot events"**
4. Click **"Add Bot User Event"**
5. Add these events:
   - `app_mention`
   - `message.channels` (optional)

6. Click **"Save Changes"** at the bottom

---

### 6️⃣ Install App & Get SLACK_BOT_TOKEN

1. In the left sidebar, click **"Install App"**
2. Click **"Install to Workspace"**
3. Review the permissions
4. Click **"Allow"**
5. You'll see **"Bot User OAuth Token"**
6. Click **"Copy"** button (token starts with `xoxb-...`)
7. ✅ This is your `SLACK_BOT_TOKEN`

---

### 7️⃣ Create Your .env File

1. In your project folder, create a file named `.env`
2. Add your three tokens:

```
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_APP_TOKEN=xapp-your-actual-token-here
SLACK_SIGNING_SECRET=your-actual-secret-here
```

**Replace the placeholder values with your actual tokens!**

---

## Part 3: Run the Bot

1. **Make sure your virtual environment is activated:**
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

2. **Run the bot:**
```bash
python slack_bot.py
```

3. **You should see:**
```
⚡️ Starting Slack bot in Socket Mode...
⚡️ Bolt app is running!
```

---

## Part 4: Test the Bot

1. Open your Slack workspace
2. Go to any channel
3. **Invite the bot to the channel:**
   ```
   /invite @ContextBot
   ```
   (Replace `ContextBot` with whatever you named your app)

4. **Mention the bot:**
   ```
   @ContextBot hello!
   ```

5. The bot should respond with context from the channel! 🎉

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure you activated the venv and installed dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### "SLACK_BOT_TOKEN not found"
- Make sure your `.env` file is in the project root folder
- Make sure there are no spaces around the `=` sign
- Make sure you copied the complete token

### Bot doesn't respond
- Make sure the bot is running (`python slack_bot.py`)
- Invite the bot to the channel (`/invite @BotName`)
- Check you added all the required permissions in step 4
- After adding permissions, you may need to reinstall the app

### Token looks wrong
- `SLACK_BOT_TOKEN` starts with `xoxb-`
- `SLACK_APP_TOKEN` starts with `xapp-`
- `SLACK_SIGNING_SECRET` is a shorter hex string

---

## Summary Checklist

- [ ] Created virtual environment
- [ ] Activated virtual environment
- [ ] Installed requirements.txt
- [ ] Created Slack app at api.slack.com/apps
- [ ] Got SLACK_SIGNING_SECRET from Basic Information
- [ ] Enabled Socket Mode and got SLACK_APP_TOKEN
- [ ] Added bot scopes (app_mentions:read, chat:write, channels:history, users:read)
- [ ] Subscribed to app_mention event
- [ ] Installed app to workspace and got SLACK_BOT_TOKEN
- [ ] Created .env file with all three tokens
- [ ] Ran python slack_bot.py
- [ ] Invited bot to a channel
- [ ] Tested by mentioning the bot

---

Need help? Double-check each step above! 🚀

