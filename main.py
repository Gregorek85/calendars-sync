import datetime as dt
import time
from calendar_sync.google import Google
from calendar_sync.outlook import MS365
from dateutil import parser
from tqdm import tqdm
from HealthCheck_Pinger import pingDecor


@pingDecor("dc45150a-31e3-4786-9643-cc4aebb262f6")
def main():
    start_time = time.time()
    current_time = "{:%Y-%m-%d %H:%M:%S}".format(dt.datetime.now())
    print(f"Started at {current_time}.")
    # authenticate outlook and google credentials
    ms365 = MS365()
    google = Google()
    print("Deleting Private Events from Microsoft")
    ms365.delete_private_events()
    print("Get google events")
    events = google.get_family_events()
    print("Looping through family events")
    for google_event in tqdm(events):
        event_id = google_event["id"]
        start = google_event.get("start", {})
        end = google_event.get("end", {})
        # Check if the event is not an all-day event
        if "dateTime" in start and "dateTime" in end:
            # Create new events in Microsoft Calendar:
            subject = "Private Event"
            body = google_event["summary"]  # google_event.get("description", "")
            start = parser.isoparse(google_event["start"]["dateTime"])
            end = parser.isoparse(google_event["end"]["dateTime"])
            duration = (end - start).total_seconds() / 60.0
            ms365.createEvent(subject, body, start, duration)

    # delete all existing google events then add all outlook events
    google.delete_google_events()
    outlook_events = ms365.get_outlook_events()
    added = 0
    print("Adding MS events to Google family calendar")
    for event in outlook_events:
        if (
            not "Hiszp" in event.subject[:5]
            and not "Canceled" in event.subject[:8]
            and not "Private Event" in event.subject
        ):
            result = google.addEvent(event)
            assert isinstance(result, dict)
            time.sleep(0.1)
            added += 1

    elapsed_time = time.time() - start_time
    print(f"Added {added} events to Google in {elapsed_time} secs.")
    # all done
    elapsed_time = time.time() - start_time
    print(f"Finished in {elapsed_time} secs.\n")


if __name__ == "__main__":
    main()
