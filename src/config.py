import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Strava API configuration
STRAVA_CLIENT_ID = int(os.environ["STRAVA_CLIENT_ID"])
STRAVA_CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
CALLBACK_URL = os.environ.get("CALLBACK_URL", "http://localhost:8000/strava/callback")

# Validate credentials
if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
    raise ValueError("Missing Strava credentials in environment")

try:
    STRAVA_CLIENT_ID = int(STRAVA_CLIENT_ID)
except ValueError:
    raise ValueError("STRAVA_CLIENT_ID must be a number")
