from flask import Blueprint, jsonify, redirect, session, url_for
import google.oauth2.credentials
from googleapiclient.discovery import build

from app.config import API_SERVICE_NAME, API_VERSION
from app.utils.helpers import credentials_to_dict

test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/')
def test_api_request():
    """
    Test the Google API connection.
    """
    if 'credentials' not in session:
        return redirect(url_for('auth.authorize'))

    # Load credentials from the session
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])

    drive = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    files = drive.files().list().execute()

    # Save credentials back to session in case access token was refreshed
    session['credentials'] = credentials_to_dict(credentials)

    return jsonify(**files)