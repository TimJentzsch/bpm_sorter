import json
import os
from time import sleep
from typing import TypedDict

import polars as pl
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from bpm_sorter.config import Config


class Playlist(TypedDict):
    id: str
    name: str
    tracks: pl.DataFrame
    min_bpm: float | None
    max_bpm: float | None


def main() -> None:
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

    with open("config.json") as config_file:
        file_config = json.load(config_file)

    sorter(
        client_id=env_client_id,
        client_secret=env_client_secret,
        redirect_uri=env_redirect_uri,
        config=file_config,
    )


def sorter(client_id: str, client_secret: str, redirect_uri: str, config: Config) -> None:
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

    source_playlist = fetch_playlist(
        sp, config["sourcePlaylist"], min_bpm=config["minBpm"], max_bpm=config["maxBpm"]
    )
    target_playlists = [
        fetch_playlist(sp, playlist["playlist"], max_bpm=playlist.get("maxBpm"))
        for playlist in config["targets"]
    ]

    all_targets = pl.concat([playlist["tracks"] for playlist in target_playlists], how="vertical")

    tracks_to_sort = source_playlist["tracks"].join(all_targets, on="id", how="anti")
    print(tracks_to_sort)

    tracks_with_audio_features = add_audio_features(sp, tracks_to_sort)
    print(tracks_with_audio_features)

    normalized_audio_features = normalize_tempo(tracks_with_audio_features, config)
    print(normalized_audio_features)

    sorted_tracks = sort_tracks(normalized_audio_features, target_playlists)
    print(sorted_tracks)

    print(f"\n\nSorting {tracks_to_sort.count()} tracks:\n")

    for playlist in target_playlists:
        new_tracks = sorted_tracks.filter(pl.col("playlist") == playlist["id"])
        print(f"{playlist['name']}:", new_tracks)

    confirm_input = ""

    while True:
        confirm_input = input("Continue [y/N]?").lower()
        if confirm_input == "y":
            break
        elif confirm_input == "n":
            exit(1)

    for playlist in target_playlists:
        new_tracks = sorted_tracks.filter(pl.col("playlist") == playlist["id"])
        add_tracks_to_playlist(sp, new_tracks, playlist)

    print("Completed successfully!")


def add_tracks_to_playlist(sp: spotipy.Spotify, tracks: pl.DataFrame, playlist: Playlist) -> None:
    """Add all the tracks in the dataframe to the given playlist."""
    # Only 100 tracks can be added at a time
    for slice in tracks.iter_slices(100):
        sp.playlist_add_items(playlist["id"], slice.get_column("id"))
        sleep(0.5)


def sort_tracks(tracks: pl.DataFrame, target_playlists: list[Playlist]) -> pl.DataFrame:
    """Sort the tracks into the target playlists depending on their BPM."""
    # For easier chaining we start with an expressions that's never true
    sort_query: pl.When = pl.when(False).then(pl.lit(""))

    # ASSUMPTION: Only the last target playlist has no max BPM and they are sorted by BPM
    for playlist in target_playlists:
        max_bpm = playlist.get("max_bpm")
        if max_bpm is not None:
            sort_query = sort_query.when(pl.col("tempo") < max_bpm).then(pl.lit(playlist["id"]))
        else:
            sort_query = sort_query.otherwise(pl.lit(playlist["id"]))
            break

    return tracks.select("id", "name", "tempo", sort_query.alias("playlist"))


def add_audio_features(sp: spotipy.Spotify, tracks: pl.DataFrame) -> pl.DataFrame:
    """Add audio features like the tempo to the tracks."""
    audio_features_raw = []

    # Audio features can be fetched for max 100 tracks
    for slice in tracks.iter_slices(100):
        response = sp.audio_features(slice.get_column("id"))
        audio_features_raw.extend(response)

        sleep(0.5)

    audio_features = pl.DataFrame(audio_features_raw).select(pl.col(["id", "tempo"]))

    return audio_features.join(tracks, on="id", how="right")


def normalize_tempo(tracks: pl.DataFrame, config: Config) -> pl.DataFrame:
    """Normalize the tempo of the tracks based on the config.

    Sometimes, the tempo detected by spotify is half or double the actual tempo.
    Based on the min and max BPM of the config, these errors can be corrected automatically.
    """
    return tracks.select(
        "id",
        "name",
        pl.when(pl.col("tempo") < config["minBpm"])
        .then(pl.col("tempo") * 2)
        .when(pl.col("tempo") > config["maxBpm"])
        .then(pl.col("tempo") / 2)
        .otherwise(pl.col("tempo")),
    )


def fetch_playlist(
    sp: spotipy.Spotify,
    playlist_url: str,
    min_bpm: float | None = None,
    max_bpm: float | None = None,
) -> Playlist:
    print(f"Fetch playlist {playlist_url}")
    playlist: dict = sp.playlist(playlist_url, fields="id,name")

    response: dict = sp.playlist_items(playlist["id"], fields="next,items(track(id,name))")
    raw_tracks: list = response["items"]

    while response.get("next"):
        response: dict = sp.next(response)  # type: ignore
        raw_tracks.extend(response["items"])

        sleep(0.5)

    track_df = pl.DataFrame([track["track"] for track in raw_tracks])
    print("track_df", track_df)

    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "min_bpm": min_bpm,
        "max_bpm": max_bpm,
        "tracks": track_df,
    }


if __name__ == "__main__":
    main()
