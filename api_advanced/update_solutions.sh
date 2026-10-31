#!/bin/bash
# Run inside alu-scripting/api_advanced: rewrites the 4 solution files, then runs the verifier
set -e
cat > 0-subs.py << 'EOF_0-subs.py'
#!/usr/bin/python3
"""Queries the Reddit API and returns the number of subscribers."""
import requests

REDIRECTS = (301, 302, 303, 307, 308, 404)


def number_of_subscribers(subreddit):
    """Return the total subscribers of a subreddit, or 0 if invalid."""
    if not subreddit or not isinstance(subreddit, str):
        return 0
    url = "https://www.reddit.com/r/{}/about.json".format(subreddit)
    headers = {"User-Agent": "linux:alu-scripting:v1.0.0 (by /u/alu_student)"}
    try:
        response = requests.get(url, headers=headers, allow_redirects=False)
        if getattr(response, "status_code", 200) in REDIRECTS:
            return 0
        return response.json()["data"]["subscribers"] or 0
    except Exception:
        return 0
EOF_0-subs.py
cat > 1-top_ten.py << 'EOF_1-top_ten.py'
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
EOF_1-top_ten.py
cat > 2-recurse.py << 'EOF_2-recurse.py'
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
EOF_2-recurse.py
cat > 3-count.py << 'EOF_3-count.py'
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
EOF_3-count.py
chmod +x *.py
python3 verify_all.py | tail -3
