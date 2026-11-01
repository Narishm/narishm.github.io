"""Split youtube_history.json into calendar-year archives without changing the original.

Run from any directory: py split_youtube_history.py
Optional: py split_youtube_history.py "path/to/youtube_history.json"
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def parse_utc_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return None
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def split(source: Path):
    with source.open('r', encoding='utf-8-sig') as handle:
        archive = json.load(handle)
    if not isinstance(archive, dict) or not isinstance(archive.get('videos'), list):
        raise ValueError('Expected an exporter archive with a top-level "videos" list.')

    videos = archive['videos']
    groups = defaultdict(list)
    seen = set()
    for index, video in enumerate(videos, start=1):
        if not isinstance(video, dict):
            raise ValueError(f'Video #{index} is not an object.')
        vid = video.get('videoId')
        if not isinstance(vid, str) or not vid:
            raise ValueError(f'Video #{index} has no videoId.')
        if vid in seen:
            raise ValueError(f'Duplicate videoId in original archive: {vid}. Refusing to split.')
        seen.add(vid)
        start = parse_utc_date(video.get('actualStartTime'))
        published = parse_utc_date(video.get('publishedAt'))
        chosen = start or published
        if chosen is None:
            raise ValueError(f'No valid actualStartTime or publishedAt for {vid}. Refusing to lose it.')
        groups[chosen.year].append(video)

    target_dir = source.parent / 'yearly'
    target_dir.mkdir(exist_ok=True)
    # Write only once all source validation is complete.
    for year in sorted(groups):
        result = {
            'channel': archive.get('channel'),
            'channelId': archive.get('channelId'),
            'exportedAt': archive.get('exportedAt'),
            'splitYear': year,
            'yearRule': 'actualStartTime UTC, otherwise publishedAt UTC',
            'count': len(groups[year]),
            'videos': groups[year],
        }
        output = target_dir / f'youtube_{year}.json'
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'{year}: {len(groups[year]):4} videos -> {output}')

    # Check the generated archives against the source IDs, not just counts.
    ids = []
    for year in groups:
        output = target_dir / f'youtube_{year}.json'
        with output.open('r', encoding='utf-8') as handle:
            part = json.load(handle)
        ids.extend(v['videoId'] for v in part['videos'])
    if len(ids) != len(videos) or set(ids) != seen:
        raise RuntimeError('Verification failed: missing or duplicated videos!')
    print(f'\nVERIFIED: {len(ids)} videos, {len(groups)} year files, no missing or duplicate IDs.')
    print(f'Original archive unchanged: {source}')
    print('Note: years are based on UTC; a livestream near midnight may fall on the prior local date.')
    print('Only upload the yearly JSON files you want available in GitHub.')


if __name__ == '__main__':
    location = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('youtube_history.json')
    try:
        split(location.expanduser().resolve())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        sys.exit(f'ERROR: {exc}')
