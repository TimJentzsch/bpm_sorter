import json
import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from bpm_sorter.config import Config


def main(client_id: str, client_secret: str, redirect_uri: str, config: Config) -> None:
    # https://developer.spotify.com/documentation/web-api/concepts/scopes
    scope = ",".join(
        [
            "playlist-read-private",
            "playlist-read-collaborative",
            "playlist-modify-private",
            "playlist-modify-public",
        ]
    )
    auth_manager = SpotifyOAuth(
        client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    source_playlist = sp.playlist(config["sourcePlaylist"], fields="tracks(items(track(id,name)))")

    print(source_playlist)

    for track in source_playlist["tracks"]["items"]:
        print(track["track"]["name"])


if __name__ == "__main__":
    load_dotenv()

    env_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    env_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    env_redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    if not env_client_id or not env_client_secret or not env_redirect_uri:
        print(
            "You need to specify SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and SPOTIFY_REDIRECT_URI "
            + "in the .env file"
        )
        exit(1)

    with open("../config.json") as config_file:
        file_config = json.load(config_file)

    main(
        client_id=env_client_id,
        client_secret=env_client_secret,
        redirect_uri=env_redirect_uri,
        config=file_config,
    )
