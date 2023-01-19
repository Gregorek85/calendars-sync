# outlook
MS_client_id = "your-client-id-here"
MS_client_secret = "your-client-secret-here"
outlook_scopes = ["basic", "calendar"]
outlook_token_path = "./credentials/"
outlook_token_filename = "outlook_token.txt"
MS_calendar_name = "your_calendar_name_or_make_it_False_to_use_default_for_account"
MS_tenant_id = "your tenant id"
previous_days = 40  # retrieve this many past days of events
future_days = 365  # retrieve this many future days of events

# google
google_calendar_id = "your-calendar-id-here@group.calendar.google.com"

# misc
events_ts_json_path = "./events_ts.json"
force = False  # force full run even if no changes
