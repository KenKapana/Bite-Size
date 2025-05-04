from firebase_admin import db
from app.utils.helpers import clean_email

def get_user_data(email):
    """
    Get user data from Firebase.
    """
    cleaned_email = clean_email(email)
    ref = db.reference(f'/clients/{cleaned_email}')
    return ref.get()

def add_todo_item(email, title, duration):
    """
    Add a to-do item to Firebase.
    """
    cleaned_email = clean_email(email)
    data = {"title": title, "duration": duration}

    user_ref = db.reference(f'/clients/{cleaned_email}')
    user_data = user_ref.get()
    
    if user_data:
        new_data_ref = user_ref.push()
        new_data_ref.set(data)
    else:
        user_ref.set({"data": data})
    
    return user_ref.get()

def delete_todo_item(email, key):
    """
    Delete a to-do item from Firebase.
    """
    cleaned_email = clean_email(email)
    ref = db.reference(f'/clients/{cleaned_email}/{key}')
    ref.delete()
    return True