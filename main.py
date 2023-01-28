import os
import logging
import spotipy
import keyring
from spotipy.oauth2 import SpotifyOAuth
from scraper import get_soup, scrape_cleaning
from spotify_playlist_functions import update_playlist
from data_maintainer import update_track_df

logging.basicConfig(
    filename='p3_to_spotify_log.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #datefmt='%m/%d/%Y %I:%M:%S %p',
    encoding='utf-8',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)
logger.info("Current working directory is: %s", os.getcwd())


# setup Spotify API
USER_ID = "toreha54"
SCOPE = "user-library-read, playlist-modify-public, playlist-modify-private"
CLIENT_ID = keyring.get_password('Spotify_CLIENT_ID', "andreastind")
CLIENT_SECRET = keyring.get_password('Spotify_CLIENT_SECRET', "andreastind")


# redirect uri must match some url selected in the Spotify developer dashboard
# since we are using a local server, we can use a dummy url
REDIRECT_URI = "http://example.com"

auth_manager = SpotifyOAuth(client_id = CLIENT_ID, 
                            client_secret = CLIENT_SECRET,
                            redirect_uri = REDIRECT_URI,
                            scope = SCOPE,
                            cache_path = "cache.txt")

sp = spotipy.Spotify(auth_manager=auth_manager)

# scrape tracklist data
soup = get_soup(stored_soup=False, decade=2020)
weekly = scrape_cleaning(soup)

# update tracklist dataframe
scraped_data = update_track_df(weekly, sp)

# update Spotify playlist with new tracks from tracklist dataframe
update_playlist(USER_ID, sp, position=0, playlist_name="P3 til Spotify (auto)")
