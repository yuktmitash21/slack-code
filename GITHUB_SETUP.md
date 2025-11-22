# GitHub Integration Setup Guide

This guide will help you set up GitHub integration so your Slack bot can create pull requests.

## Prerequisites

- A GitHub account
- A repository you want the bot to create PRs against (e.g., https://github.com/yuktmitash21/slack-code)
- Admin or write access to that repository

## Step 1: Create a GitHub Personal Access Token

1. **Go to GitHub Settings:**
   - Click your profile picture (top right) → **Settings**
   - Or visit: https://github.com/settings/profile

2. **Navigate to Developer Settings:**
   - Scroll down in the left sidebar
   - Click **Developer settings** (at the bottom)

3. **Create Personal Access Token:**
   - Click **Personal access tokens** → **Tokens (classic)**
   - Click **Generate new token** → **Generate new token (classic)**

4. **Configure Token:**
   - **Note:** `Slack Bot PR Creator` (or any descriptive name)
   - **Expiration:** Choose your preference (90 days, 1 year, or no expiration)
   - **Select scopes:** Check these boxes:
     - ✅ **repo** (Full control of private repositories)
       - This automatically checks all sub-items
     - ✅ **workflow** (Update GitHub Action workflows)

5. **Generate and Copy:**
   - Scroll down and click **Generate token**
   - **⚠️ IMPORTANT:** Copy the token immediately! You won't see it again.
   - The token starts with `ghp_`
   - Save it somewhere safe temporarily (you'll add it to `.env` next)

## Step 2: Configure Your Repository

The bot needs to know which repository to create PRs against.

Your repository format should be: `owner/repo-name`

**Examples:**
- `yuktmitash21/slack-code`
- `octocat/Hello-World`
- `your-username/your-repo`

## Step 3: Update Your .env File

Add the GitHub configuration to your `.env` file:

```bash
# Add these lines to your existing .env file

# GitHub Configuration
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_REPO=yuktmitash21/slack-code
```

**Example complete .env file:**

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx
SLACK_APP_TOKEN=xapp-1-A01ABCDEFGH-1234567890-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrs
SLACK_SIGNING_SECRET=1234567890abcdef1234567890abcdef

# GitHub Configuration
GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
GITHUB_REPO=yuktmitash21/slack-code
```

## Step 4: Install Additional Dependencies

The GitHub integration requires additional Python packages:

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Install/update requirements
pip install -r requirements.txt
```

This will install:
- `PyGithub` - GitHub API library
- `gitpython` - Git operations library

## Step 5: Restart Your Bot

```bash
# Stop the bot if it's running (Ctrl+C)

# Start it again
python slack_bot.py
```

You should see:
```
⚡️ Starting Slack bot in Socket Mode...
GitHub integration enabled
⚡️ Bolt app is running!
```

## Step 6: Test PR Creation

### In Slack:

1. **Invite the bot to a channel** (if not already):
   ```
   /invite @YourBotName
   ```

2. **Ask the bot to create a PR:**
   ```
   @BotName create a PR for adding user authentication
   ```

3. **Other command variations:**
   ```
   @BotName make a pull request for bug fix
   @BotName open a PR to refactor database code
   @BotName submit a PR for new feature
   @BotName generate a pull request for documentation updates
   ```

### What Happens:

1. The bot acknowledges your request
2. It creates a new branch with a timestamp (e.g., `bot-task-20251122-143045`)
3. It makes a random change to demonstrate functionality:
   - Adds a comment to README, OR
   - Creates a task log file, OR
   - Updates a bot statistics file
4. It creates a pull request with:
   - Your task description in the title
   - Detailed PR description
   - Changes made
   - Timestamp

5. The bot responds with PR details including a link!

### Example Response:

```
✅ Pull Request Created Successfully!

📋 Task: adding user authentication
🔢 PR #: 42
🌿 Branch: bot-task-20251122-143045
🔗 URL: https://github.com/yuktmitash21/slack-code/pull/42

📝 Changes: Created new file: bot_tasks/task_20251122-143045.txt

The PR is ready for review! 🎉
```

## How It Works

### Current Behavior (Placeholder Implementation)

Right now, the bot creates **random PRs** to demonstrate the functionality. When you ask it to create a PR, it will:

1. Create a new branch from `main`
2. Make one of these random changes:
   - Add a timestamped comment to `README.md`
   - Create a new task log file in `bot_tasks/` directory
   - Update or create a `BOT_STATS.md` file tracking all tasks

### Future Implementation

Later, you can extend the bot to:
- Parse the task description and generate actual code
- Integrate with AI/LLM to write code based on the task
- Read existing code and make intelligent modifications
- Run tests before creating the PR
- Add more sophisticated code generation logic

## Repository Structure After Use

After the bot creates a few PRs, your repository might have:

```
your-repo/
├── README.md (with timestamped comments)
├── BOT_STATS.md (tracking all bot tasks)
├── bot_tasks/
│   ├── task_20251122-143045.txt
│   ├── task_20251122-150230.txt
│   └── task_20251122-163015.txt
└── ... your other files
```

## Troubleshooting

### "GitHub integration is not configured"

**Problem:** Bot responds that GitHub is not configured.

**Solutions:**
1. Check your `.env` file has both `GITHUB_TOKEN` and `GITHUB_REPO`
2. Make sure there are no spaces around the `=` sign
3. Restart the bot after adding the variables
4. Check the bot startup logs for errors

### "GitHub API error: Bad credentials"

**Problem:** GitHub token is invalid or expired.

**Solutions:**
1. Generate a new token following Step 1
2. Make sure you copied the entire token (starts with `ghp_`)
3. Update `.env` with the new token
4. Restart the bot

### "GitHub API error: Not Found"

**Problem:** Repository name is incorrect or bot doesn't have access.

**Solutions:**
1. Verify `GITHUB_REPO` format is `owner/repo-name`
2. Check the repository exists and is accessible
3. Ensure your token has `repo` scope access
4. If it's a private repo, make sure the token has full `repo` access

### "GitHub API error: Resource not accessible by integration"

**Problem:** Token doesn't have required permissions.

**Solutions:**
1. Regenerate token with `repo` and `workflow` scopes checked
2. Make sure you're using a Personal Access Token (classic)
3. Update `.env` with the new token

### PRs are created but changes seem random

**This is expected!** The current implementation creates placeholder PRs to demonstrate functionality. The actual coding logic will be implemented later based on your needs.

### Bot creates branch but fails to create PR

**Problem:** Often a permissions issue.

**Solutions:**
1. Make sure you have write access to the repository
2. Check if branch protection rules are blocking bot PRs
3. Verify the default branch name matches your repo (main vs master)

## Security Best Practices

### Token Security

- ✅ **DO:** Keep your token in `.env` file
- ✅ **DO:** Add `.env` to `.gitignore`
- ✅ **DO:** Set token expiration (90 days recommended)
- ✅ **DO:** Regenerate token if compromised

- ❌ **DON'T:** Commit token to Git
- ❌ **DON'T:** Share token in Slack or other channels
- ❌ **DON'T:** Use a token with more permissions than needed
- ❌ **DON'T:** Use your personal token for production bots (use GitHub Apps instead)

### Repository Access

- Only give the bot access to repositories it needs
- Consider using a dedicated bot account for production use
- Review PR permissions and branch protection rules
- Monitor bot activity through GitHub audit logs

## Customization Ideas

Once you have the basic setup working, you can customize:

1. **Change Types:**
   - Modify `github_helper.py` to add new change types
   - Implement actual code generation logic
   - Integrate with AI for intelligent code writing

2. **PR Templates:**
   - Customize `_generate_pr_description()` method
   - Add labels, reviewers, or assignees automatically
   - Include testing results or screenshots

3. **Validation:**
   - Add code linting before creating PR
   - Run tests on the new branch
   - Check for conflicts with base branch

4. **Notifications:**
   - Send Slack notifications when PR is reviewed
   - Update thread when PR is merged
   - Create summary reports of bot activity

## Next Steps

Now that GitHub integration is set up:

1. ✅ Test creating a few PRs with different task descriptions
2. ✅ Review the generated PRs on GitHub
3. ✅ Merge or close the test PRs
4. 🔧 Start planning the actual code generation logic
5. 🤖 Consider integrating AI/LLM for intelligent code generation

## Reference Links

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [GitHub API Reference](https://docs.github.com/en/rest)

---

Questions? Issues? Check the main README or open an issue! 🚀

