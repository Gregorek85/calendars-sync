from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import pickle
import time
from .helpers import clean_subject, clean_body
import datetime as dt

from .config import *

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class Google:
    def __init__(self):
        # authenticate google api credentials
        creds = None
        pp = "calendar_sync/credentials/google_token.pickle"
        if os.path.exists(pp):
            with open(pp, "rb") as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = service_account.Credentials.from_service_account_file(
                    "calendar_sync/credentials/google_token.json", scopes=SCOPES
                )
            # Save the credentials for the next run
            with open(pp, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("calendar", "v3", credentials=creds)
        self.g_events_service = self.service.events()
        print("Authenticated Google.")

    def build_gcal_event(self, event):
        # construct a google calendar event from an outlook event

        e = {
            "summary": clean_subject(event.subject),
            "location": event.location["displayName"],
            "description": clean_body(event.body),
        }

        if event.is_all_day:
            # all day events just get a start/end date
            # use UTC start date to get correct day
            date = str(event.start.astimezone(dt.datetime.utcnow()).date())
            start_end = {"start": {"date": date}, "end": {"date": date}}
        else:
            # normal events have start/end datetime/timezone
            start_end = {
                "start": {
                    "dateTime": str(event.start).replace(" ", "T"),
                    "timeZone": str(event.start.tzinfo),
                },
                "end": {
                    "dateTime": str(event.end).replace(" ", "T"),
                    "timeZone": str(event.end.tzinfo),
                },
            }

        e.update(start_end)
        return e

    def delete_google_events(self):
        # delete all events from google calendar
        start_time = time.time()
        gcid = google_calendar_id
        mr = 2500
        # retrieve a list of all events
        result = self.g_events_service.list(calendarId=gcid, maxResults=mr).execute()
        gcal_events = result.get("items", [])

        # if nextPageToken exists, we need to paginate: sometimes a few items are
        # spread across several pages of results for whatever reason
        i = 1
        while "nextPageToken" in result:
            npt = result["nextPageToken"]
            result = self.g_events_service.list(
                calendarId=gcid, maxResults=mr, pageToken=npt
            ).execute()
            gcal_events.extend(result.get("items", []))
            i += 1
        print(f"Retrieved {len(gcal_events)} events across {i} pages from Google.")

        # delete each event retrieved
        for gcal_event in gcal_events:
            request = self.g_events_service.delete(
                calendarId=google_calendar_id, eventId=gcal_event["id"]
            )
            result = request.execute()
            assert result == ""
            time.sleep(0.1)

        elapsed_time = time.time() - start_time
        print(f"Deleted {len(gcal_events)} events from Google in {elapsed_time} secs.")

    def addEvent(self, event):
        self.g_events_service.insert(
            calendarId=google_calendar_id, body=self.build_gcal_event(event)
        ).execute()
