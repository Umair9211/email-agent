import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

def authenticate_gmail():

    creds = None

    # Check whether we already have an access token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_PATH), SCOPES
        )

    # If credentials are invalid, refresh or authenticate
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
    str(CREDENTIALS_PATH),
    SCOPES
)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

    # Connect to Gmail API
    service = build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )

    return service