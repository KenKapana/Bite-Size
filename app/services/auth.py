import requests
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
from flask import session, url_for

from app.config import CLIENT_SECRETS_FILE, SCOPES
from app.utils.helpers import credentials_to_dict

def create_oauth_flow(redirect_uri):
    """
    Create and configure the OAuth flow.
    """
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = redirect_uri
    return flow

def get_user_email(credentials):
    """
    Get the user's email from Google API.
    """
    userinfo_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
    headers = {'Authorization': f'Bearer {credentials.token}'}
    
    response = requests.get(userinfo_endpoint, headers=headers)
    user_info = response.json()

    return user_info.get('email')

def is_user_logged_in():
    """
    Check if the user is logged in and refresh token if necessary.
    """
    # Check if the credentials are in the session
    if 'credentials' not in session:
        return False
    
    # Load the credentials from the session
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    
    # Check if the credentials are valid and not expired
    if credentials and credentials.valid:
        return True
    
    # If the credentials have expired, try to refresh them
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(google.auth.transport.requests.Request())
            # Update the session with the new credentials
            session['credentials'] = credentials_to_dict(credentials)
            return True
        except Exception as e:
            print(f"Error refreshing credentials: {e}")
            return False
    
    return False

def revoke_credentials(credentials):
    """
    Revoke the OAuth credentials.
    """
    revoke = requests.post(
        'https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )
    
    return revoke.status_code