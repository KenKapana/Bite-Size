import datetime
import pytz
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from flask import Flask, render_template, request, jsonify

from dotenv import load_dotenv
from pprint import pprint
import requests
import os

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main(title="", time="0"):

    request_url = f'https://www.googleapis.com/calendar/v3/calendars/rpsj44u6koirtq5hehkt21qs6k%40group.calendar.google.com/events?appid={os.geteng("API_KEY")}&q={title}&v={time}'

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    
    add_event(creds, time, title)
    return 

#key=AIzaSyBH79yPuU82JSl0tKX8CfqJBEHFwdFlJL8
def add_event(creds, duration_split: int, title: str) -> str:
    """
    Add an event to the user's Google Calendar.
    """
    duration_split = int(duration_split)
    #splits work time if over 7 hours long
    if int(duration_split) > 7:
        duration_split = duration_split // 7  # 7 = days in a week

    #finds starting time for task to fit in schedule
    event_start = time_window(creds, duration_split)

    try:
        service = build("calendar", "v3", credentials=creds)

        open_hour = int(event_start)
        # print(open_hour)

        today = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        start_time = today.replace(hour=open_hour, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(hours=duration_split)

        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        # return (f'Event created:\nTime: {start_time}-{end_time}\nName: {title}\nLink: {event.get("htmlLink")}')
        return (f'event created: {title}')
    except HttpError as error:
        print(f"An error occurred in add_event: {error}")

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/calendar']


    

def time_window(creds, duration_of_task: int):
    """
    finds an open window for select duration of time and returns the starting time
    creates based on current hour and goes up by the hour
    """
    try:
        # Call the Calendar API for current time
        now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        start_time = now.replace(minute=0, second=0, microsecond=0)

        occupied_time = get_event_durations(creds)
        opening_found = False
        time_frame = 0
        start = -1
        for hour in range(start_time.hour+1, 24):
            if time_frame == duration_of_task and opening_found == True:
                # print('done')
                return start

            if (hour not in occupied_time) and opening_found == False:
                # print('found opening')
                start = hour
                opening_found = True
                time_frame += 1

            elif hour in occupied_time and opening_found == True:
                # print('closed before time fulfilled')
                start = -1
                time_frame=0
                opening_found = False
                
            elif hour not in occupied_time and opening_found==True:
                # print('still open')
                time_frame += 1

            # else:
            #     print('booked')
            
        return start
    except HttpError as error:
        print(f'An error occurred: {error}')
        return -1

def get_event_durations(creds, calendar_id='primary'):
    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        start_of_hour = now.replace(minute=0, second=0, microsecond=0)
        end_of_hour = now.replace(hour=23, minute=59, second=59)

        timeMin = start_of_hour.isoformat()
        timeMax = end_of_hour.isoformat()
        # print(timeMin, timeMax)
        # print('Getting events from the current hour')
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            # print('No events found for the current hour.')
            return []

        event_details = []
        occupied_time = {}
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary')

            # print(f"Event: {summary}, Start: {start}, End: {end}")
            event_details.append((summary, start, end))

            # duration = end_time - start_time
            # event_durations.append(duration.total_seconds() / 3600)  # Convert duration to hours
            # print(f"Event: {summary}, Start: {start}, End: {end}, Duration: {duration}")
            # print(end_time.hour, start_time.hour)

            # creating dictionary of filled schedule
            event_start = datetime.datetime.fromisoformat(start).hour
            event_end = datetime.datetime.fromisoformat(end).hour
            
            # print('start: ', event_start, 'end: ', event_end)
            for i in range(event_start, event_end):
                # print('im in loop lol', i)
                occupied_time[i] = summary

        # print(event_details)
        return occupied_time

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/calendar"]

# def authenticate_google_calendar():
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
   
# def commitHours(creds):
#     """
#     Save previous events into database.
#     """
#     try:
#         service = build("calendar", "v3", credentials=creds)

#         # Call the Calendar API
#         today = datetime.datetime.today()
#         timeMin = today.replace(hour=9, minute=0, second=0, microsecond=0).isoformat() + "Z"
#         timeMax = today.replace(hour=17, minute=0, second=0, microsecond=0).isoformat() + "Z"
#         print("Getting today's coding hours")
#         events_result = (
#             service.events()
#             .list(
#                 calendarId="primary",
#                 timeMin=timeMin,
#                 timeMax=timeMax,
#                 singleEvents=True,
#                 orderBy="startTime"
#             )
#             .execute()
#         )
#         events = events_result.get("items", [])

#         if not events:
#             print("No upcoming events found.")
#             return
        
#         total_duration = datetime.timedelta(
#             seconds=0,
#             minutes=0,
#             hours=0,
#         )
#         print("Coding hours:")
#         for event in events:
#             start = event['start'].get('dateTime', event['start'].get('date'))
#             end = event['end'].get('dateTime', event['end'].get('date'))

#             start_formatted = parser.isoparse(start)
#             end_formatted = parser.isoparse(end)
#             duration = end_formatted - start_formatted
#             total_duration += duration
#             print(f"{event['summary']}, duration: {duration}")
#         print(f"Total coding time: {total_duration}")

#     except HttpError as error:
#         print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
