import datetime
import pytz
import os.path
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow

from flask import render_template, redirect, Flask, session, jsonify, url_for, request
import flask 
import requests

from dotenv import load_dotenv

load_dotenv()

CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CLIENT_ID=os.getenv("API_CLIENT_ID")
FLASK_SECRET=os.getenv("FLASK_SECRET")

API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

#activate flask
app = Flask(__name__)
app.secret_key = FLASK_SECRET

@app.route("/")
def index():
    return render_template("index.html")

#for documentation on google login go to:
#https://developers.google.com/identity/protocols/oauth2/web-server#python

@app.route("/authorize")
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    #this uri must match with the authorized uri in google console
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        #best practice for security
        #enable incremental authorization
        include_granted_scopes='true'
    )
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('index'))

@app.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return ('You need to <a href="/authorize">authorize</a> before testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **session['credentials']
    )

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers= {'content-type': 'application/x-www-form-urlencoded'})
    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return ('Credentials successfully revoken.' + print_index_table())
    else:
        return ('An error occurred.' + print_index_table())
    
@app.route('/clear')
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    return ('Credentials have been cleared. <br><br>'+print_index_table())
    
def credentials_to_dict(credentials):
    return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

def print_index_table():
  return ('<table>' +
          '<tr><td><a href="/test">Test an API request</a></td>' +
          '<td>Submit an API request and see a formatted JSON response. ' +
          '    Go through the authorization flow if there are no stored ' +
          '    credentials for the user.</td></tr>' +
          '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
          '<td>Go directly to the authorization flow. If there are stored ' +
          '    credentials, you still might not be prompted to reauthorize ' +
          '    the application.</td></tr>' +
          '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
          '<td>Revoke the access token associated with the current user ' +
          '    session. After revoking credentials, if you go to the test ' +
          '    page, you should see an <code>invalid_grant</code> error.' +
          '</td></tr>' +
          '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
          '<td>Clear the access token currently stored in the user session. ' +
          '    After clearing the token, if you <a href="/test">test the ' +
          '    API request</a> again, you should go back to the auth flow.' +
          '</td></tr></table>')


@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'credentials' in session:

        creds = google.oauth2.credentials.Credentials(
            **session['credentials']
        )
        print(creds)
        
        if request.method=='POST':
            title = request.form['title']
            time = request.form['time']
            add_event(creds, title, time)
            print('added')
            return render_template('index.html', result = 'success')
        else:
            return render_template('index.html', result = 'fail')
    else:
        return redirect(url_for('authorize'))

    # if request.method=='POST':
    #     creds = get_token_file_path(session['user_id'])
    #     title = request.form['title']
    #     time = request.form['time']
    #     add_event(creds, title, time)
    #     print('added')
    # return render_template('index.html', result = 'added')


def add_event(creds, title: str, duration_split: int) -> str:
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
        return (f'event created: {event}')
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


if __name__ == "__main__":
    # main()
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8080, debug=True)
