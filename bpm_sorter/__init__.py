import json
import os
from typing import Any, TypedDict

import polars as pl
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from bpm_sorter.config import Config


class Playlist(TypedDict):
    id: str
    name: str
    tracks: pl.DataFrame


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
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    source_playlist = fetch_playlist(sp, config["sourcePlaylist"])
    target_playlists = [fetch_playlist(sp, playlist["playlist"]) for playlist in config["targets"]]

    all_targets = pl.concat([playlist["tracks"] for playlist in target_playlists], how="vertical")

    tracks_to_sort = source_playlist["tracks"].join(all_targets, on="id", how="anti")

    print(tracks_to_sort)


def fetch_playlist(sp: spotipy.Spotify, playlist_url: str) -> Playlist:
    print(f"Fetch playlist {playlist_url}")
    playlist: dict = sp.playlist(playlist_url, fields="id,name")

    response: dict = sp.playlist_items(playlist["id"], fields="next,items(track(id,name))")
    raw_tracks: list = response["items"]

    while response.get("next"):
        response: dict = sp.next(response)  # type: ignore
        raw_tracks.extend(response["items"])

    track_df = pl.DataFrame([track["track"] for track in raw_tracks])
    print("track_df", track_df)

    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "tracks": track_df,
    }


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
