"""
OAuth Callback Server

Simple Flask server to handle GitHub OAuth callbacks
Run alongside the Slack bot to handle authentication
"""

import logging
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from flask import Flask, request, redirect
from github_oauth import auth_manager

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return """
        <html>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>❌ Authentication Failed</h1>
                <p>Missing code or state parameter</p>
                <p><a href="/">Try again</a></p>
            </body>
        </html>
        """, 400
    
    # Handle the OAuth callback (synchronous call)
    import asyncio
    result = asyncio.run(auth_manager.handle_oauth_callback(code, state))
    
    if result["success"]:
        github_username = result["github_username"]
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 40px;
                        text-align: center;
                        color: white;
                    }}
                    .container {{
                        background: white;
                        color: #333;
                        padding: 40px;
                        border-radius: 12px;
                        max-width: 500px;
                        margin: 0 auto;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    }}
                    h1 {{ color: #4CAF50; margin-bottom: 10px; }}
                    .username {{ 
                        background: #f0f0f0;
                        padding: 10px 20px;
                        border-radius: 20px;
                        display: inline-block;
                        margin: 20px 0;
                        font-weight: bold;
                    }}
                    .next-steps {{
                        text-align: left;
                        background: #f9f9f9;
                        padding: 20px;
                        border-radius: 8px;
                        margin-top: 20px;
                    }}
                    .next-steps li {{ margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Successfully Connected!</h1>
                    <p>Your GitHub account has been linked to the Slack bot.</p>
                    <div class="username">🐙 {github_username}</div>
                    
                    <div class="next-steps">
                        <h3>📋 Next Steps:</h3>
                        <ol>
                            <li>Go back to Slack</li>
                            <li>Mention the bot: <code>@bot set repo owner/repository</code></li>
                            <li>Start creating PRs: <code>@bot create a login page</code></li>
                        </ol>
                    </div>
                    
                    <p style="margin-top: 30px; color: #888; font-size: 14px;">
                        You can close this window now
                    </p>
                </div>
            </body>
        </html>
        """
    else:
        error = result.get("error", "Unknown error")
        return f"""
        <html>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>❌ Authentication Failed</h1>
                <p>{error}</p>
                <p><a href="/">Try again</a></p>
            </body>
        </html>
        """, 400


@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "github-oauth-callback"}


if __name__ == '__main__':
    print("=" * 60)
    print("🔐 GitHub OAuth Callback Server")
    print("=" * 60)
    print("📍 Callback URL: http://localhost:5050/auth/github/callback")
    print("🏥 Health check: http://localhost:5050/health")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5050, debug=False)

