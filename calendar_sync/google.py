from google.auth.transport.requests import Request
import os
import pickle
import time
from .helpers import clean_subject
import datetime as dt

from .config import *
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


class Google:
    def __init__(self):
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ["https://www.googleapis.com/auth/calendar"]

        # authenticate google api credentials
        creds = None
        pp = "calendar_sync/credentials/google_token.pickle"
        if os.path.exists(pp):
            with open(pp, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "calendar_sync/credentials/client_secret.json", SCOPES
                )
                creds = flow.run_local_server()

            with open(pp, "wb") as token:
                pickle.dump(creds, token)

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

    def update_family_events(self):
        events = self.get_family_events()
        for event in events:
            event_id = event["id"]
            start = event.get("start", {})
            end = event.get("end", {})
            # Check if the event is not an all-day event
            if "dateTime" in start and "dateTime" in end:
                attendee = {"email": MS_calendar_email}
                try:
                    freshly_removed = False
                    attendees = event.get("attendees", [])
                    for att in attendees:
                        if (
                            att["email"] == MS_calendar_email
                            and att["responseStatus"] == "needsAction"
                        ):
                            attendees.remove(att)
                            event["attendees"] = attendees
                            event = self.g_events_service.update(
                                calendarId=family_google_calendar_id,
                                eventId=event_id,
                                body=event,
                            ).execute()
                            print(
                                f"Attendee {MS_calendar_email} removed from event {event_id}."
                            )
                            freshly_removed = True
                    if not freshly_removed:
                        event["attendees"] = event.get("attendees", []) + [attendee]
                        updated_event = self.g_events_service.update(
                            calendarId=family_google_calendar_id,
                            eventId=event_id,
                            body=event,
                            sendUpdates="all",
                        ).execute()
                        print(
                            f"Event {event_id} updated with attendee: {attendee['email']}"
                        )
                except HttpError as error:
                    print(f"Error updating event {event_id}: {error}")

    def get_family_events(self):
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()
        return self.getGoogleCalendarEvents(family_google_calendar_id, timeMin=now)

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
        print(
            f"Retrieved {len(gcal_events)} events across {i} pages from Google Calendar (id={gcid})."
        )
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
