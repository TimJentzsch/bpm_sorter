# BPM Sorter

Sort Spotify playlists by their BPM.

## Usage

### Setup Spotify App

First, you need to create a Spotify Developer app to be able to access the Spotify API.
Navigate to the [**Spotify Developer Dashboard**](https://developer.spotify.com/dashboard), log in and create a new app.

Choose a name and description for your app and set the **redirect URI** to `http://localhost:3333`.
Select "Web API" for the API you plan to use.

Once you have created your app, you will be able to access the **client ID** and **client secret**.
You will need them soon.

### Configuring the Tool

But first, clone the repository in a folder of your choice, via HTTPS or SSH.
For example, using HTTPS:

```cli
git clone https://github.com/TimJentzsch/bpm_sorter.git
```

Then navigate into the `bpm_sorter` directory (the _repository root_).

Next create a `.env` file inside the repository root, where you configure the client ID, secret and redirect URI as above:

```env
SPOTIFY_CLIENT_ID="<client_id>"
SPOTIFY_CLIENT_SECRET="<client_secret>"
SPOTIFY_REDIRECT_URI="http://localhost:3333"
```

Don't forget to replace the values with the ones from your app.

Next, you need to configure the playlists for the sorter in a `config.json` file, also in the repository root:

```json
{
  "sourcePlaylist": "<playlist_url>",
  "minBpm": 65,
  "maxBpm": 135,
  "targets": [{
      "playlist": "<playlist_url>",
      "maxBpm": 90
    },
    {
      "playlist": "<playlist_url>",
      "maxBpm": 105
    },
    {
      "playlist": "<playlist_url>"
    }
  ]
}
```

You can get the playlist URLs on Spotify by clicking "share" and "copy URL".

The first `minBpm` and `maxBpm` configure the BPM range that is reasonable for your songs.
Somtimes, Spotify detects half or double of the actual BPM and these values are used to fix these errors.

The targets are the playlists where the songs will be sorted.
The tool expects them to be ascending by their BPM values.
The last playlist can omit the `maxBpm` field, all remaining songs will be put here.

### Running the Tool

You will need Python 3.12 and the [Poetry package manager](https://python-poetry.org/) to run the tool.

First install the dependencies via `poetry install`.
Then, you can run the tool via `poetry run main`.

## License

This project is available under the GPL-3.0 license.

### Your contributions

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in the work by you, shall be licensed as above, without any additional terms or conditions.
