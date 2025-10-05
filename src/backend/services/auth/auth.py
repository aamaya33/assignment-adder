from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.backend.utils.models.scopes import GoogleScopes
import datetime
import os.path

# going through documentation
SCOPES = [GoogleScopes.CALENDAR_EVENTS]


class AuthService:
    """
    A service class for handling Google Calendar authentication and basic calendar operations.
    
    This class manages OAuth2 authentication with Google APIs and provides methods
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
        print(os.getcwd())
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

    def print_calendar(self):
        """
        Fetch and print upcoming calendar events to the console.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            HttpError: If there's an error communicating with the Google Calendar API
        """
        try:
            self.service = build("calendar", "v3", credentials=self.creds)

            now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            print("Getting the upcoming 10 events")
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return

            # Prints the start and name of the next 10 events
            for event in events:
                start = event["start"].get(
                    "dateTime",
                    event["start"].get("date"))
                print(start, event["summary"])
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_calendar_events(self):
        """
        Get calendar events from the Google Calendar API.
        """
        self.service = build("calendar", "v3", credentials=self.creds)
        events_result = self.service.events().list(calendarId="primary").execute()
        return events_result.get("items", [])


test = AuthService()
test.authenticate()
print(test.get_calendar_events())