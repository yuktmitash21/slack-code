"""
REST API Server for External Bot Access

This module provides a REST API that allows external clients (non-Slack platforms)
to interact with the AI code generation bot.

Endpoints:
- POST /api/v1/chat - Send a message and get a response
- POST /api/v1/threads - Create a new conversation thread
- GET /api/v1/threads/<thread_id> - Get thread history
- DELETE /api/v1/threads/<thread_id> - Delete a thread

Authentication: API Key via X-API-Key header
"""

import os
import logging
import json
import uuid
import time
import base64
from datetime import datetime
from typing import Dict, Optional, List
from functools import wraps

from flask import Blueprint, request, jsonify, g

logger = logging.getLogger(__name__)

# API Blueprint for modular integration
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Thread storage (in-memory, persistent to file)
API_THREADS_FILE = os.path.join(os.path.dirname(__file__), "data", "api_threads.json")


def _load_api_threads() -> dict:
    """Load API threads from persistent storage."""
    try:
        if os.path.exists(API_THREADS_FILE):
            with open(API_THREADS_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"📂 Loaded {len(data)} API threads from storage")
                return data
    except Exception as e:
        logger.error(f"Error loading API threads: {e}")
    return {}


def _save_api_threads():
    """Save API threads to persistent storage."""
    try:
        os.makedirs(os.path.dirname(API_THREADS_FILE), exist_ok=True)
        with open(API_THREADS_FILE, "w") as f:
            json.dump(api_threads, f, indent=2)
        logger.debug(f"💾 Saved {len(api_threads)} API threads to storage")
    except Exception as e:
        logger.error(f"Error saving API threads: {e}")


# Load threads on module import
api_threads = _load_api_threads()


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.environ.get('BOT_API_KEY')
        
        if not expected_key:
            logger.warning("BOT_API_KEY not configured - API access disabled")
            return jsonify({
                "error": "API not configured",
                "message": "Server has not configured API access. Set BOT_API_KEY environment variable."
            }), 503
        
        if not api_key:
            return jsonify({
                "error": "Missing API key",
                "message": "Include X-API-Key header with your API key"
            }), 401
        
        if api_key != expected_key:
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is not valid"
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def get_ai_generator():
    """Get the AI code generator instance."""
    from ai_agent import get_ai_code_generator
    return get_ai_code_generator()


def generate_ai_response(
    message: str,
    thread_id: Optional[str] = None,
    image_data: Optional[Dict] = None,
    github_repo: Optional[str] = None,
    github_token: Optional[str] = None
) -> Dict:
    """
    Generate an AI response for a message.
    
    Args:
        message: User's message text
        thread_id: Optional thread ID for conversation context
        image_data: Optional dict with 'data' (base64) and 'format' (png/jpeg/etc)
        github_repo: Optional GitHub repo for codebase context (owner/repo)
        github_token: Optional GitHub token for private repo access
        
    Returns:
        Dict with response text and metadata
    """
    try:
        generator = get_ai_generator()
        if not generator:
            return {
                "success": False,
                "error": "AI generator not available. Check OPENAI_API_KEY.",
                "response": None
            }
        
        # Build conversation context from thread
        conversation_context = ""
        if thread_id and thread_id in api_threads:
            thread = api_threads[thread_id]
            messages = thread.get("messages", [])
            
            # Build context from previous messages
            for msg in messages[-10:]:  # Last 10 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role}: {content}\n\n"
        
        # Build the full prompt
        full_prompt = ""
        if conversation_context:
            full_prompt = f"Previous conversation:\n{conversation_context}\n\nCurrent message:\n{message}"
        else:
            full_prompt = message
        
        # Get codebase context if GitHub repo is specified
        codebase_context = ""
        if github_repo and github_token:
            try:
                from github_helper import GitHubPRHelper
                helper = GitHubPRHelper(
                    github_token=github_token,
                    repo_name=github_repo,
                    use_ai=False  # We just need repo access
                )
                default_branch = helper.repo.default_branch
                codebase_context = helper._get_full_codebase_context(default_branch, user_prompt=message)
                logger.info(f"Loaded codebase context: {len(codebase_context)} chars")
            except Exception as e:
                logger.warning(f"Could not load codebase context: {e}")
        
        # Generate response
        logger.info(f"Generating AI response for message: {message[:100]}...")
        logger.info(f"Image data present: {image_data is not None}")
        
        result = generator.generate_code_sync(
            task_description=full_prompt,
            context=codebase_context if codebase_context else None,
            image_data=image_data
        )
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Generation failed"),
                "response": None
            }
        
        # Format response as text (similar to Slack formatting)
        raw_response = result.get("raw_response", "")
        files = result.get("files", [])
        
        # Build formatted response
        formatted_response = ""
        if files:
            formatted_response = "📝 PROPOSED CHANGESET\n" + "=" * 40 + "\n\n"
            
            for file_info in files:
                filepath = file_info.get("path", "unknown")
                action = file_info.get("action", "NEW")
                content = file_info.get("content", "")
                
                lines = content.split('\n') if content else []
                line_count = len(lines)
                
                if action == "DELETED":
                    formatted_response += f"🔴 {filepath} [DELETED] -{line_count}\n\n"
                elif action == "NEW":
                    formatted_response += f"🟢 {filepath} [NEW] +{line_count}\n\n"
                else:
                    formatted_response += f"🟡 {filepath} [MODIFIED] ~{line_count}\n\n"
                
                # Show code preview
                formatted_response += f"```\n{content}\n```\n\n"
                formatted_response += "-" * 40 + "\n\n"
            
            formatted_response += f"📊 Summary: {len(files)} file(s) in this changeset"
        else:
            formatted_response = raw_response
        
        return {
            "success": True,
            "response": formatted_response,
            "files": files,
            "raw_response": raw_response,
            "truncated": result.get("truncated", False)
        }
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "response": None
        }


# ============================================================================
# API Endpoints
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def api_health():
    """Health check endpoint (no auth required)."""
    return jsonify({
        "status": "ok",
        "service": "slack-bot-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })


@api_bp.route('/threads', methods=['POST'])
@require_api_key
def create_thread():
    """
    Create a new conversation thread.
    
    Request body (optional):
    {
        "metadata": {
            "client": "my-app",
            "user_id": "user123"
        }
    }
    
    Returns:
    {
        "thread_id": "uuid-...",
        "created_at": "2024-01-01T00:00:00Z"
    }
    """
    try:
        data = request.get_json() or {}
        metadata = data.get("metadata", {})
        
        thread_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        api_threads[thread_id] = {
            "id": thread_id,
            "created_at": created_at,
            "updated_at": created_at,
            "metadata": metadata,
            "messages": [],
            "codebase_context": None,
            "cached_files": []
        }
        _save_api_threads()
        
        logger.info(f"Created new API thread: {thread_id}")
        
        return jsonify({
            "thread_id": thread_id,
            "created_at": created_at
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/threads/<thread_id>', methods=['GET'])
@require_api_key
def get_thread(thread_id: str):
    """
    Get thread history and metadata.
    
    Returns:
    {
        "thread_id": "uuid-...",
        "created_at": "2024-01-01T00:00:00Z",
        "messages": [
            {"role": "user", "content": "...", "timestamp": "..."},
            {"role": "assistant", "content": "...", "timestamp": "..."}
        ]
    }
    """
    if thread_id not in api_threads:
        return jsonify({
            "error": "Thread not found",
            "thread_id": thread_id
        }), 404
    
    thread = api_threads[thread_id]
    return jsonify({
        "thread_id": thread_id,
        "created_at": thread.get("created_at"),
        "updated_at": thread.get("updated_at"),
        "metadata": thread.get("metadata", {}),
        "messages": thread.get("messages", []),
        "message_count": len(thread.get("messages", []))
    })


@api_bp.route('/threads/<thread_id>', methods=['DELETE'])
@require_api_key
def delete_thread(thread_id: str):
    """Delete a conversation thread."""
    if thread_id not in api_threads:
        return jsonify({
            "error": "Thread not found",
            "thread_id": thread_id
        }), 404
    
    del api_threads[thread_id]
    _save_api_threads()
    
    logger.info(f"Deleted API thread: {thread_id}")
    
    return jsonify({
        "deleted": True,
        "thread_id": thread_id
    })


@api_bp.route('/threads', methods=['GET'])
@require_api_key
def list_threads():
    """List all threads (with pagination)."""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    thread_ids = list(api_threads.keys())
    thread_ids.sort(key=lambda x: api_threads[x].get("updated_at", ""), reverse=True)
    
    paginated = thread_ids[offset:offset + limit]
    
    threads = []
    for tid in paginated:
        t = api_threads[tid]
        threads.append({
            "thread_id": tid,
            "created_at": t.get("created_at"),
            "updated_at": t.get("updated_at"),
            "message_count": len(t.get("messages", [])),
            "metadata": t.get("metadata", {})
        })
    
    return jsonify({
        "threads": threads,
        "total": len(thread_ids),
        "limit": limit,
        "offset": offset
    })


@api_bp.route('/chat', methods=['POST'])
@require_api_key
def chat():
    """
    Send a message and get an AI response.
    
    Request body:
    {
        "message": "Create a login page with email and password fields",
        "thread_id": "optional-uuid-for-conversation-context",
        "image": {
            "data": "base64-encoded-image-data",
            "format": "png"  // or "jpeg", "gif", "webp"
        },
        "github": {
            "repo": "owner/repo-name",
            "token": "github-personal-access-token"
        }
    }
    
    Returns:
    {
        "success": true,
        "thread_id": "uuid-...",
        "response": "📝 PROPOSED CHANGESET\n...",
        "files": [
            {"path": "login.html", "content": "...", "action": "NEW"}
        ],
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "Request body required",
                "message": "Send JSON with 'message' field"
            }), 400
        
        message = data.get("message")
        if not message:
            return jsonify({
                "error": "Message required",
                "message": "Include 'message' field in request body"
            }), 400
        
        thread_id = data.get("thread_id")
        
        # Handle image data
        image_data = None
        if "image" in data:
            img = data["image"]
            if isinstance(img, dict) and "data" in img:
                image_data = {
                    "data": img["data"],
                    "format": img.get("format", "png"),
                    "filename": img.get("filename", "api_upload.png")
                }
                logger.info(f"Image received: {image_data['format']}, {len(image_data['data'])} chars")
        
        # Handle GitHub context
        github_repo = None
        github_token = None
        if "github" in data:
            gh = data["github"]
            github_repo = gh.get("repo")
            github_token = gh.get("token")
        
        # Create thread if not provided
        if not thread_id:
            thread_id = str(uuid.uuid4())
            api_threads[thread_id] = {
                "id": thread_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {},
                "messages": [],
                "codebase_context": None,
                "cached_files": []
            }
        elif thread_id not in api_threads:
            return jsonify({
                "error": "Thread not found",
                "message": f"Thread {thread_id} does not exist. Create it first or omit thread_id."
            }), 404
        
        # Add user message to thread
        timestamp = datetime.utcnow().isoformat()
        api_threads[thread_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": timestamp,
            "has_image": image_data is not None
        })
        api_threads[thread_id]["updated_at"] = timestamp
        
        # Generate AI response
        start_time = time.time()
        result = generate_ai_response(
            message=message,
            thread_id=thread_id,
            image_data=image_data,
            github_repo=github_repo,
            github_token=github_token
        )
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if not result.get("success"):
            return jsonify({
                "success": False,
                "error": result.get("error"),
                "thread_id": thread_id,
                "timestamp": timestamp
            }), 500
        
        # Add assistant response to thread
        response_timestamp = datetime.utcnow().isoformat()
        api_threads[thread_id]["messages"].append({
            "role": "assistant",
            "content": result.get("response"),
            "timestamp": response_timestamp,
            "files": result.get("files", [])
        })
        api_threads[thread_id]["cached_files"] = result.get("files", [])
        api_threads[thread_id]["updated_at"] = response_timestamp
        _save_api_threads()
        
        return jsonify({
            "success": True,
            "thread_id": thread_id,
            "response": result.get("response"),
            "files": result.get("files", []),
            "raw_response": result.get("raw_response"),
            "truncated": result.get("truncated", False),
            "timestamp": response_timestamp,
            "processing_time_ms": processing_time_ms
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/chat/stream', methods=['POST'])
@require_api_key
def chat_stream():
    """
    Send a message and get a streaming AI response.
    
    Note: This endpoint returns the full response at once for now.
    True streaming (SSE) can be added later.
    
    Same request/response format as /chat
    """
    # For now, just use the regular chat endpoint
    # True SSE streaming can be implemented later
    return chat()


# ============================================================================
# Helper to register blueprint with existing Flask app
# ============================================================================

def register_api(flask_app):
    """Register the API blueprint with a Flask app."""
    flask_app.register_blueprint(api_bp)
    logger.info("📡 API endpoints registered at /api/v1/")
    logger.info("   POST /api/v1/chat - Send message, get response")
    logger.info("   POST /api/v1/threads - Create conversation thread")
    logger.info("   GET  /api/v1/threads - List all threads")
    logger.info("   GET  /api/v1/threads/<id> - Get thread history")
    logger.info("   DELETE /api/v1/threads/<id> - Delete thread")
    logger.info("   GET  /api/v1/health - Health check")


# ============================================================================
# Standalone server (for separate deployment)
# ============================================================================

def create_standalone_app():
    """Create a standalone Flask app with just the API."""
    from flask import Flask
    app = Flask(__name__)
    register_api(app)
    return app


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create standalone API server
    app = create_standalone_app()
    
    port = int(os.environ.get("API_PORT", 5051))
    
    print("=" * 60)
    print("🚀 Standalone API Server")
    print("=" * 60)
    print(f"📍 Base URL: http://localhost:{port}/api/v1")
    print(f"🔑 API Key: Set BOT_API_KEY environment variable")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
