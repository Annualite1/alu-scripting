# api_advanced

Python scripts that query the Reddit API.

| File | Description |
|------|-------------|
| 0-subs.py | Returns the number of subscribers of a subreddit (0 if invalid) |
| 1-top_ten.py | Prints the titles of the first 10 hot posts (None if invalid) |
| 2-recurse.py | Recursively returns the titles of all hot posts (None if invalid) |
| 3-count.py | Recursively counts keywords in hot post titles and prints them sorted |
| verify_all.py | Offline verifier for all four tasks |

## Requirements

- Python 3 and the `requests` module
- A custom User-Agent is set on every request and redirects are not followed

## Usage

    python3 0-main.py programming
    python3 1-main.py programming
    python3 2-main.py programming
    python3 3-main.py programming 'python java javascript'
