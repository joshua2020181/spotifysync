from spotipy.oauth2 import SpotifyOAuth
import spotipy

CLIENTID = 'db44ed541fca41c59ff7059f084e3cd4'
CLIENTSECRET = 'b49f57ee339a4c649a4d06c0d0f79abe'
REDIRECT = 'http://127.0.0.1:8000/account/link'


scope = "streaming user-read-playback-state user-modify-playback-state user-read-currently-playing"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENTID, client_secret=CLIENTSECRET, redirect_uri=REDIRECT, scope=scope))

print(sp.current_playback())

print('-'*100)
print(sp.auth_manager.get_access_token(as_dict=True))

while True:
    userin = input('pause, play, skip\n')
    if userin == 'pause':
        sp.pause_playback()
    elif userin == 'play':
        sp.start_playback()
    elif userin == 'skip':
        sp.next_track()


results = sp.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])
