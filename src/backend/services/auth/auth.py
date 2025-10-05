from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.backend.utils.models.scopes import GoogleScopes
import os.path
# going through documentation
SCOPES = [GoogleScopes.CALENDAR_EVENTS]


class AuthService:
    """
    A service class for handling Google Calendar authentication and basic calendar operations.

    This class manages OAuth2 authentication with Google APIs and providesmethods
    to interact with Google Calendar. It handles token storage, refresh, and provides
    a simple interface for calendar operations.
    """

    def __init__(self):
        """
        Initialize the AuthService.

        Args:
            None

        Returns:
            None
        """
        self.creds: Credentials = None
        self.service = None

    def authenticate(self):
        """
        Authenticate with Google APIs using OAuth2 flow.

        Args:
            None

        Returns:
            None
        """
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file(
              "token.json", SCOPES
            )

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        # check if credentials are valid
        try:
            self.service = build("calendar", "v3", credentials=self.creds)
        except HttpError as error:
            print(f"An error occurred: {error}")
            self.service = None
