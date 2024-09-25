import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time
import csv
from flask import Flask, request, url_for, session, redirect, render_template
from rapidfuzz import fuzz

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = os.getenv('SECRET_KEY')
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_tiktok_live', external=True))

@app.route('/saveTikTokLive')
def save_tiktok_live(): 
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    current_playlist = sp.current_user_playlists()['items']
    tiktok_live_playlist_id = None

    for playlist in current_playlist:
        if playlist['name'] == "TikTok Live":
            tiktok_live_playlist_id = playlist['id']
    
    if tiktok_live_playlist_id is None:
        return 'TikTok Live playlist not found'
    
    # Read song details from the CSV file and add them to the playlist
    added_songs = []
    with open('song_details.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        existing_tracks = set(item['track']['uri'] for item in sp.playlist_tracks(tiktok_live_playlist_id)['items'])
        
        for row in reader:
            song_name = row['Song Name']
            artist = row['Artist']
            query = song_name  # Search using only the song name
            results = sp.search(q=query, type='track', limit=10)

            best_match = None
            highest_score = 0

            for item in results['tracks']['items']:
                track_name = item['name']
                track_artist = item['artists'][0]['name']

                # Compute similarity scores
                name_score = fuzz.ratio(song_name.lower(), track_name.lower())
                artist_score = fuzz.ratio(artist.lower(), track_artist.lower())
                total_score = (2 * name_score + artist_score) / 3  # Weighted average

                if total_score > highest_score:
                    highest_score = total_score
                    best_match = item

            # Set a threshold for accepting matches
            if highest_score > 70:  # Adjust the threshold as needed
                song_uri = best_match['uri']
                if song_uri not in existing_tracks:
                    sp.user_playlist_add_tracks(user_id, tiktok_live_playlist_id, [song_uri])
                    existing_tracks.add(song_uri)
                    added_songs.append(f"{best_match['name']} by {best_match['artists'][0]['name']}")
            else:
                # Could not find a good match
                print(f"No good match found for {song_name} by {artist}")

    if not added_songs:
        return render_template('result.html', message="No new songs were added to your 'TikTok Live' playlist.")
    
    return render_template('result.html', message="The following songs were added to your 'TikTok Live' playlist:", songs=added_songs)

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=url_for('redirect_page', _external=True),
                        scope='user-library-read playlist-modify-public playlist-modify-private')

app.run(debug=True)
