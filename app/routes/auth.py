from flask import Blueprint, redirect, session, request, url_for, jsonify
import google.oauth2.credentials

from app.services.auth import (
    create_oauth_flow, 
    get_user_email, 
    revoke_credentials, 
    is_user_logged_in
)
from app.utils.helpers import credentials_to_dict

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/authorize")
def authorize():
    """
    Start the OAuth flow with Google.
    """
    flow = create_oauth_flow(url_for('auth.oauth2callback', _external=True))
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state

    return redirect(authorization_url)

@auth_bp.route('/oauth2callback')
def oauth2callback():
    """
    Handle the OAuth callback from Google.
    """
    state = session['state']

    flow = create_oauth_flow(url_for('auth.oauth2callback', _external=True))
    flow.state = state
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('todo.index'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Revoke credentials and log out.
    """
    if 'credentials' not in session:
        return redirect(url_for('todo.index'))

    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    status_code = revoke_credentials(credentials)
    
    # Even if revocation fails, we'll clear the session
    if 'credentials' in session:
        del session['credentials']
    
    return redirect(url_for('todo.index'))

@auth_bp.route('/check_login')
def check_login():
    """
    Check if the user is logged in.
    """
    return jsonify({'logged_in': is_user_logged_in()})

@auth_bp.route('/clear', methods=['POST', 'GET'])
def clear_credentials():
    """
    Clear credentials from session.
    """
    if 'credentials' in session:
        del session['credentials']
    return redirect(url_for('todo.index'))