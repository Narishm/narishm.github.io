
import os
import requests

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "YOUTUBE_API_KEY not found. Restart VS Code "
        "after adding the environment variable."
    )

url = "https://www.googleapis.com/youtube/v3/channels"

params = {
    "part": "snippet,contentDetails,statistics",
    "forHandle": "@narishm",
    "key": API_KEY
}

response = requests.get(url, params=params, timeout=20)
response.raise_for_status()

data = response.json()

if not data.get("items"):
    print("Channel not found.")
else:
    channel = data["items"][0]

    print("SUCCESS! YouTube connection established!")
    print("Channel:", channel["snippet"]["title"])
    print("Channel ID:", channel["id"])
    print("Uploads playlist:",
          channel["contentDetails"]["relatedPlaylists"]["uploads"])
    print("Public video count:",
          channel["statistics"].get("videoCount", "Unknown"))
