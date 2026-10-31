#!/usr/bin/python3
"""Recursively counts keywords in the titles of hot articles."""
import requests


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
    url = "https://www.reddit.com/r/{}/hot.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    params = {"limit": 100}
    if after:
        params["after"] = after
    try:
        response = requests.get(url, headers=headers, params=params,
                                allow_redirects=False, timeout=10)
        if response.status_code != 200:
            return _print_results(word_list, counts)
        data = response.json().get("data", {})
    except (requests.RequestException, ValueError, AttributeError):
        return _print_results(word_list, counts)
    titles = [(c.get("data", {}).get("title") or "").lower().split()
              for c in data.get("children", [])]
    unique = set(w.lower() for w in word_list)
    counts = {w: counts.get(w, 0) + sum(t.count(w) for t in titles)
              for w in unique}
    after = data.get("after")
    if after:
        return count_words(subreddit, word_list, after, counts)
    return _print_results(word_list, counts)
