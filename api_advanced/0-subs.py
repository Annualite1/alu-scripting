#!/usr/bin/python3
"""Queries the Reddit API and returns the number of subscribers."""
import requests


def number_of_subscribers(subreddit):
    """Return the total subscribers of a subreddit, or 0 if invalid."""
    if not subreddit or not isinstance(subreddit, str):
        return 0
    url = "https://www.reddit.com/r/{}/about.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    try:
        response = requests.get(url, headers=headers,
                                allow_redirects=False, timeout=10)
        if response.status_code != 200:
            return 0
        return response.json().get("data", {}).get("subscribers", 0)
    except (requests.RequestException, ValueError, AttributeError):
        return 0
