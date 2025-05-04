from flask import Blueprint, redirect, render_template, url_for, request, session
import google.oauth2.credentials

from app.services.auth import get_user_email
from app.services.firebase import get_user_data, add_todo_item, delete_todo_item

todo_bp = Blueprint('todo', __name__)

@todo_bp.route("/")
def index():
    """
    Main index route showing the todo list.
    """
    if 'credentials' in session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        email = get_user_email(credentials)
        if email is not None:
            data = get_user_data(email)
        else:
            return render_template("index.html")
        down_time = session.get('selected_hours')
        
        return render_template("index.html", data=data, selected_hours=down_time)
    else:
        return render_template("index.html")

@todo_bp.route("/add", methods=['POST'])
def add():
    """
    Process the form submission to add a task.
    """
    title = request.form['title']
    duration = request.form['duration']
    action = request.form['action']

    if action == 'add_now':
        return redirect(url_for('calendar.add_now', title=title, duration=int(duration)))
    elif action == 'add_later':
        return redirect(url_for('todo.add_later', title=title, duration=int(duration)))

@todo_bp.route('/add_later')
def add_later():
    """
    Add a task to the to-do list for later.
    """
    title = request.args.get('title')
    duration = request.args.get('duration')

    if 'credentials' in session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        email = get_user_email(credentials)
        data = add_todo_item(email, title, duration)
        
        return render_template('index.html', data=data)
    else:
        return redirect(url_for('auth.authorize'))

@todo_bp.route('/delete_data/<key>', methods=['POST'])
def delete_data(key):
    """
    Delete a task from the to-do list.
    """
    if 'credentials' in session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        email = get_user_email(credentials)
        delete_todo_item(email, key)
        
        return redirect(url_for('todo.index'))
    else:
        return redirect(url_for('auth.authorize'))

@todo_bp.route('/add_now_from_todo/<key>/<title>/<duration>', methods=['POST'])
def add_now_from_todo(key, title, duration):
    """
    Add a task from the to-do list to the calendar.
    """
    if 'credentials' in session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        email = get_user_email(credentials)
        delete_todo_item(email, key)
       
        title = title.replace('%20', ' ')
        return redirect(url_for('calendar.add_now', title=title, duration=duration))
    else:
        return redirect(url_for('auth.authorize'))