# GitHub OAuth Setup Guide

This guide shows you how to set up GitHub OAuth so users can authenticate with their own GitHub accounts.

## Why OAuth Instead of Shared Token?

✅ **Security**: Each user uses their own credentials  
✅ **Privacy**: Users control what repos the bot can access  
✅ **Permissions**: PRs are created under each user's account  
✅ **Audit Trail**: Clear who made each change

## Step 1: Create a GitHub OAuth App

1. Go to **GitHub Settings** → **Developer settings** → **OAuth Apps**

   - Or visit: https://github.com/settings/developers

2. Click **"New OAuth App"**

3. Fill in the details:

   ```
   Application name: Slack Code Bot (or your preferred name)
   Homepage URL: https://your-ngrok-url.ngrok-free.app
   Application description: AI-powered coding bot for Slack
   Authorization callback URL: https://your-ngrok-url.ngrok-free.app/auth/github/callback
   ```

4. Click **"Register application"**

5. You'll see your **Client ID** - copy this

6. Click **"Generate a new client secret"**

7. Copy the **Client Secret** (you can only see it once!)

## Step 2: Configure Environment Variables

Add these to your `.env` file:

```bash
# GitHub OAuth (for per-user authentication)
GITHUB_OAUTH_CLIENT_ID=Ov23liNNPp2553pVK8aM
GITHUB_OAUTH_CLIENT_SECRET=2617e7da38be8d3e9173be8c692112b26345bc58
GITHUB_OAUTH_CALLBACK_URL=https://60964e6236f1.ngrok-free.app/auth/github/callback

# You can remove these old ones if you're not using them:
# GITHUB_TOKEN=...  (not needed anymore)
# GITHUB_REPO=...   (users set their own)
```

## Step 3: Set Up Ngrok (for Public Callback URL)

If you're running locally, you need a public URL for OAuth callbacks:

```bash
# Install ngrok
brew install ngrok

# Start ngrok on port 5050
ngrok http 5050
```

Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and update:

- Your `.env` file: `GITHUB_OAUTH_CALLBACK_URL`
- Your GitHub OAuth App settings: Authorization callback URL

## Step 4: Run the Bot

The bot now includes the OAuth server built-in! **Just run one command:**

```bash
python slack_bot.py
```

You should see:

```
============================================================
🚀 Slack Bot with GitHub OAuth
============================================================
📍 OAuth Callback: http://localhost:5050/auth/github/callback
🏥 Health Check: http://localhost:5050/health
⚡️ Slack Bot: Starting Socket Mode...
============================================================
```

**No need for `oauth_server.py` anymore - everything runs in one process!**

## Step 5: Test the Flow

1. **Mention the bot** in Slack:

   ```
   @bot hello
   ```

2. **You'll see an authentication prompt**:

   - Click "Connect GitHub Account"
   - Authorize the app on GitHub
   - You'll be redirected back with a success message

3. **Set your default repository**:

   ```
   @bot set repo your-username/your-repo
   ```

4. **Check your connection**:

   ```
   @bot github status
   ```

5. **Start using the bot**:
   ```
   @bot create a login page
   ```

## User Commands

### Authentication Management

```bash
# Check connection status
@bot github status

# Set default repository
@bot set repo owner/repository

# Disconnect GitHub account
@bot disconnect github
```

### Regular Bot Commands

Once authenticated, all normal commands work:

```bash
# Create PRs
@bot add authentication to the app

# Merge PRs
@bot merge PR 123

# Revert PRs
@bot revert PR 45

# View usage
@bot show my usage
```

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│             │         │              │         │             │
│  Slack Bot  │────────▶│ OAuth Server │────────▶│   GitHub    │
│  (port N/A) │         │ (port 5050)  │         │   OAuth     │
│             │         │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │                        │                        │
       └────────────────────────┴────────────────────────┘
                                 │
                          ┌──────▼───────┐
                          │ User Tokens  │
                          │ (JSON file)  │
                          └──────────────┘
```

## Troubleshooting

### "Callback URL not found"

- Make sure `oauth_server.py` is running
- Verify the ngrok URL matches your `.env` and GitHub OAuth app settings

### "User not authenticated"

- User needs to click the "Connect GitHub Account" button
- Check that the OAuth flow completed successfully

### "Invalid client credentials"

- Verify `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` in `.env`
- Make sure you copied them correctly from GitHub

### "Repository not found"

- User needs to set their default repo: `@bot set repo owner/repo`
- Repository must exist and user must have access to it

## Security Notes

- ✅ User tokens are stored in `data/user_github_tokens.json` (excluded from git)
- ✅ OAuth state parameter prevents CSRF attacks
- ✅ Each user's token has scopes: `repo` and `user:email`
- ✅ Users can revoke access anytime: https://github.com/settings/applications

## Migration from Shared Token

If you're upgrading from a shared `GITHUB_TOKEN`:

1. All users need to authenticate individually
2. Each user sets their own default repo
3. PRs will be created under each user's account
4. Old `.env` variables (`GITHUB_TOKEN`, `GITHUB_REPO`) are no longer used

## Production Deployment

For production, replace ngrok with a permanent public URL:

1. Deploy `oauth_server.py` to a server (Heroku, AWS, etc.)
2. Use a real domain (e.g., `https://bot.yourcompany.com`)
3. Update GitHub OAuth app callback URL
4. Update `GITHUB_OAUTH_CALLBACK_URL` in `.env`

---

🎉 That's it! Users can now authenticate with their own GitHub accounts.
