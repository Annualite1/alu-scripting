#!/usr/bin/python3
"""Recursively collects the titles of all hot articles of a subreddit."""
import requests

REDIRECTS = (301, 302, 303, 307, 308, 404)


def recurse(subreddit, hot_list=[], after=None):
    """Return a list of all hot article titles, or None if no results."""
    if not subreddit or not isinstance(subreddit, str):
        return None
    url = "https://www.reddit.com/r/{}/hot.json?limit=100".format(subreddit)
    if after:
        url += "&after={}".format(after)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    try:
        response = requests.get(url, headers=headers, allow_redirects=False)
        if getattr(response, "status_code", 200) in REDIRECTS:
            return hot_list or None
        data = response.json()["data"]
        titles = [child["data"]["title"] for child in data["children"]]
        after = data.get("after")
    except Exception:
        return hot_list or None
    hot_list = hot_list + titles
    if after:
        return recurse(subreddit, hot_list, after)
    return hot_list or None
