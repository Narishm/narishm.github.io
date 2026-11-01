import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API_KEY = os.environ.get('YOUTUBE_API_KEY')
CHANNEL_HANDLE = '@narishm'
BASE = 'https://www.googleapis.com/youtube/v3/'
OUTPUT = Path(__file__).with_name('youtube_history.json')


def api_get(endpoint, **params):
    response = requests.get(
        BASE + endpoint,
        params={'key': API_KEY, **params},
        timeout=30,
    )
    if not response.ok:
        try:
            message = response.json()['error']['message']
        except (ValueError, KeyError, TypeError):
            message = f'HTTP {response.status_code}'
        raise RuntimeError(f'YouTube API error: {message}')
    return response.json()


def batches(items, count=50):
    for i in range(0, len(items), count):
        yield items[i:i + count]


def main():
    if not API_KEY:
        sys.exit('Missing YOUTUBE_API_KEY. Restart VS Code after setting it.')

    channel_data = api_get('channels', part='snippet,contentDetails', forHandle=CHANNEL_HANDLE)
    if not channel_data.get('items'):
        sys.exit('Channel not found. Check CHANNEL_HANDLE.')

    channel = channel_data['items'][0]
    playlist = channel['contentDetails']['relatedPlaylists']['uploads']
    print(f"Channel: {channel['snippet']['title']}")
    print('Collecting upload IDs...')

    video_ids = []
    token = None
    while True:
        params = {'part': 'contentDetails', 'playlistId': playlist, 'maxResults': 50}
        if token:
            params['pageToken'] = token
        page = api_get('playlistItems', **params)
        video_ids.extend(
            item['contentDetails']['videoId']
            for item in page.get('items', [])
            if item.get('contentDetails', {}).get('videoId')
        )
        print(f'Found {len(video_ids)} upload entries...', flush=True)
        token = page.get('nextPageToken')
        if not token:
            break

    # Preserve order, avoiding duplicate video IDs.
    video_ids = list(dict.fromkeys(video_ids))
    videos = []
    print('Retrieving video metadata...')
    for group in batches(video_ids):
        data = api_get(
            'videos',
            part='snippet,contentDetails,liveStreamingDetails,status',
            id=','.join(group),
            maxResults=50,
        )
        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            detail = item.get('contentDetails', {})
            live = item.get('liveStreamingDetails', {})
            status = item.get('status', {})
            vid = item['id']
            videos.append({
                'videoId': vid,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'publishedAt': snippet.get('publishedAt'),
                'actualStartTime': live.get('actualStartTime'),
                'actualEndTime': live.get('actualEndTime'),
                'scheduledStartTime': live.get('scheduledStartTime'),
                'duration': detail.get('duration'),
                'liveBroadcastContent': snippet.get('liveBroadcastContent'),
                'privacyStatus': status.get('privacyStatus'),
                'url': f'https://www.youtube.com/watch?v={vid}',
            })
        print(f'Retrieved {len(videos)} video records...', flush=True)

    # Oldest first; retain YouTube's original UTC timestamps.
    videos.sort(key=lambda x: x.get('actualStartTime') or x.get('publishedAt') or '')
    archive = {
        'channel': channel['snippet']['title'],
        'channelId': channel['id'],
        'exportedAt': datetime.now(timezone.utc).isoformat(),
        'count': len(videos),
        'uploadEntries': len(video_ids),
        'videos': videos,
    }
    OUTPUT.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nSUCCESS! Exported {len(videos)} videos to {OUTPUT}')
    if len(videos) != len(video_ids):
        print(f'Note: {len(video_ids) - len(videos)} uploads were not returned by the public video lookup.')
    if videos:
        print('Oldest available:', videos[0]['title'], videos[0]['actualStartTime'] or videos[0]['publishedAt'])
        print('Newest available:', videos[-1]['title'], videos[-1]['actualStartTime'] or videos[-1]['publishedAt'])


if __name__ == '__main__':
    try:
        main()
    except (requests.RequestException, RuntimeError) as exc:
        sys.exit(str(exc))
