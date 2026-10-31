#!/usr/bin/python3
"""Prints the titles of the first 10 hot posts of a subreddit."""
import requests


def top_ten(subreddit):
    """Print the first 10 hot post titles, or None if invalid."""
    if not subreddit or not isinstance(subreddit, str):
        print(None)
        return
    url = "https://www.reddit.com/r/{}/hot.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    params = {"limit": 10}
    try:
        response = requests.get(url, headers=headers, params=params,
                                allow_redirects=False, timeout=10)
        if response.status_code != 200:
            print(None)
            return
        children = response.json().get("data", {}).get("children", [])
    except (requests.RequestException, ValueError, AttributeError):
        print(None)
        return
    for child in children[:10]:
        print(child.get("data", {}).get("title"))
