import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

class Config:
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://localhost:5000/callback')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    ACCOUNT_KEY_PATH = os.getenv('ACCOUNT_KEY_PATCH', "serviceAccountKey.json")

cred = credentials.Certificate(Config.ACCOUNT_KEY_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()
