import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time
import csv
from flask import Flask, request, url_for, session, redirect, render_template
from rapidfuzz import fuzz

# Load environment variables from a .env file
load_dotenv()

# Retrieve Spotify client credentials from environment variables
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

# Initialize a Flask application
app = Flask(__name__)

# Set up session and security configurations for Flask
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = os.getenv('SECRET_KEY')
TOKEN_INFO = 'token_info'

#Homepage
@app.route('/')
def login():
    """
    Redirects the user to the Spotify login page for authentication.
    """
    # Generate Spotify authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()  
    return redirect(auth_url)

#Spotify redirect URI after authentication
@app.route('/redirect')
def redirect_page():
    """
    Handles the redirect from Spotify's authentication flow.
    Exchanges the authorization code for an access token.
    """
    session.clear()  # Clear any existing session data
    code = request.args.get('code')  # Retrieve authorization code from query parameters
    token_info = create_spotify_oauth().get_access_token(code)  # Exchange code for access token
    session[TOKEN_INFO] = token_info  # Store token in session
    return redirect(url_for('save_tiktok_live', external=True))  # Redirect to TikTok Live playlist route

#Save TikTok Live songs to Spotify playlist
@app.route('/saveTikTokLive')
def save_tiktok_live():
    """
    Reads song details from a CSV file and adds them to a Spotify playlist named 'TikTok Live'.
    """
    
    # Retrieve Spotify access token
    try:
        token_info = get_token()  
    except:
        # Redirect to login if no valid token
        print("User not logged in")  
        return redirect('/')  
    
    # Create Spotify client with access token
    sp = spotipy.Spotify(auth=token_info['access_token']) 
    user_id = sp.current_user()['id']  

    # Check if a playlist named "TikTok Live" already exists
    current_playlist = sp.current_user_playlists()['items']
    tiktok_live_playlist_id = None
    
    for playlist in current_playlist:
        # Save the playlist ID if found
        if playlist['name'] == "TikTok Live":
            tiktok_live_playlist_id = playlist['id']  

    # Return error if playlist doesn't exist
    if tiktok_live_playlist_id is None:
        return 'TikTok Live playlist not found'  

    # Read song details from the CSV file
    added_songs = []
    with open('song_details.csv', 'r', newline='', encoding='utf-8') as csvfile:
        
        reader = csv.DictReader(csvfile)  
        
        # Fetch existing playlist tracks
        existing_tracks = set(item['track']['uri'] for item in sp.playlist_tracks(tiktok_live_playlist_id)['items'])  
        
        for row in reader:
            song_name = row['Song Name']  # Extract song name
            artist = row['Artist']  # Extract artist name
            query = song_name  # Use song name for Spotify search
            results = sp.search(q=query, type='track', limit=10)  # Search for tracks

            # Find the best match for the song using fuzzy matching
            best_match = None
            highest_score = 0
            for item in results['tracks']['items']:
                track_name = item['name']
                track_artist = item['artists'][0]['name']

                # Compute similarity scores using fuzz
                name_score = fuzz.ratio(song_name.lower(), track_name.lower())
                artist_score = fuzz.ratio(artist.lower(), track_artist.lower())
                total_score = (2 * name_score + artist_score) / 3
                
                
                # Update the best match if the score is higher
                if total_score > highest_score:  
                    highest_score = total_score
                    best_match = item

            # Add the best match to the playlist if it meets the threshold
            if highest_score > 70:
                song_uri = best_match['uri']
                
                # Avoid adding duplicate tracks
                if song_uri not in existing_tracks:  
                    sp.user_playlist_add_tracks(user_id, tiktok_live_playlist_id, [song_uri])
                    existing_tracks.add(song_uri)  
                    added_songs.append(f"{best_match['name']} by {best_match['artists'][0]['name']}") 
                     
            else:
                # Log if no good match is found
                print(f"No good match found for {song_name} by {artist}")

    # Display a message if no songs were added
    if not added_songs:
        return render_template('result.html', message="No new songs were added to your 'TikTok Live' playlist.")
    
    # Render the result template with added songs
    return render_template('result.html', message="The following songs were added to your 'TikTok Live' playlist:", songs=added_songs)

# Retrieve and refresh Spotify token if needed
def get_token():
    """
    Retrieves and refreshes the Spotify access token if expired.
    """
    token_info = session.get(TOKEN_INFO, None)
    # Redirect to login if no token found
    if not token_info:  
        redirect(url_for('login', external=False))

    now = int(time.time())
    # Check if token is close to expiration
    is_expired = token_info['expires_at'] - now < 60  
    
    # Refresh token if expired
    if is_expired:  
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
        
    # Return updated token
    return token_info  

# create spotifyoauth client
def create_spotify_oauth():
    """
    Configures SpotifyOAuth with client credentials and scopes.
    """
    return SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=url_for('redirect_page', _external=True),
                        scope='user-library-read playlist-modify-public playlist-modify-private')

app.run(debug=True)