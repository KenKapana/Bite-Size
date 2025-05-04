import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth Configuration
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar", 
          "https://www.googleapis.com/auth/userinfo.email", 
          "openid"]
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CLIENT_ID = os.getenv("API_CLIENT_ID")
FLASK_SECRET = os.getenv("FLASK_SECRET")

# Google API Services
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

# Firebase Configuration
FIREBASE_DATABASE_URL = "https://bite-size-59972-default-rtdb.firebaseio.com"