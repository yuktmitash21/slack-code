# Changeset Format Guide

## Overview

Every response from the bot now includes a **formatted changeset** showing exactly what files will be created or modified. This makes it crystal clear what the PR will contain before you create it.

## Changeset Structure

The bot always replies in this format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
Brief description of what this changeset accomplishes

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: path/to/file1.py [NEW] or [MODIFIED]

```python
# Complete, working implementation
def example_function():
    return "actual code"
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: path/to/file2.py [NEW] or [MODIFIED]

```python
# Complete, working implementation
class ExampleClass:
    def __init__(self):
        pass
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: 2 file(s) in this changeset
📝 Files: path/to/file1.py, path/to/file2.py
```

## Key Features

### 1. Clear Visual Structure
- **Header**: Shows this is a changeset
- **Separators**: Clear boundaries between files
- **File markers**: 📄 emoji and [NEW]/[MODIFIED] tags
- **Summary footer**: Quick overview of what's included

### 2. Complete Code
- **No placeholders**: Every function/class is fully implemented
- **Actual imports**: Uses libraries already in your codebase
- **Real logic**: Working code, not stubs
- **Comments**: Explains key decisions

### 3. Context-Aware
- **File paths**: Match your repository structure
- **Code style**: Matches your existing patterns
- **Dependencies**: Uses what's already in your project
- **Imports**: References actual modules in your codebase

## Example Conversation

### Initial Request
```
You: @bot add JWT authentication to the API

Bot: 🤖 I'll propose a changeset for:
     > add JWT authentication to the API
     
     📚 Reading codebase and generating changes...
```

### Initial Changeset
```
🆕 Proposed Changeset (3 files)

@user

📝 PROPOSED CHANGESET

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
Add JWT authentication with token generation, validation, and middleware

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/auth/jwt.py [NEW]

```python
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "your-secret-key"  # Should be in config

def generate_token(user_id: int, expires_in: int = 3600) -> str:
    """Generate a JWT token for the user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return {'success': True, 'user_id': payload['user_id']}
    except jwt.ExpiredSignatureError:
        return {'success': False, 'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'success': False, 'error': 'Invalid token'}

def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        result = verify_token(token)
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        
        return f(user_id=result['user_id'], *args, **kwargs)
    
    return decorated_function
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/api/auth_routes.py [NEW]

```python
from flask import Blueprint, request, jsonify
from src.auth.jwt import generate_token
from src.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.authenticate(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user.id)
    return jsonify({
        'token': token,
        'user_id': user.id,
        'username': user.username
    }), 200
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/app.py [MODIFIED]

```python
# Add this import at the top
from src.api.auth_routes import auth_bp

# Add this line where you register blueprints
app.register_blueprint(auth_bp)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: 3 file(s) in this changeset
📝 Files: src/auth/jwt.py, src/api/auth_routes.py, src/app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━

[🚀 Make PR with These Changes]

💬 Reply with feedback to modify this changeset • 🚀 Click button to create PR
```

### User Feedback
```
You: Add token refresh functionality
```

### Updated Changeset
```
🔄 Proposed Changeset (3 files)

@user

📝 UPDATED CHANGESET

━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CHANGESET SUMMARY
Add JWT authentication with token generation, validation, middleware, and refresh

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/auth/jwt.py [NEW]

```python
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "your-secret-key"
REFRESH_SECRET = "your-refresh-secret"

def generate_token(user_id: int, expires_in: int = 3600) -> str:
    """Generate a JWT access token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def generate_refresh_token(user_id: int) -> str:
    """Generate a JWT refresh token (longer expiry)"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, REFRESH_SECRET, algorithm='HS256')

def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode a JWT token"""
    secret = REFRESH_SECRET if token_type == 'refresh' else SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        if payload.get('type') != token_type:
            return {'success': False, 'error': 'Invalid token type'}
        return {'success': True, 'user_id': payload['user_id']}
    except jwt.ExpiredSignatureError:
        return {'success': False, 'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'success': False, 'error': 'Invalid token'}

def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        result = verify_token(token, 'access')
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        
        return f(user_id=result['user_id'], *args, **kwargs)
    
    return decorated_function
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/api/auth_routes.py [NEW]

```python
from flask import Blueprint, request, jsonify
from src.auth.jwt import generate_token, generate_refresh_token, verify_token
from src.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.authenticate(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = generate_token(user.id)
    refresh_token = generate_refresh_token(user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user_id': user.id,
        'username': user.username
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'No refresh token provided'}), 400
    
    result = verify_token(refresh_token, 'refresh')
    if not result['success']:
        return jsonify({'error': result['error']}), 401
    
    # Generate new access token
    new_access_token = generate_token(result['user_id'])
    
    return jsonify({
        'access_token': new_access_token
    }), 200
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 File: src/app.py [MODIFIED]

```python
# Add this import at the top
from src.api.auth_routes import auth_bp

# Add this line where you register blueprints
app.register_blueprint(auth_bp)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: 3 file(s) in this changeset
📝 Files: src/auth/jwt.py, src/api/auth_routes.py, src/app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━

[🚀 Make PR with These Changes]

💬 Reply with feedback to modify this changeset • 🚀 Click button to create PR
```

### Final Action
```
You: Make PR

Bot: ✅ Perfect! Creating the pull request now...
Bot: ✅ Pull Request Created!
     PR #456: 🤖 Bot Task: add JWT authentication to the API
     🔗 https://github.com/user/repo/pull/456
     
     Files changed:
     • src/auth/jwt.py (created)
     • src/api/auth_routes.py (created)
     • src/app.py (modified)
```

## Benefits

### 1. Complete Visibility
- You see EXACTLY what will be in the PR
- No surprises after clicking "Make PR"
- Review code before committing

### 2. Iterative Refinement
- Propose changes through conversation
- Bot updates the changeset each time
- Get exactly what you want

### 3. Context-Aware Code
- Bot knows your existing codebase
- Matches your patterns and style
- Uses your existing dependencies

### 4. Professional Format
- Clean, organized presentation
- Easy to scan and review
- Summary shows what's included

## Tips for Best Results

### Be Specific in Feedback
```
❌ "Make it better"
✅ "Add error handling for network timeouts"

❌ "Change the function"
✅ "Make the authentication function async"
```

### Review the Changeset Carefully
- Check file paths are correct
- Verify imports match your project
- Look for any hardcoded values
- Ensure error handling is appropriate

### Iterate Until Perfect
- Don't rush to "Make PR"
- Request multiple changes
- Bot will keep updating the changeset
- Only create PR when you're satisfied

## Summary

The changeset format ensures:
- ✅ You always see proposed changes before PR creation
- ✅ Code is complete and functional (no placeholders)
- ✅ Changes integrate with your existing codebase
- ✅ You can iterate and refine through conversation
- ✅ Clear visual structure makes review easy

**Every response is a changeset. Every changeset is reviewable. Every PR is intentional.** 🚀

