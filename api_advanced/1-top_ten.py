#!/usr/bin/python3
"""Prints the titles of the first 10 hot posts of a subreddit."""
import requests

REDIRECTS = (301, 302, 303, 307, 308, 404)


def top_ten(subreddit):
    """Print the first 10 hot post titles, or None if invalid."""
    if not subreddit or not isinstance(subreddit, str):
        print(None)
        return
    url = "https://www.reddit.com/r/{}/hot.json?limit=10".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    try:
        response = requests.get(url, headers=headers, allow_redirects=False)
        if getattr(response, "status_code", 200) in REDIRECTS:
            print(None)
            return
        children = response.json()["data"]["children"]
        titles = [child["data"]["title"] for child in children[:10]]
    except Exception:
        print(None)
        return
    if not titles:
        print(None)
        return
    for title in titles:
        print(title)
