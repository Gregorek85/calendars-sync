from O365 import Account, FileSystemTokenBackend
import datetime as dt
import time

from .config import *


class MS365:
    def __init__(self):
        # authenticate microsoft graph api credentials
        scopes = ["basic", "calendar"]
        self.credentials = (MS_client_id, MS_client_secret)
        self.token_backend = FileSystemTokenBackend(
            token_path=outlook_token_path,
            token_filename=outlook_token_filename,
        )
        self.account = Account(
            self.credentials,
            token_backend=self.token_backend,
            tenant_id=MS_tenant_id or None,
        )
        if not self.account.is_authenticated:
            # not authenticated, throw error
            self.account.authenticate(scopes=scopes)
        print("Authenticated Microsoft")
        self.get_calendar()

    def get_calendar(self):
        # get default or named calendar to which this account has access to:
        if MS_calendar_name:
            self.cal = self.account.schedule().get_calendar(
                calendar_name=MS_calendar_name
            )
        else:
            self.cal = self.account.schedule().get_default_calendar()

    def delete_private_events(self):
        calendar = self.cal
        query = calendar.new_query("subject").contains("Private Event")
        events = list(
            self.cal.get_events(query=query, limit=None, include_recurring=False)
        )
        for event in events:
            print(event.start, event.end, event.subject)
            event.delete()

    def createEvent(self, name, body, start, duration=False):
        calendar = self.cal
        new_event = calendar.new_event()  # creates a new unsaved event
        new_event.subject = name
        new_event.body = body
        # naive datetimes will automatically be converted to timezone aware datetime
        #  objects using the local timezone detected or the protocol provided timezone
        new_event.start = start
        if duration:
            new_event.end = start + dt.timedelta(minutes=duration)
        # Check if such event exists:
        query = (
            self.cal.new_query("start")
            .greater_equal(start)
            .chain("and")
            .on_attribute("end")
            .less_equal(new_event.end)
        )
        events = list(
            self.cal.get_events(query=query, limit=None, include_recurring=True)
        )
        for event in events:
            if event.subject == name:
                print("Such event exists")
                return False
        # new_event.location = "This is a Virtual Classroom in Microsoft Teams"
        # new_event.remind_before_minutes = 45
        new_event.save()

    def get_outlook_events(self):
        # get all events from an outlook calendar
        start_time = time.time()
        start = dt.datetime.today() - dt.timedelta(days=previous_days)
        end = dt.datetime.today() + dt.timedelta(days=future_days)
        query = (
            self.cal.new_query("start")
            .greater_equal(start)
            .chain("and")
            .on_attribute("end")
            .less_equal(end)
        )
        events = self.cal.get_events(query=query, limit=None, include_recurring=True)
        events = list(events)

        elapsed_time = time.time() - start_time
        print(f"Retrieved {len(events)} events from Outlook in {elapsed_time} secs.")
        return events
