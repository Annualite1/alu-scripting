#!/usr/bin/python3
"""Recursively counts keywords in the titles of hot articles."""
import requests

REDIRECTS = (301, 302, 303, 307, 308, 404)


def _print_results(word_list, counts):
    """Print sorted keyword totals (duplicates in word_list are summed)."""
    multiplier = {}
    for word in word_list:
        key = word.lower()
        multiplier[key] = multiplier.get(key, 0) + 1
    totals = {w: n * multiplier[w] for w, n in counts.items() if n > 0}
    for word, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])):
        print("{}: {}".format(word, total))


def count_words(subreddit, word_list, after=None, counts=None):
    """Print a sorted count of keywords found in hot article titles."""
    if counts is None:
        counts = {}
    if not subreddit or not isinstance(subreddit, str) or not word_list:
        return
    url = "https://www.reddit.com/r/{}/hot.json?limit=100".format(subreddit)
    if after:
        url += "&after={}".format(after)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    try:
        response = requests.get(url, headers=headers, allow_redirects=False)
        if getattr(response, "status_code", 200) in REDIRECTS:
            return _print_results(word_list, counts)
        data = response.json()["data"]
        titles = [(child["data"]["title"] or "").lower().split()
                  for child in data["children"]]
        next_after = data.get("after")
    except Exception:
        return _print_results(word_list, counts)
    unique = set(w.lower() for w in word_list)
    counts = {w: counts.get(w, 0) + sum(t.count(w) for t in titles)
              for w in unique}
    if next_after:
        return count_words(subreddit, word_list, next_after, counts)
    return _print_results(word_list, counts)
