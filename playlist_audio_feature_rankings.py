from typing import Dict, List
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred

from constants import audio_feature_names


def get_playlists(sp: spotipy.Spotify, collab_only: bool = False) -> Dict:
    '''Gets playlists by making API call to Spotify.

    Args:
        sp: Instance of Spotify class from spotipy
        collab_only: Whether or not to include only collaborative playlists

    Returns:
        Dictionary with keys as playlist names and values as playlist data
    '''  
    results = sp.current_user_playlists()
    playlists = results['items']
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])
    resulting_playlists = {}
    for item in playlists:
        if item['collaborative'] or not collab_only:
            resulting_playlists[item['name']] = item['id']
    return resulting_playlists


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> List:
    '''Gets data for all tracks in a playlist

    Args:
        sp: Instance of Spotify class from spotipy
        playlist_id: id of playlist to be searched

    Returns:
        List of all track's data in the playlist
    '''
    results = sp.playlist_items(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def get_audio_features(sp: spotipy.Spotify, tracks: List) -> List:
    '''Gets audio features for all the tracks in a playlist

    Args:
        sp: Instance of Spotify class from spotipy
        tracks: List of tracks and their data

    Returns:
        List of audio features for the given tracks
    '''
    track_ids = list(filter(None, [track['track']['id'] for track in tracks]))
    num_tracks_left = len(track_ids)
    start = 0
    audio_features = []
    while num_tracks_left > 0:
        ids = track_ids[start:start+100]
        audio_features.extend(sp.audio_features(tracks=ids))
        num_tracks_left -= 100
        start += 100
    return audio_features


def average_audio_features(audio_features: List) -> Dict:
    '''Provides the averages of the audio features of a given playlist

    Args:
        audio_features: List of a each song in a playlist's audio features

    Returns:
        Dictionary containing the average audio features for the playlist
    '''
    cumulative_audio_features = {
        'danceability': 0,
        'energy': 0,
        'loudness': 0,
        'speechiness': 0,
        'acousticness': 0,
        'instrumentalness': 0,
        'liveness': 0,
        'valence': 0,
        'tempo': 0,
    }
    num_tracks = len(audio_features)
    for audio_feature in audio_features:
        for category in cumulative_audio_features:
            cumulative_audio_features[category] += audio_feature[category]
    return {
        category: round((total/num_tracks), 2) for category, total in cumulative_audio_features.items()
    }


def print_rankings(playlists_audio_features: Dict, top_amount: int = 10):
    '''Prints the top N number of playlists for each audio feature

    Args:
        playlists_audio_features: The audio features for each playlist
        top_amount: denotes the top N number of playlists to print
    '''
    for category in audio_feature_names:
        print(f'-----------\n{category}\n-----------')
        sorted_playlists = sorted(
            playlists_audio_features.items(),
            key=lambda x: (x[1][category]),
            reverse=True
        )
        top_ten = sorted_playlists[:top_amount]
        for playlist in top_ten:
            print(f'{playlist[0]}: {playlist[1][category]}')
        print()


def main():
    scope = "playlist-read-collaborative"
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=cred.client_id,
            client_secret=cred.client_secret,
            redirect_uri=cred.redirect_url,
            scope=scope
        )
    )
    playlists = get_playlists(sp=sp)
    playlist_audio_features = {}
    for playlist in playlists:
        tracks = get_playlist_tracks(sp, playlists[playlist])
        audio_features = get_audio_features(sp, tracks)
        playlist_audio_features[playlist] = average_audio_features(audio_features)
    print_rankings(playlist_audio_features)


if __name__ == "__main__":
    main()
