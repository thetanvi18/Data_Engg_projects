from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")


URL = "https://www.googleapis.com/youtube/v3/videos"

params = {
    "part": "snippet,statistics",
    "chart": "mostPopular",
    "regionCode": "IN",
    "maxResults": 10,
    "key": API_KEY
}

response = requests.get(URL, params=params)

print("Status Code:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

print("\nTop 10 Trending Videos in India\n")

for i, item in enumerate(data["items"], start=1):
    print(f"{i}. {item['snippet']['title']}")
    print(f"   Channel : {item['snippet']['channelTitle']}")
    print(f"   Views   : {item['statistics'].get('viewCount', 'N/A')}")
    print("-" * 70)