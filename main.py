import datetime as dt
import time
from calendar_sync.google import Google
from calendar_sync.outlook import MS365

if __name__ == "__main__":
    current_time = "{:%Y-%m-%d %H:%M:%S}".format(dt.datetime.now())
    print(f"Started at {current_time}.")
    start_time = time.time()
    # authenticate outlook and google credentials
    ms365 = MS365()
    google = Google()
    family_events = google.update_family_events()
    exit()
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
        if not "Hiszp" in event.subject[:5] and not "Canceled" in event.subject[:8]:
            result = google.addEvent(event)
            assert isinstance(result, dict)
            time.sleep(0.1)
            added += 1

    elapsed_time = time.time() - start_time
    print(f"Added {added} events to Google in {elapsed_time} secs.")
    # now update events from Google family calendar to make sure they include my company address:
    family_events = google.update_family_events()
    # all done
    elapsed_time = time.time() - start_time
    print(f"Finished in {elapsed_time} secs.\n")
