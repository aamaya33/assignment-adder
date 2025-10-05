from src.backend.services.auth.auth import AuthService
from datetime import datetime
from googleapiclient.errors import HttpError


class CalendarService:
    def __init__(self):
        self.auth_service = AuthService()
        self.auth_service.authenticate()
        self.service = self.auth_service.service

    def get_calendar_events(self, max_results=10):
        """

        Fetch the upcoming calendar events.

        Args:
            max_results (int): Maximum number of events to fetch.
        Returns:
            List of upcoming events.

        Raises:
            HttpError: If an error occurs while fetching events.

        """
        try:
            now = datetime.datetime.utcnow().isoformat()
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            return events
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def print_events(self, events):
        if not events:
            print('No upcoming events found.')
            return
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
