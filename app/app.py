from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from config import db
import requests
import time

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(client_id=app.config['SPOTIPY_CLIENT_ID'],
                            client_secret=app.config['SPOTIPY_CLIENT_SECRET'],
                            redirect_uri=app.config['SPOTIPY_REDIRECT_URI'],
                            scope="user-read-playback-state user-modify-playback-state")
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(client_id=app.config['SPOTIPY_CLIENT_ID'],
                            client_secret=app.config['SPOTIPY_CLIENT_SECRET'],
                            redirect_uri=app.config['SPOTIPY_REDIRECT_URI'])
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('sync'))

def get_spotify_client():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    if token_info['expires_at'] < time.time():
        sp_oauth = SpotifyOAuth(client_id=app.config['SPOTIPY_CLIENT_ID'],
                                client_secret=app.config['SPOTIPY_CLIENT_SECRET'],
                                redirect_uri=app.config['SPOTIPY_REDIRECT_URI'])
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return Spotify(auth=token_info['access_token'])

def sanitize_lyrics(lyrics):
    return [line.strip() for line in lyrics if line.strip()]

@app.route('/sync')
def sync():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))
    
    current_track = sp.current_playback()
    if not current_track or not current_track['is_playing']:
        return render_template('no-sync.html')
    song_id = current_track['item']['id']
    song_name = current_track['item']['name']
    artists = ', '.join([artist['name'] for artist in current_track['item']['artists']])

    lyrics_response = requests.get(f'https://api.lyrics.ovh/v1/{current_track["item"]["artists"][0]["name"]}/{song_name}')
    if lyrics_response.status_code == 200:
        raw_lyrics = lyrics_response.json().get('lyrics', '').split('\n')
        lyrics = ["\n"] + sanitize_lyrics(raw_lyrics)
    else:
        lyrics = ["Lyrics not found"]

    return render_template('sync.html', song_id=song_id, song_name=song_name, artists=artists, lyrics=lyrics, token=session['token_info']['access_token'])

@app.route('/save_lyrics', methods=['POST'])
def save_lyrics():
    data = request.get_json()
    song_id = data['song_id']
    song_name = data['song_name']
    artists = data['artists']
    lyrics = data['lyrics']

    song_ref = db.collection('songs').document(song_id)
    song_ref.set({
        'name': song_name,
        'artists': artists
    })

    for lyric in lyrics:
        db.collection('songs').document(song_id).collection('lyrics').add({
            'timestamp': lyric['timestamp'],
            'line': lyric['line']
        })

    return jsonify({'status': 'success'})

@app.route('/display/<song_id>')
def display(song_id):
    song_ref = db.collection('songs').document(song_id).get()
    if not song_ref.exists:
        return 'Song not found', 404

    song = song_ref.to_dict()
    lyrics_ref = db.collection('songs').document(song_id).collection('lyrics').order_by('timestamp').stream()
    lyrics = [lyric.to_dict() for lyric in lyrics_ref]

    return render_template('display.html', song_name=song['name'], artists=song['artists'], lyrics=lyrics)

@app.route('/thankyou/<song_name>/<artists>/<song_id>')
def thankyou(song_name, artists, song_id):
    return render_template('thank_you.html', song_name=song_name, artists=artists, song_id=song_id)

if __name__ == '__main__':
    app.run(debug=True)
