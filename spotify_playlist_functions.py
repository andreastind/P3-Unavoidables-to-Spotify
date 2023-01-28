import pandas as pd
from datetime import datetime


def get_playlist_uri(username, playlist_name, sp):
    '''Fetches the URI of a playlist.
    
    Arguments:
        username: Spotify username
        playlist_name: name of playlist to get URI for
        sp: SpotifyOAuth object

    Returns:
        playlist_uri: URI of the playlist
    '''
        
    playlist_uri = ''
    playlists = sp.user_playlists(username)

    # iterate through the playlists that the user follows
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_uri = playlist['uri']
    
    return playlist_uri


def update_playlist(
    user_id, sp, 
    position=0, playlist_name="P3 Ugens Uundgåelige (Auto Update)"
):
    '''Updates a playlist with new tracks from the locally stored scraped data.
    
    Arguments:
        user_id: Spotify username
        sp: SpotifyOAuth object
        position: position in playlist to add new tracks
        playlist_name: name of playlist to update

    Returns:
        None
    '''
    
    # fetching uri of the playlist to fill with tracks
    playlist_uri = get_playlist_uri(user_id, playlist_name, sp)

    # get item information of the first 50 items in the playlist
    playlist_track_data = sp.playlist_items(playlist_uri)
    playlist_track_uris = []
    current_page = playlist_track_data

    # iterate through pages of playlist items to collect all track uris
    while True:
        for item in current_page["items"]:
            playlist_track_uris.append(item["track"]["uri"])
        if current_page["next"]:
            current_page = sp.next(current_page)
        else:
            break
    print(f"Got {len(playlist_track_uris)} track URIs present in playlist.")
    
    # get track uris from scraped data
    scraped_df = pd.read_pickle("data/scraped_dataframe.pkl")
    new_track_uris = scraped_df["uri"].tolist()

    # remove tracks already in playlist
    track_uris_to_add = [track.removeprefix("spotify:track:") 
                        for track in new_track_uris 
                        if (track is not None and track not in playlist_track_uris)]
    
    print(f"Found {len(track_uris_to_add)} track(s) not already in playlist.")

    # if playlist is empty (or just a few tracks), add to bottom of list     
    if len(playlist_track_uris) < 5:
        position = None
    
    batch_size = 100 # max 100 tracks per batch

    # add tracks to playlist in batches
    for i in range(0, len(track_uris_to_add), batch_size):
        sp.user_playlist_add_tracks(user_id, 
                                    playlist_uri, 
                                    track_uris_to_add[i:i+batch_size], 
                                    position=position)
        
        print(f"Added tracks from batch {i+1}-{i+batch_size+1} to playlist.")
    
    sp.user_playlist_change_details(
        user_id, 
        playlist_uri, 
        description="Indeholder alle \"P3's Ugens Uundgåelig\" tracks fra "
        "1991 til i dag. Sidste automatiske opdatering: "
        f"{datetime.now().strftime('%d-%m-%Y, %H:%M:%S')}."
    )
