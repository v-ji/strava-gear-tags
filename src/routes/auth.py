import logging
from datetime import datetime
import webbrowser
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from stravalib.client import Client
from pydantic import BaseModel

from ..auth import TokenManager
from ..config import CALLBACK_URL, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

router = APIRouter()
logger = logging.getLogger(__name__)
strava_client = Client()
token_manager = TokenManager()


class AuthStatus(BaseModel):
    status: str
    message: str
    token_expires: Optional[str] = None
    user_id: Optional[str] = None


@router.get("/", response_model=AuthStatus)
async def root(request: Request):
    """Root endpoint with authentication status and debug info"""
    # Get user_id from query params or header, if your app uses them
    user_id = request.query_params.get("user_id")

    if user_id:
        try:
            tokens = token_manager.get_tokens(user_id)
            expires_at_dt = datetime.fromtimestamp(int(tokens["expires_at"]))
            return {
                "status": "authenticated",
                "message": "Ready to fetch Strava data",
                "token_expires": expires_at_dt.isoformat(),
                "user_id": user_id,
            }
        except HTTPException:
            pass

    return {
        "status": "not_authenticated",
        "message": "Please authenticate with Strava first",
        "token_expires": None,
        "user_id": None,
    }


@router.get("/strava/auth")
async def strava_auth():
    """Start Strava OAuth flow"""
    auth_url = strava_client.authorization_url(
        client_id=STRAVA_CLIENT_ID,
        redirect_uri=CALLBACK_URL,
        scope=["read", "read_all", "profile:read_all", "activity:read_all"],
    )
    logger.info(f"Generated auth URL: {auth_url}")
    webbrowser.open(auth_url)
    return {"message": "Please check your browser to complete authentication"}


@router.get("/strava/callback")
async def strava_callback(request: Request):
    """Handle Strava OAuth callback"""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    try:
        # Exchange the code for tokens
        token_response = strava_client.exchange_code_for_token(
            client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, code=code
        )

        # Get the athlete info to use their Strava ID
        temp_client = Client(access_token=token_response["access_token"])
        athlete = temp_client.get_athlete()
        user_id = str(athlete.id)  # Convert to string for consistent handling

        # Store tokens using the athlete's Strava ID
        token_manager.update_tokens(user_id, token_response)

        return {
            "message": "Authentication successful! You can now use the API.",
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Error in callback: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication error: {str(e)}")
