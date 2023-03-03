import datetime as dt
import time
from calendar_sync.google import Google
from calendar_sync.outlook import MS365
from calendar_sync.config import MS_calendar_email, family_google_calendar_id
from googleapiclient.errors import HttpError
from dateutil import parser
from dateutil.rrule import rrulestr

if __name__ == "__main__":
    current_time = "{:%Y-%m-%d %H:%M:%S}".format(dt.datetime.now())
    print(f"Started at {current_time}.")
    start_time = time.time()
    # authenticate outlook and google credentials
    ms365 = MS365()
    google = Google()
    ms365.delete_private_events()
    events = google.get_family_events()
    for google_event in events:
        event_id = google_event["id"]
        start = google_event.get("start", {})
        end = google_event.get("end", {})
        # Check if the event is not an all-day event
        if "dateTime" in start and "dateTime" in end:
            # remove my email if it was invited, as this was old solution
            # try:
            #     attendees = google_event.get("attendees", [])
            #     for att in attendees:
            #         if att["email"] == MS_calendar_email:
            #             attendees.remove(att)
            #             google_event["attendees"] = attendees
            #             google_event = google.g_events_service.update(
            #                 calendarId=family_google_calendar_id,
            #                 eventId=event_id,
            #                 body=google_event,
            #                 sendUpdates="all",
            #             ).execute()
            #             print(
            #                 f"Attendee {MS_calendar_email} removed from event {event_id}."
            #             )
            # except HttpError as error:
            #     print(f"Error updating event {event_id}: {error}")
            # Create new events in Microsoft Calendar:
            subject = "Private Event"
            body = google_event["summary"]  # google_event.get("description", "")
            # event.location = google_event.get("location", "")
            start = parser.isoparse(
                google_event["start"]["dateTime"]
            )  # .replace(tzinfo=None)
            end = parser.isoparse(
                google_event["end"]["dateTime"]
            )  # .replace(tzinfo=None)
            # print(start)
            # print(google_event["start"]["timeZone"])
            # print(body)
            # continue
            duration = (end - start).total_seconds() / 60.0
            # start = start + dt.timedelta(hours=2)
            google_recurrence = google_event.get("recurrence", None)
            if not google_recurrence:
                # print(f"Not recurring:{start}")
                ms365.createEvent(subject, body, start, duration)
            else:
                rrule = rrulestr(google_recurrence[0], dtstart=start)
                # print(rrule)
                list_of_events = list(rrule)
                i = min(2, len(list_of_events))
                for event_start in list_of_events:
                    if event_start.date() > dt.date.today():
                        print(event_start)
                        ms365.createEvent(subject, body, event_start, duration)
                        i -= 1
                    if i == 0:
                        break
    # delete all existing google events then add all outlook events
    google.delete_google_events()
    # exit()
    # get all events from outlook
    outlook_events = ms365.get_outlook_events()
    # check if all the current event ids/timestamps match the previous run
    # only update google calendar if they don't all match (means there are changes)
    start_time = time.time()
    added = 0
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
