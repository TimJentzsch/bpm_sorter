from typing import TypedDict

SpotifyUrl = str


class Target(TypedDict):
    playlist: SpotifyUrl
    maxBpm: float | None


class Config(TypedDict):
    sourcePlaylist: SpotifyUrl
    minBpm: float
    maxBpm: float
    targets: list[Target]
