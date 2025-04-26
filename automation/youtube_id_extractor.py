import re
import requests

# Function to extract video IDs from a YouTube playlist URL
def extract_video_ids_from_playlist(playlist_url):
    response = requests.get(playlist_url)
    if response.status_code != 200:
        print(f"Failed to fetch playlist page: {response.status_code}")
        return []
    html = response.text
    # Regex to find all video IDs in the playlist
    video_ids = re.findall(r"watch\?v=([\w-]{11})", html)
    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for vid in video_ids:
        if vid not in seen:
            seen.add(vid)
            unique_ids.append(vid)
    return unique_ids

if __name__ == "__main__":
    playlist_url = input("Enter YouTube playlist URL: ")
    ids = extract_video_ids_from_playlist(playlist_url)
    print(f"Found {len(ids)} video IDs:")
    for vid in ids:
        print(vid)