import json
import os
from datetime import datetime, UTC

import boto3
import requests

# AWS S3 Client
s3 = boto3.client("s3")

# Environment Variables
API_KEY = os.environ["YOUTUBE_API_KEY"]
BUCKET = os.environ["S3_BUCKET"]


def lambda_handler(event, context):
    """
    Fetch Top 10 Trending YouTube Videos (India)
    and store the raw JSON in the Bronze layer of S3.
    """

    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": "IN",
        "maxResults": 10,
        "key": API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {
            "statusCode": response.status_code,
            "body": response.text
        }

    data = response.json()

    # Create timestamped filename
    filename = (
        "bronze/trending/"
        + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    # Upload raw JSON to S3 Bronze layer
    s3.put_object(
        Bucket=BUCKET,
        Key=filename,
        Body=json.dumps(data),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "message": "Upload Successful",
        "file": filename
    }