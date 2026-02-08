from fastapi import HTTPException
from stravalib.client import Client
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from stravalib.protocol import AccessInfo
from .config import STATE_DIR, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self, tokens_file="strava_tokens.json"):
        self.tokens_file = STATE_DIR / Path(tokens_file)
        self._ensure_tokens_file()

    def _ensure_tokens_file(self):
        """Create tokens file if it doesn't exist"""
        if not self.tokens_file.exists():
            self.tokens_file.write_text("{}")

    def _load_tokens(self):
        """Load tokens from JSON file"""
        return json.loads(self.tokens_file.read_text())

    def _save_tokens(self, tokens):
        """Save tokens to JSON file"""
        self.tokens_file.write_text(json.dumps(tokens, indent=2))

    def update_tokens(self, user_id: str, token_response: AccessInfo):
        """Update tokens for a specific user"""
        tokens = self._load_tokens()
        tokens[user_id] = {
            "access_token": token_response["access_token"],
            "refresh_token": token_response["refresh_token"],
            "expires_at": str(token_response["expires_at"]),
        }
        self._save_tokens(tokens)

    def get_tokens(self, user_id: str):
        """Get tokens for a specific user"""
        tokens = self._load_tokens()
        if user_id not in tokens:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please visit /strava/auth first",
            )
        return tokens[user_id]


def get_client(user_id: str) -> Client:
    """Get an authenticated Strava client with automatic token refresh for a specific user"""
    token_manager = TokenManager()
    strava_client = Client()

    try:
        user_tokens = token_manager.get_tokens(user_id)
        access_token = user_tokens["access_token"]
        refresh_token = user_tokens["refresh_token"]
        expires_at = user_tokens["expires_at"]

        # Check if token needs refresh (if it expires in the next 5 minutes)
        expires_at = int(expires_at)
        if datetime.fromtimestamp(expires_at) < datetime.now() + timedelta(minutes=5):
            logger.info(
                f"Token expired or expiring soon for user {user_id}, refreshing..."
            )
            token_response = strava_client.refresh_access_token(
                client_id=STRAVA_CLIENT_ID,
                client_secret=STRAVA_CLIENT_SECRET,
                refresh_token=refresh_token,
            )
            # Update tokens in JSON file
            token_manager.update_tokens(user_id, token_response)
            strava_client.access_token = token_response["access_token"]
        else:
            strava_client.access_token = access_token

    except Exception as e:
        logger.error(f"Error refreshing token for user {user_id}: {e}")
        raise HTTPException(status_code=401, detail="Error refreshing authentication")

    return strava_client
