#!/usr/bin/python3
"""Recursively collects the titles of all hot articles of a subreddit."""
import requests


def recurse(subreddit, hot_list=[], after=None):
    """Return a list of all hot article titles, or None if no results."""
    if not subreddit or not isinstance(subreddit, str):
        return None
    url = "https://www.reddit.com/r/{}/hot.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    params = {"limit": 100}
    if after:
        params["after"] = after
    try:
        response = requests.get(url, headers=headers, params=params,
                                allow_redirects=False, timeout=10)
        if response.status_code != 200:
            return hot_list or None
        data = response.json().get("data", {})
    except (requests.RequestException, ValueError, AttributeError):
        return hot_list or None
    titles = [c.get("data", {}).get("title") for c in data.get("children", [])]
    hot_list = hot_list + titles
    after = data.get("after")
    if after:
        return recurse(subreddit, hot_list, after)
    return hot_list or None
