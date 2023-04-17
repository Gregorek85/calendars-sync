from google.auth.transport.requests import Request
import os
import json
import time
from .helpers import clean_subject
import datetime as dt
from google.oauth2.credentials import Credentials
from .config import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
import traceback


class Google:
    def __init__(self):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        # authenticate google api credentials
        creds = None
        pp = "calendar_sync/credentials/google_token.json"
        if os.path.exists(pp):
            creds = Credentials.from_authorized_user_file(pp, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    request = Request()
                    creds.refresh(request)
                except RefreshError:
                    traceback.print_exc()
                    print("error refreshing credentials")
                    os.sys.exit(1)
                except:
                    print("Other error occurred")
                    traceback.print_exc()
                    os.sys.exit(1)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "calendar_sync/credentials/client_secret.json", SCOPES
                )
                creds = flow.run_local_server()
            with open(pp, "w") as token:
                json.dump(json.loads(creds.to_json()), token)
        self.service = build("calendar", "v3", credentials=creds)
        self.g_events_service = self.service.events()
        print("Authenticated Google.")

    def build_gcal_event(self, event):
        # get number of attendees:
        no = 0
        for at in event.attendees:
            no += 1
        if " ".join(str(event.organizer).split(" ", 2)[:2]) == MS_calendar_name:
            no += 1
        # construct a google calendar event from an outlook event
        e = {
            "summary": clean_subject(event.subject),
            "location": event.location["displayName"],
            "description": f"Wydarzenie z pracy R, liczba uczestników: {no}",
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

    def get_family_events(self):
        # Using now did not work because of recurrent events
        # now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
        start_date = dt.datetime(
            2023, 4, 1, 8, 0, 0, 0, tzinfo=dt.timezone.utc
        ).isoformat()
        return self.getGoogleCalendarEvents(
            family_google_calendar_id, timeMin=start_date
        )

    def getGoogleCalendarEvents(self, google_calendar_id, timeMin=None):
        gcid = google_calendar_id
        mr = 2500
        # retrieve a list of all events
        result = self.g_events_service.list(
            calendarId=gcid, maxResults=mr, timeMin=timeMin
        ).execute()
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
        # print(
        #     f"Retrieved {len(gcal_events)} events across {i} pages from Google Calendar (id={gcid})."
        # )
        return gcal_events

    def delete_google_events(self):
        # delete all events from google calendar
        start_time = time.time()
        gcal_events = self.getGoogleCalendarEvents(google_calendar_id)
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
        return self.g_events_service.insert(
            calendarId=google_calendar_id, body=self.build_gcal_event(event)
        ).execute()
