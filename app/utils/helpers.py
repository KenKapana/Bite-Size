def clean_email(email):
    """
    Replace periods in email with commas for Firebase compatibility.
    """
    return email.replace('.', ',')
    
def credentials_to_dict(credentials):
    """
    Convert credentials object to dictionary for session storage.
    """
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }