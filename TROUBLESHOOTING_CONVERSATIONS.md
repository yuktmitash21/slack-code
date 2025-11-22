# Troubleshooting: Bot Not Responding to Follow-up Messages

## Problem

After the bot generates a changeset, you try to reply with feedback in the thread, but the bot doesn't respond.

## Root Cause

Your Slack app is missing the **`message.channels`** event subscription. Without this, Slack won't send your thread replies to the bot.

## Solution

### Step 1: Check Current Event Subscriptions

1. Go to https://api.slack.com/apps
2. Select your bot app
3. Click **"Event Subscriptions"** in the sidebar
4. Look at **"Subscribe to bot events"**

### Step 2: Add Required Events

You MUST have these events:

✅ **`app_mention`** - For initial @mentions
✅ **`message.channels`** - For thread replies (THIS IS THE ONE YOU'RE MISSING!)

Optional but recommended:
- `message.groups` - For private channels
- `message.im` - For direct messages

### Step 3: Add the Missing Event

1. Click **"Add Bot User Event"**
2. Search for `message.channels`
3. Click it to add
4. **IMPORTANT**: Click **"Save Changes"** at the bottom

### Step 4: Reinstall the App

⚠️ **CRITICAL STEP**: After changing events, you MUST reinstall:

1. Go to **"Install App"** in the sidebar
2. Click **"Reinstall to Workspace"**
3. Review permissions
4. Click **"Allow"**

Without reinstalling, the new events won't take effect!

### Step 5: Restart Your Bot

```bash
# Stop the bot (Ctrl+C)
# Start it again
python slack_bot.py
```

### Step 6: Test

1. **Start a new thread**: `@bot add a test function`
2. **Wait for changeset**: Bot should show proposed code
3. **Reply in the thread**: `add error handling`
4. **Bot should respond**: With updated changeset

## Verification

### Check Logs

When you reply in a thread, you should see:

```bash
📨 Message event received: ...
   User: U123456
   Text: add error handling
   Thread: 1234567890.123456
   Active conversations: ['1234567890.123456']
   ✅ Processing message in PR conversation thread!
```

If you don't see ANY logs when replying, the event subscription is missing!

### Expected Flow

```
You: @bot add authentication
Bot: [Shows changeset]
     📝 PROPOSED CHANGESET
     ...
     [Make PR button]

You: add JWT support          ← Reply in thread
Bot: [Shows updated changeset] ← Should respond!
     📝 UPDATED CHANGESET
     ...

You: make PR
Bot: ✅ PR created!
```

## Common Mistakes

### ❌ Mistake 1: Didn't Save Changes

After adding `message.channels`, you must click **"Save Changes"** at the bottom of the Event Subscriptions page.

### ❌ Mistake 2: Didn't Reinstall

Event changes require reinstalling the app to take effect. Just saving isn't enough!

### ❌ Mistake 3: Wrong Channel

Make sure you're replying **in the same thread** where the bot posted the changeset. New threads won't work.

### ❌ Mistake 4: Bot Not Restarted

After reinstalling the Slack app, restart your Python bot to pick up the new configuration.

## Still Not Working?

### Debug Logs

Check your bot logs when you reply:

```bash
# Should see this:
📨 Message event received: ...

# If you see this, the event isn't subscribed:
# (no logs at all when you reply)
```

### Manual Test

In your bot terminal, check if it's receiving events:

```python
# The handle_message_events function should log every message
# If you don't see logs, Slack isn't sending the events
```

### Verify Event Subscriptions

Go back to Event Subscriptions and verify:
- ✅ "Enable Events" is ON
- ✅ `app_mention` is listed
- ✅ `message.channels` is listed
- ✅ App has been reinstalled since adding events

## Why This Happens

Slack's event system requires explicit subscriptions:

- **`app_mention`** → Only sends events when bot is @mentioned
- **`message.channels`** → Sends ALL channel messages (filtered by bot)

Without `message.channels`, the bot only gets the initial @mention, not your follow-up replies!

## Quick Checklist

- [ ] Added `message.channels` event subscription
- [ ] Clicked "Save Changes" in Event Subscriptions
- [ ] Reinstalled app to workspace
- [ ] Restarted Python bot
- [ ] Tested in a NEW thread (old threads might not work)
- [ ] Checked logs show "📨 Message event received"

## Summary

**The issue**: Missing `message.channels` event subscription

**The fix**: 
1. Add `message.channels` to Event Subscriptions
2. Save Changes
3. Reinstall app to workspace
4. Restart bot
5. Test in new thread

**After this, the bot will respond to all your replies in PR conversation threads!** 🎉

