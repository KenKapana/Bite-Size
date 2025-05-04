import datetime
import pytz
from flask import session
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def add_event(creds, title, duration):
    """
    Add an event to the user's Google Calendar.
    """
    try:
        service = build("calendar", "v3", credentials=creds)
    except HttpError as error:
        print(f"An error occurred in add_event: {error}")
        return None

    now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
    now = now.replace(minute=0, second=0, microsecond=0)

    duration = int(duration)
    days_passed = 0
    events_added = 0

    while events_added < duration:
        cur = now + datetime.timedelta(days=days_passed)
        
        # Decides which hour to start
        # If today hour is not replaced, but future dates have 0 as their hours
        if days_passed == 0:
            event_start_hour = time_window(creds, 1, cur)
        else:
            cur = cur.replace(hour=0)
            event_start_hour = time_window(creds, 1, cur)

        # If there's not enough time today to fit the task
        # Loops through the days until it finds an open spot
        while event_start_hour == -1:
            cur += datetime.timedelta(days=1)
            cur = cur.replace(hour=0)
            days_passed += 1
            event_start_hour = time_window(creds, 1, cur)

        start_time = cur.replace(hour=event_start_hour)
        event_end = start_time + datetime.timedelta(hours=1)

        # Calls Google API
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': event_end.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        events_added += 1
        days_passed += 1

    return title

def time_window(creds, duration_of_task, cur_date):
    """
    Finds an open window for select duration of time and returns the starting time.
    Creates based on current hour and goes up by the hour.
    """
    try:
        occupied_time = get_event_durations(creds, cur_date)
        
        # Two pointer to find open slot of time
        # Beginning starts from current hour plus one
        cur_hour = cur_date.hour
        beginning = cur_hour + 1
        # End, the second of the two pointer, will start at the same point as beginning
        end = beginning

        hours_in_a_day = 24

        while end < hours_in_a_day:
            if end in occupied_time or beginning in occupied_time:
                beginning = end
            elif (end - beginning) == duration_of_task:
                return beginning
            end += 1

        # If no slots are open today -1 is returned
        return -1
                 
    except HttpError as error:
        print(f'An error occurred: {error}')
        return -1

def get_event_durations(creds, cur_date, calendar_id='primary'):
    """
    Get the hours that are already occupied by events.
    """
    try:
        # Calls Google Calendar API
        service = build('calendar', 'v3', credentials=creds)

        # Creates time frame to check for events
        start_of_hour = cur_date.replace(minute=0, second=0, microsecond=0)
        end_of_hour = cur_date.replace(hour=23, minute=59, second=59)

        # Format
        timeMin = start_of_hour.isoformat()
        timeMax = end_of_hour.isoformat()
        
        # Gets list of events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # For clear schedule
        if not events:
            return []

        # Creates list of occupied hours
        occupied_time = []

        # This loop goes through each event of today
        for event in events:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')

            event_start = datetime.datetime.fromisoformat(start).hour
            event_end = datetime.datetime.fromisoformat(end).hour
            
            # This loop appends the event hours to the list
            for i in range(event_start, event_end):
                occupied_time.append(i)
        
        # Add user-specified down time
        if 'selected_hours' in session:
            down_time = session['selected_hours']
            occupied_time.extend(down_time)
            
        return occupied_time

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []