import datetime as dt
import os
import pickle
import time

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from O365 import Account, FileSystemTokenBackend

import config

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def authenticate_outlook():
    # authenticate microsoft graph api credentials
    scopes = ["basic", "calendar"]
    credentials = (config.MS_client_id, config.MS_client_secret)
    token_backend = FileSystemTokenBackend(
        token_path=config.outlook_token_path,
        token_filename=config.outlook_token_filename,
    )
    account = Account(
        credentials,
        token_backend=token_backend,
        tenant_id=config.MS_tenant_id or None,
    )
    if not account.is_authenticated:
        # not authenticated, throw error
        account.authenticate(scopes=scopes)

    # connection = Connection(
    #     credentials, token_backend=token_backend, scopes=scopes
    # )
    # connection.refresh_token()

    print("Authenticated Outlook.")
    return account


def authenticate_google():
    # authenticate google api credentials
    creds = None
    pp = "./credentials/google_token.pickle"
    if os.path.exists(pp):
        with open(pp, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = service_account.Credentials.from_service_account_file(
                "./credentials/google_token.json", scopes=SCOPES
            )
        # Save the credentials for the next run
        with open(pp, "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)
    print("Authenticated Google.")
    return service


def get_outlook_events(cal):
    # get all events from an outlook calendar
    start_time = time.time()

    start = dt.datetime.today() - dt.timedelta(days=config.previous_days)
    end = dt.datetime.today() + dt.timedelta(days=config.future_days)
    query = (
        cal.new_query("start")
        .greater_equal(start)
        .chain("and")
        .on_attribute("end")
        .less_equal(end)
    )
    events = cal.get_events(query=query, limit=None, include_recurring=True)
    events = list(events)

    elapsed_time = time.time() - start_time
    print(f"Retrieved {len(events)} events from Outlook in {elapsed_time} secs.")
    return events


def clean_subject(subject):
    # remove prefix clutter from an outlook event subject
    remove = [
        "Fwd: ",
        "Invitation: ",
        "Updated invitation: ",
        "Updated invitation with note: ",
    ]
    for s in remove:
        subject = subject.replace(s, "")
    return subject


def clean_body(body):
    #TODO
    # strip out html and excess line returns from outlook event body
    text = BeautifulSoup(body, "html.parser").get_text()
    return text.replace("\n", " ").replace("\r", "\n")


def build_gcal_event(event):
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


def delete_google_events(g_events_service):
    # delete all events from google calendar
    start_time = time.time()
    gcid = config.google_calendar_id
    mr = 2500

    # retrieve a list of all events
    result = g_events_service.list(calendarId=gcid, maxResults=mr).execute()
    gcal_events = result.get("items", [])

    # if nextPageToken exists, we need to paginate: sometimes a few items are
    # spread across several pages of results for whatever reason
    i = 1
    while "nextPageToken" in result:
        npt = result["nextPageToken"]
        result = g_events_service.list(
            calendarId=gcid, maxResults=mr, pageToken=npt
        ).execute()
        gcal_events.extend(result.get("items", []))
        i += 1
    print(f"Retrieved {len(gcal_events)} events across {i} pages from Google.")

    # delete each event retrieved
    for gcal_event in gcal_events:
        request = g_events_service.delete(
            calendarId=config.google_calendar_id, eventId=gcal_event["id"]
        )
        result = request.execute()
        assert result == ""
        time.sleep(0.1)

    elapsed_time = time.time() - start_time
    print(f"Deleted {len(gcal_events)} events from Google in {elapsed_time} secs.")


def add_google_events(g_events_service, events):
    # add all events to google calendar
    start_time = time.time()

    for event in events:
        e = build_gcal_event(event)
        result = g_events_service.insert(
            calendarId=config.google_calendar_id, body=e
        ).execute()
        assert isinstance(result, dict)
        time.sleep(0.1)

    elapsed_time = time.time() - start_time
    print(f"Added {len(events)} events to Google in {elapsed_time} secs.")


if __name__ == "__main__":
    current_time = "{:%Y-%m-%d %H:%M:%S}".format(dt.datetime.now())
    print(f"Started at {current_time}.")
    start_time = time.time()

    # authenticate outlook and google credentials
    outlook_acct = authenticate_outlook()
    google = authenticate_google()
    g_events_service = google.events()

    # get default or named calendar to which this account has access to:
    if config.MS_calendar_name:
        outlook_cal = outlook_acct.schedule().get_calendar(
            calendar_name=config.MS_calendar_name
        )
    else:
        outlook_cal = outlook_acct.schedule().get_default_calendar()
    # delete all existing google events then add all outlook events
    delete_google_events(g_events_service)
    # exit()
    # get all events from outlook
    outlook_events = get_outlook_events(outlook_cal)

    # check if all the current event ids/timestamps match the previous run
    # only update google calendar if they don't all match (means there are changes)
    if True:  # TODO
        add_google_events(g_events_service, outlook_events)
    else:
        print("No changes found.")

    # all done
    elapsed_time = time.time() - start_time
    print(f"Finished in {elapsed_time} secs.\n")
