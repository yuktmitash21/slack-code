# REST API Documentation

This document describes how to interact with the Slack Bot through a REST API, enabling non-Slack platforms to access the AI code generation capabilities.

## Base URL

When running locally with ngrok:
```
https://your-ngrok-subdomain.ngrok-free.app/api/v1
```

When running locally (development):
```
http://localhost:5050/api/v1
```

---

## Authentication

All API endpoints (except `/health`) require authentication via an API key.

### Setting Up Your API Key

1. Generate a secure API key:
   ```bash
   # Generate a random 32-character key
   openssl rand -hex 16
   ```

2. Add it to your `.env` file:
   ```env
   BOT_API_KEY=your-generated-api-key-here
   ```

3. Include the key in all API requests:
   ```
   X-API-Key: your-generated-api-key-here
   ```

### Default GitHub Configuration (Optional)

Set these environment variables to avoid passing GitHub credentials with every request:

```env
# Default GitHub repo (owner/repo format)
DEFAULT_GITHUB_REPO=your-username/your-repo

# Default GitHub personal access token
DEFAULT_GITHUB_TOKEN=ghp_your_token_here
```

With these set, you can make requests without the `github` object:

```bash
# No github config needed - uses environment defaults
curl -X POST .../api/v1/chat \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "Add a login page"}'

# Can still override per-request if needed
curl -X POST .../api/v1/chat \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "Add a login page",
    "github": {"repo": "other/repo", "token": "ghp_different_token"}
  }'
```

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check (no auth required) |
| `POST` | `/api/v1/chat` | Send message, get AI-generated changeset |
| `POST` | `/api/v1/pr` | Create a PR from thread's changeset |
| `POST` | `/api/v1/pr/merge` | Merge an existing PR |
| `POST` | `/api/v1/pr/revert` | Revert a merged PR (creates revert PR) |
| `POST` | `/api/v1/threads` | Create new conversation thread |
| `GET` | `/api/v1/threads` | List all threads |
| `GET` | `/api/v1/threads/{id}` | Get thread history |
| `DELETE` | `/api/v1/threads/{id}` | Delete a thread |

---

### Health Check

Check if the API is running.

```
GET /api/v1/health
```

**Response:**
```json
{
    "status": "ok",
    "service": "slack-bot-api",
    "version": "1.0.0",
    "timestamp": "2024-01-15T12:00:00.000000"
}
```

---

### Send a Chat Message

Send a message and receive an AI-generated response.

```
POST /api/v1/chat
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
    "message": "Create a login page with email and password fields",
    "thread_id": "optional-uuid-for-conversation-context",
    "image": {
        "data": "base64-encoded-image-data",
        "format": "png",
        "filename": "wireframe.png"
    },
    "github": {
        "repo": "owner/repo-name",
        "token": "github-personal-access-token"
    }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's message/request |
| `thread_id` | string | No | UUID of existing thread for conversation context. If omitted, creates a new thread. |
| `image` | object | No | Image data for wireframe/screenshot analysis |
| `image.data` | string | Yes (if image) | Base64-encoded image data |
| `image.format` | string | No | Image format: `png`, `jpeg`, `gif`, `webp` (default: `png`) |
| `image.filename` | string | No | Original filename (for caching) |
| `github` | object | No | GitHub repository context |
| `github.repo` | string | Yes (if github) | Repository in `owner/repo` format |
| `github.token` | string | Yes (if github) | GitHub personal access token with repo access |

**Response (Success):**
```json
{
    "success": true,
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "response": "📝 PROPOSED CHANGESET\n========================================\n\n🟢 login.html [NEW] +45\n\n```html\n<!DOCTYPE html>...\n```\n\n📊 Summary: 1 file(s) in this changeset",
    "files": [
        {
            "path": "login.html",
            "content": "<!DOCTYPE html>...",
            "action": "NEW"
        }
    ],
    "raw_response": "Full AI response text...",
    "truncated": false,
    "timestamp": "2024-01-15T12:00:00.000000",
    "processing_time_ms": 3500
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Error message here",
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T12:00:00.000000"
}
```

---

### Create a Thread

Create a new conversation thread explicitly.

```
POST /api/v1/threads
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body (optional):**
```json
{
    "metadata": {
        "client": "my-app",
        "user_id": "user123",
        "custom_field": "any value"
    }
}
```

**Response:**
```json
{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T12:00:00.000000"
}
```

---

### List All Threads

Get a paginated list of all conversation threads.

```
GET /api/v1/threads?limit=50&offset=0
```

**Headers:**
```
X-API-Key: your-api-key
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum threads to return |
| `offset` | integer | 0 | Number of threads to skip |

**Response:**
```json
{
    "threads": [
        {
            "thread_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_at": "2024-01-15T12:00:00.000000",
            "updated_at": "2024-01-15T12:05:00.000000",
            "message_count": 4,
            "metadata": {"client": "my-app"}
        }
    ],
    "total": 25,
    "limit": 50,
    "offset": 0
}
```

---

### Get Thread History

Retrieve the full conversation history of a thread.

```
GET /api/v1/threads/{thread_id}
```

**Headers:**
```
X-API-Key: your-api-key
```

**Response:**
```json
{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T12:00:00.000000",
    "updated_at": "2024-01-15T12:05:00.000000",
    "metadata": {"client": "my-app"},
    "messages": [
        {
            "role": "user",
            "content": "Create a login page",
            "timestamp": "2024-01-15T12:00:00.000000",
            "has_image": false
        },
        {
            "role": "assistant",
            "content": "📝 PROPOSED CHANGESET...",
            "timestamp": "2024-01-15T12:00:03.500000",
            "files": [{"path": "login.html", "content": "...", "action": "NEW"}]
        },
        {
            "role": "user",
            "content": "Add a forgot password link",
            "timestamp": "2024-01-15T12:01:00.000000",
            "has_image": false
        },
        {
            "role": "assistant",
            "content": "📝 UPDATED CHANGESET...",
            "timestamp": "2024-01-15T12:01:03.200000",
            "files": [{"path": "login.html", "content": "...", "action": "MODIFIED"}]
        }
    ],
    "message_count": 4
}
```

---

### Delete a Thread

Delete a conversation thread and its history.

```
DELETE /api/v1/threads/{thread_id}
```

**Headers:**
```
X-API-Key: your-api-key
```

**Response:**
```json
{
    "deleted": true,
    "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### Create a Pull Request

Create a GitHub PR from a thread's cached changeset.

```
POST /api/v1/pr
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "github": {
        "repo": "owner/repo-name",
        "token": "ghp_your_github_token"
    },
    "title": "Optional custom PR title",
    "description": "Optional custom PR description"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | string | Yes | Thread ID from a previous `/chat` response |
| `github.repo` | string | Yes | Repository in `owner/repo` format |
| `github.token` | string | Yes | GitHub personal access token with repo write access |
| `title` | string | No | Custom PR title (auto-generated if omitted) |
| `description` | string | No | Custom PR description |

**Response (Success):**
```json
{
    "success": true,
    "pr_number": 123,
    "pr_url": "https://github.com/owner/repo/pull/123",
    "branch_name": "ai-generated-abc123",
    "changes": "3 file(s)",
    "processing_time_ms": 2500
}
```

---

### Merge a Pull Request

Merge an existing GitHub PR.

```
POST /api/v1/pr/merge
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
    "pr_number": 123,
    "github": {
        "repo": "owner/repo-name",
        "token": "ghp_your_github_token"
    },
    "merge_method": "squash"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pr_number` | integer | Yes | PR number to merge |
| `github.repo` | string | Yes | Repository in `owner/repo` format |
| `github.token` | string | Yes | GitHub token with repo write access |
| `merge_method` | string | No | `merge`, `squash`, or `rebase` (default: `merge`) |

**Response (Success):**
```json
{
    "success": true,
    "pr_number": 123,
    "pr_title": "Add login page",
    "branch_name": "ai-generated-abc123",
    "merge_method": "squash",
    "pr_url": "https://github.com/owner/repo/pull/123"
}
```

---

### Revert a Pull Request

Create a revert PR to undo a previously merged PR.

```
POST /api/v1/pr/revert
```

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
    "pr_number": 123,
    "github": {
        "repo": "owner/repo-name",
        "token": "ghp_your_github_token"
    }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pr_number` | integer | Yes | PR number to revert (must be merged) |
| `github.repo` | string | No* | Repository in `owner/repo` format |
| `github.token` | string | No* | GitHub token with repo write access |

*Required if `DEFAULT_GITHUB_REPO` and `DEFAULT_GITHUB_TOKEN` environment variables are not set.

**Response (Success):**
```json
{
    "success": true,
    "original_pr_number": 123,
    "original_pr_title": "Add login page",
    "original_pr_url": "https://github.com/owner/repo/pull/123",
    "revert_pr_number": 456,
    "revert_pr_url": "https://github.com/owner/repo/pull/456",
    "revert_branch_name": "revert-123"
}
```

**Note:** This creates a new PR that reverts the changes. You still need to merge the revert PR to complete the undo.

---

## Examples

### Full Workflow: Chat → PR → Merge (cURL)

```bash
# Step 1: Generate a changeset
CHAT_RESPONSE=$(curl -s -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "Create a login page with email and password"}')

echo "$CHAT_RESPONSE" | jq '.response'  # Review the changeset
THREAD_ID=$(echo "$CHAT_RESPONSE" | jq -r '.thread_id')

# Step 2: Create the PR (after reviewing the changeset)
PR_RESPONSE=$(curl -s -X POST https://your-ngrok-url.ngrok-free.app/api/v1/pr \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d "{
    \"thread_id\": \"$THREAD_ID\",
    \"github\": {
      \"repo\": \"your-username/your-repo\",
      \"token\": \"ghp_your_github_token\"
    }
  }")

echo "$PR_RESPONSE" | jq '.pr_url'  # Get the PR URL
PR_NUMBER=$(echo "$PR_RESPONSE" | jq -r '.pr_number')

# Step 3: Merge the PR (after review)
curl -X POST https://your-ngrok-url.ngrok-free.app/api/v1/pr/merge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d "{
    \"pr_number\": $PR_NUMBER,
    \"github\": {
      \"repo\": \"your-username/your-repo\",
      \"token\": \"ghp_your_github_token\"
    },
    \"merge_method\": \"squash\"
  }"
```

### Basic Chat (cURL)

```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "Create a simple HTML landing page with a hero section"
  }'
```

### Multi-turn Conversation (cURL)

```bash
# First message - creates a new thread
RESPONSE=$(curl -s -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "Create a todo list app"}')

# Extract thread_id from response
THREAD_ID=$(echo $RESPONSE | jq -r '.thread_id')

# Second message - continues the conversation
curl -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d "{
    \"message\": \"Add a delete button for each todo item\",
    \"thread_id\": \"$THREAD_ID\"
  }"
```

### With Image/Wireframe (cURL)

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -i wireframe.png | tr -d '\n')

curl -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d "{
    \"message\": \"Implement this wireframe as HTML/CSS\",
    \"image\": {
      \"data\": \"$IMAGE_BASE64\",
      \"format\": \"png\",
      \"filename\": \"wireframe.png\"
    }
  }"
```

### With GitHub Context (cURL)

```bash
curl -X POST https://your-ngrok-url.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "Add unit tests for the auth module",
    "github": {
      "repo": "myusername/myproject",
      "token": "ghp_your_github_token"
    }
  }'
```

### Python Example

```python
import requests
import base64

API_URL = "https://your-ngrok-url.ngrok-free.app/api/v1"
API_KEY = "your-api-key"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Simple chat
response = requests.post(
    f"{API_URL}/chat",
    headers=headers,
    json={"message": "Create a Python Flask REST API for a blog"}
)
result = response.json()
print(result["response"])

# With conversation context
thread_id = result["thread_id"]
response = requests.post(
    f"{API_URL}/chat",
    headers=headers,
    json={
        "message": "Add pagination to the posts endpoint",
        "thread_id": thread_id
    }
)

# With image
with open("wireframe.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = requests.post(
    f"{API_URL}/chat",
    headers=headers,
    json={
        "message": "Convert this wireframe to code",
        "image": {
            "data": image_data,
            "format": "png",
            "filename": "wireframe.png"
        }
    }
)
```

### JavaScript/Node.js Example

```javascript
const fetch = require('node-fetch');
const fs = require('fs');

const API_URL = 'https://your-ngrok-url.ngrok-free.app/api/v1';
const API_KEY = 'your-api-key';

async function chat(message, threadId = null, imagePath = null) {
    const body = { message };
    
    if (threadId) {
        body.thread_id = threadId;
    }
    
    if (imagePath) {
        const imageData = fs.readFileSync(imagePath).toString('base64');
        const format = imagePath.split('.').pop();
        body.image = {
            data: imageData,
            format: format,
            filename: imagePath.split('/').pop()
        };
    }
    
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify(body)
    });
    
    return response.json();
}

// Usage
async function main() {
    // Simple chat
    const result1 = await chat('Create a React component for a user profile card');
    console.log(result1.response);
    
    // Continue conversation
    const result2 = await chat('Add a dark mode toggle', result1.thread_id);
    console.log(result2.response);
    
    // With wireframe
    const result3 = await chat('Implement this design', null, './wireframe.png');
    console.log(result3.response);
}

main();
```

---

## Deployment with ngrok

### Step 1: Install ngrok

```bash
# macOS (Homebrew)
brew install ngrok

# Or download from https://ngrok.com/download
```

### Step 2: Set Up ngrok Account (Free)

1. Sign up at https://ngrok.com
2. Get your auth token from the dashboard
3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Step 3: Start Your Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_API_KEY="your-secure-api-key"
export OPENAI_API_KEY="sk-..."
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."

# Start the bot
python slack_bot.py
```

### Step 4: Start ngrok Tunnel

In a separate terminal:

```bash
# Expose port 5050 (default Flask port)
ngrok http 5050
```

ngrok will display your public URL:
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:5050
```

### Step 5: Test Your API

```bash
# Test health endpoint
curl https://abc123.ngrok-free.app/api/v1/health

# Test chat endpoint
curl -X POST https://abc123.ngrok-free.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "Hello, create a simple HTML page"}'
```

### Using a Static ngrok Domain (Recommended)

For a consistent URL, use ngrok's static domains:

```bash
# With free account (one static domain)
ngrok http 5050 --domain=your-chosen-subdomain.ngrok-free.app
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Resource created (threads) |
| 400 | Bad request (missing required fields) |
| 401 | Unauthorized (missing or invalid API key) |
| 404 | Resource not found (thread doesn't exist) |
| 500 | Internal server error |
| 503 | Service unavailable (API key not configured on server) |

---

## Rate Limits

Currently, there are no rate limits enforced by the API. However:
- OpenAI API has its own rate limits
- Consider implementing client-side rate limiting for production use

---

## Best Practices

1. **Store thread_id**: Save the `thread_id` from responses to maintain conversation context.

2. **Handle errors gracefully**: Always check the `success` field in responses.

3. **Use meaningful messages**: Be specific in your requests for better AI responses.

4. **Include context**: When working with a codebase, provide GitHub credentials for better code generation.

5. **Secure your API key**: Never expose your API key in client-side code. Use a backend proxy.

6. **Monitor usage**: Track `processing_time_ms` to understand response times.
