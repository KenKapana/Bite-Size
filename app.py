import datetime
import pytz
import os.path
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from flask import render_template, redirect, Flask, session, url_for, request
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
    return render_template("index.html", result='')

@app.route('/test')
def test_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  files = drive.files().list().execute()

  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.jsonify(**files)

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

@app.route('/logout', methods=['GET', 'POST'])
def logOut():
  if 'credentials' not in session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **session['credentials'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())

@app.route('/revoke')
def revoke():
  if 'credentials' not in session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **session['credentials'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())
    
@app.route('/clear', methods=['POST', 'GET'])
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    return redirect(url_for('index'))
    
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
            result = add_event(creds, title, time)
            return render_template('index.html', result=result)
        else:
            return render_template('index.html', result='uh oh, something went wrong')
    else:
        return redirect(url_for('authorize'))


def add_event(creds, title: str, duration: int) -> str:
    """
    Add an event to the user's Google Calendar.
    """
    try:
        service = build("calendar", "v3", credentials=creds)
    except HttpError as error:
        print(f"An error occurred in add_event: {error}")

    #for now one hour each tasks
    #now is formatted like: class datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)
    #but for the future, time_window can find slots for duration longer than 1 hour
    for loop in range(int(duration)+1):

        now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        now = now.replace(minute=0, second=0, microsecond=0)
        now+= datetime.timedelta(days=loop)
        #decides which hour to start
        #if today hour is not replaced, but future dates have 0 as their hours
        if loop==0:
           event_start_hour = time_window(creds, 1, int(now.day), True)

        else:
            now = now.replace(hour=0)
            event_start_hour = time_window(creds, 1, int(now.day+loop), False)

        #if there's not enough time today to fit the task
        #loops thru the days until it finds an open spot
        while event_start_hour == -1:
            now += datetime.timedelta(days=1)
            event_start_hour = time_window(creds, 1, now.day, False)

        start_time = now.replace(hour=event_start_hour)

        event_end = start_time.replace(hour=(start_time.hour+1))

        #calls google api
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
    
    return 'events added'


def time_window(creds, duration_of_task: int, date: int, keep_hour: bool):
    """
    finds an open window for select duration of time and returns the starting time
    creates based on current hour and goes up by the hour
    """
    try:
        
        #now is formatted like: class datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)
        now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        if keep_hour:
            now = now.replace(day=date, minute=0, second=0, microsecond=0)
        else:
            now = now.replace(day=date,hour=0, minute=0, second=0, microsecond=0)

        occupied_time = get_event_durations(creds, date)
        #two pointer to find open slot of time
        #beginning starts from current hour plus one
        beginning=now.hour+1
        #end, the second of the two pointer, will start at the same point as beginning
        end=beginning

        #hours in a day
        hours_in_a_day = 24

        while end<=hours_in_a_day:
            if end in occupied_time or beginning in occupied_time:
               beginning=end
            elif (end-beginning)==duration_of_task:
                return beginning
            end+=1

        #if no slots are open today -1 is returned
        return -1
                 
    except HttpError as error:
        print(f'An error occurred: {error}')
        return -1

def get_event_durations(creds, day: int, calendar_id='primary') -> dict:
    try:
        #calls google calendar api
        service = build('calendar', 'v3', credentials=creds)

        #creates time frame to check for events
        #now is formatted like: class datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)

        now = datetime.datetime.now(tz=pytz.timezone('America/Los_Angeles'))
        start_of_hour = now.replace(day=day, minute=0, second=0, microsecond=0)
        end_of_hour = now.replace(hour=23, minute=59, second=59)

        #format
        timeMin = start_of_hour.isoformat()
        timeMax = end_of_hour.isoformat()
        
        #gets list of events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        #for clear schedule
        if not events:
            return {}

        #creates dict of event times
        #the value is the title and the key is the hour of the day
        occupied_time = {}

        #this loop goes thru each event of today
        for event in events:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')

            #gets title to save as value for the dictionary
            summary = event.get('summary')

            event_start = datetime.datetime.fromisoformat(start).hour
            event_end = datetime.datetime.fromisoformat(end).hour
            
            #this loop appends the events hours to the dict
            for i in range(event_start, event_end):
                # print('im in loop lol', i)
                occupied_time[i] = summary

        print(occupied_time)
        return occupied_time

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/calendar"]


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8080, debug=True)
