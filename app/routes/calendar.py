from flask import Blueprint, redirect, url_for, request, session, jsonify
import google.oauth2.credentials

from app.services.calendar import add_event

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/add_now')
def add_now():
    """
    Add an event to the calendar now.
    """
    if 'credentials' in session:
        creds = google.oauth2.credentials.Credentials(**session['credentials'])
        title = request.args.get('title')
        duration = request.args.get('duration')
        result = add_event(creds, title, duration)
        return redirect(url_for('todo.index', result='success'))
    else:
        return redirect(url_for('auth.authorize'))

@calendar_bp.route('/submit_hours', methods=['POST'])
def submit_hours():
    """
    Submit the hours when the user doesn't want to schedule tasks.
    """
    selected_hours = request.form.getlist('hours')
    selected_hours = list(map(int, selected_hours))

    session['selected_hours'] = selected_hours
    session['update_successful'] = True

    return redirect(url_for('todo.index'))

@calendar_bp.route('/check_update_success')
def check_update_success():
    """
    Check if the hours update was successful.
    """
    update_successful = session.pop('update_successful', False)
    return jsonify({'update_successful': update_successful})