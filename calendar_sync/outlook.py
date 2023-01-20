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
