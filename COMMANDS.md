# Bot Commands Reference

Quick reference for all available Slack bot commands.

## Context Commands

Get channel and thread context:

```
@BotName hello
@BotName what's been discussed?
@BotName give me the context
```

**What it does:** Shows the last 30 messages from the channel and thread context if applicable.

---

## GitHub PR Commands

### Create a Pull Request

Create a new PR with a task description:

```
@BotName create a PR for [task description]
@BotName make a pull request for [task description]
@BotName open a PR to [task description]
@BotName submit a PR for [task description]
@BotName generate a pull request for [task description]
```

**Examples:**

```
@BotName create a PR for adding user authentication
@BotName make a pull request for fixing login bug
@BotName open a PR to refactor database code
```

**What it does:**

1. Creates a new branch (e.g., `bot-task-20251122-143045`)
2. Makes a change (currently placeholder, will be actual code in the future)
3. Opens a pull request with your task description
4. Returns PR number and URL

---

### Merge a Pull Request

Merge an existing PR:

```
@BotName merge PR [number]
@BotName merge #[number]
@BotName merge [number]
```

**With merge methods:**

```
@BotName merge PR 42               # Standard merge (default)
@BotName merge PR 42 squash        # Squash commits
@BotName merge PR 42 rebase        # Rebase and merge
```

**Examples:**

```
@BotName merge PR 42
@BotName merge #15
@BotName merge 23 squash
```

**What it does:**

1. Validates the PR exists and is mergeable
2. Checks for conflicts
3. Merges the PR using the specified method
4. Confirms when merged

**Merge Methods:**

- **merge** (default): Creates a merge commit, preserves all individual commits
- **squash**: Combines all commits into one before merging
- **rebase**: Rebases commits onto base branch, then fast-forwards

---

### Revert/Unmerge a Pull Request

Create a revert PR to undo a merged PR:

```
@BotName unmerge PR [number]
@BotName revert PR [number]
@BotName unmerge #[number]
@BotName revert [number]
```

**Examples:**

```
@BotName unmerge PR 42
@BotName revert PR 15
@BotName unmerge #23
```

**What it does:**

1. Verifies the PR was merged
2. Clones the repository locally
3. Creates a new branch (e.g., `revert-pr-42-20251122-150045`)
4. Executes `git revert -m 1 <merge_commit_sha>` to create actual revert commits
5. Pushes the revert branch to GitHub
6. Opens a new "revert PR" with the actual reverted code
7. You can then merge the revert PR to complete the undo

**Important:**

- Only works on merged PRs
- Uses actual `git revert` command to properly undo changes
- Creates real revert commits, not placeholder files

---

## Complete Workflow Examples

### Example 1: Create and Merge

```
You: @BotName create a PR for adding user login feature

Bot: ✅ Pull Request Created Successfully!
     🔢 PR #: 42
     🔗 URL: https://github.com/your-repo/pull/42
     💡 Tip: You can merge it with @bot merge PR 42

You: @BotName merge PR 42

Bot: ✅ Pull Request Merged Successfully!
     The changes have been merged to master! 🎉
     💡 Tip: If you need to undo this, use @bot unmerge PR 42
```

### Example 2: Create, Merge, Then Revert

```
You: @BotName create a PR for experimental feature

Bot: ✅ Pull Request Created Successfully!
     🔢 PR #: 43

You: @BotName merge PR 43

Bot: ✅ Pull Request Merged Successfully!

[Later, you realize you need to undo this]

You: @BotName unmerge PR 43

Bot: ✅ Revert Pull Request Created Successfully!
     🔄 Reverting PR #: 43
     **New Revert PR:**
     🔢 PR #: 44
     💡 Tip: Merge it with @bot merge PR 44

You: @BotName merge PR 44

Bot: ✅ Pull Request Merged Successfully!
     The changes have been merged to master! 🎉
```

### Example 3: Squash Merge

```
You: @BotName create a PR for multiple small fixes

Bot: ✅ Pull Request Created Successfully!
     🔢 PR #: 50

You: @BotName merge PR 50 squash

Bot: ✅ Pull Request Merged Successfully!
     🔀 Merge Method: squash
     The changes have been merged to master! 🎉
```

---

## Error Handling

### Common Error Messages

**"GitHub integration is not configured"**

- Add `GITHUB_TOKEN` and `GITHUB_REPO` to your `.env` file
- See [GITHUB_SETUP.md](GITHUB_SETUP.md) for setup instructions

**"PR #X is already merged"**

- The PR was already merged, cannot merge again
- Use `unmerge` if you need to revert it

**"PR #X has merge conflicts"**

- Resolve conflicts manually on GitHub first
- Or close the PR and create a new one

**"PR #X is not merged yet"**

- When trying to unmerge: Only merged PRs can be reverted
- Merge the PR first, then you can revert it

**"PR #X is closed and cannot be merged"**

- The PR was closed without merging
- Reopen it on GitHub or create a new PR

---

## Command Syntax Summary

| Command      | Syntax                        | Description             |
| ------------ | ----------------------------- | ----------------------- |
| Context      | `@bot hello`                  | Get channel context     |
| Create PR    | `@bot create a PR for [task]` | Create new pull request |
| Merge PR     | `@bot merge PR [#]`           | Merge a pull request    |
| Squash Merge | `@bot merge PR [#] squash`    | Squash and merge        |
| Rebase Merge | `@bot merge PR [#] rebase`    | Rebase and merge        |
| Revert PR    | `@bot unmerge PR [#]`         | Create revert PR        |
| Revert PR    | `@bot revert PR [#]`          | Same as unmerge         |

---

## Tips

1. **Always check the PR on GitHub** before merging important changes
2. **Use squash merge** for PRs with many small commits to keep history clean
3. **Test the revert PR** before merging it to ensure it properly undoes changes
4. **Branch protection rules** on GitHub will still apply - bot respects them
5. **PR numbers** are returned after creating PRs - save them for later merging

---

## What's Next?

Current Status:

- ✅ Create PRs from Slack
- ✅ Merge PRs from Slack (3 methods)
- ✅ Revert/unmerge PRs from Slack

Coming Soon:

- 🔜 List open/merged PRs
- 🔜 Add comments to PRs
- 🔜 Close PRs without merging
- 🔜 Request reviewers
- 🔜 Actual code generation based on task descriptions
- 🔜 AI-powered intelligent code changes

---

For detailed setup and troubleshooting, see:

- [QUICK_START.md](QUICK_START.md) - Fast setup guide
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub integration
- [README.md](README.md) - Complete documentation
