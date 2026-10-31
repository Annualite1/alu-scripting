#!/usr/bin/python3
"""
verify_all.py - one script that verifies all four api_advanced tasks.

Usage:
    python3 verify_all.py          # offline, mocked Reddit API (deterministic)
    python3 verify_all.py --live   # also try the real Reddit API (needs network)
"""
import ast
import contextlib
import importlib
import io
import os
import runpy
import sys
from unittest import mock
from urllib.parse import parse_qs, urlparse

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PASSED = []
FAILED = []


def check(name, condition, detail=""):
    """Record a single check."""
    if condition:
        PASSED.append(name)
        print("  [PASS] {}".format(name))
    else:
        FAILED.append(name)
        print("  [FAIL] {} {}".format(name, detail))


# --------------------------------------------------------------------------
# Fake Reddit API
# --------------------------------------------------------------------------
class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


TITLES = (
    ["Java is great", "java java java", "python rocks", "Python and Java",
     "javascript vs java", "java. is not counted", "java! neither", "java_x",
     "scala time", "React and python"]
    + ["filler title {}".format(i) for i in range(240)]
)
PAGE_SIZE = 100
CALLS = []


def fake_get(url, headers=None, params=None, allow_redirects=True,
             timeout=None, **kwargs):
    """Fake requests.get that serves 'programming' and rejects the rest."""
    CALLS.append({"url": url, "headers": headers or {}, "params": params or {},
                  "allow_redirects": allow_redirects})
    parsed = urlparse(url)
    query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    query.update(params or {})
    parts = parsed.path.strip("/").split("/")  # r/<name>/<hot|about>.json
    name = parts[1] if len(parts) > 1 else ""
    kind = parts[2] if len(parts) > 2 else ""
    if name == "boom":
        raise requests.ConnectionError("network down")
    if name != "programming":
        # invalid subreddits redirect to search results
        return FakeResponse(302, {})
    if kind == "about.json":
        return FakeResponse(200, {"data": {"subscribers": 756024,
                                           "active_user_count": 12}})
    limit = int(query.get("limit", 25))
    start = int(query.get("after", "t3_0")[3:])
    page = min(limit, PAGE_SIZE)
    chunk = TITLES[start:start + page]
    nxt = start + page
    after = "t3_{}".format(nxt) if nxt < len(TITLES) and limit > 10 else None
    return FakeResponse(200, {"data": {
        "after": after,
        "children": [{"data": {"title": t}} for t in chunk]}})


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def load(module_name):
    """Import a module whose name starts with a digit."""
    return importlib.import_module(module_name)


def capture(func, *args):
    """Run func and return what it printed."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        func(*args)
    return buf.getvalue()


def run_main(script, argv):
    """Run a *-main.py file in-process and return its stdout."""
    buf = io.StringIO()
    old = sys.argv
    sys.argv = [script] + argv
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(os.path.join(HERE, script), run_name="__main__")
    finally:
        sys.argv = old
    return buf.getvalue()


def get_function(path, func_name):
    """Return the AST node of a function in a file."""
    with open(os.path.join(HERE, path)) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return node
    return None


def is_recursive_no_loops(path, func_name):
    """True if function calls itself and has no for/while loop."""
    node = get_function(path, func_name)
    if node is None:
        return False, False
    calls_self = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == func_name for n in ast.walk(node))
    has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node))
    return calls_self, has_loop


def check_headers(prefix):
    """All fake requests made so far must be safe (UA, no redirects)."""
    ok_ua = all(c["headers"].get("User-Agent") for c in CALLS)
    ok_redirect = all(c["allow_redirects"] is False for c in CALLS)
    check("{}: sets custom User-Agent".format(prefix), ok_ua)
    check("{}: allow_redirects=False".format(prefix), ok_redirect)


# --------------------------------------------------------------------------
# Verifications
# --------------------------------------------------------------------------
def verify_files():
    print("\n== Files & style ==")
    for fname in ["0-subs.py", "0-main.py", "1-top_ten.py", "1-main.py",
                  "2-recurse.py", "2-main.py", "3-count.py", "3-main.py"]:
        path = os.path.join(HERE, fname)
        exists = os.path.isfile(path)
        check("{} exists".format(fname), exists)
        if not exists:
            continue
        with open(path) as f:
            first = f.readline().strip()
        check("{} shebang".format(fname), first == "#!/usr/bin/python3")
        check("{} executable".format(fname), os.access(path, os.X_OK))
    for fname in ["0-subs.py", "1-top_ten.py", "2-recurse.py", "3-count.py"]:
        with open(os.path.join(HERE, fname)) as f:
            tree = ast.parse(f.read())
        check("{} module docstring".format(fname),
              ast.get_docstring(tree) is not None)
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        check("{} function docstrings".format(fname),
              all(ast.get_docstring(fn) for fn in funcs))
        with open(os.path.join(HERE, fname)) as f:
            long_lines = [i for i, line in enumerate(f, 1)
                          if len(line.rstrip("\n")) > 79]
        check("{} lines <= 79 chars".format(fname), not long_lines,
              str(long_lines))


def verify_task0():
    print("\n== Task 0: How many subs? ==")
    mod = load("0-subs")
    del CALLS[:]
    check("valid subreddit -> 756024",
          mod.number_of_subscribers("programming") == 756024)
    check("invalid subreddit (redirect) -> 0",
          mod.number_of_subscribers("this_is_a_fake_subreddit") == 0)
    check("network error -> 0", mod.number_of_subscribers("boom") == 0)
    check("empty / None -> 0",
          mod.number_of_subscribers("") == 0
          and mod.number_of_subscribers(None) == 0)
    check_headers("task 0")
    check("0-main valid output",
          run_main("0-main.py", ["programming"]).strip() == "756024")
    check("0-main invalid output",
          run_main("0-main.py", ["this_is_a_fake_subreddit"]).strip() == "0")


def verify_task1():
    print("\n== Task 1: Top Ten ==")
    mod = load("1-top_ten")
    del CALLS[:]
    out = capture(mod.top_ten, "programming").splitlines()
    check("prints exactly 10 titles", len(out) == 10, str(len(out)))
    check("titles are the first 10 hot posts", out == TITLES[:10])
    check("invalid subreddit prints None",
          capture(mod.top_ten, "this_is_a_fake_subreddit").strip() == "None")
    check("network error prints None",
          capture(mod.top_ten, "boom").strip() == "None")
    check_headers("task 1")
    check("1-main invalid output",
          run_main("1-main.py", ["this_is_a_fake_subreddit"]).strip()
          == "None")
    check("1-main valid output has 10 lines",
          len(run_main("1-main.py", ["programming"]).splitlines()) == 10)


def verify_task2():
    print("\n== Task 2: Recurse it! ==")
    mod = load("2-recurse")
    del CALLS[:]
    result = mod.recurse("programming")
    check("returns all titles across pages", result == TITLES,
          str(None if result is None else len(result)))
    check("paginated (3 requests for 250 posts)", len(CALLS) == 3,
          str(len(CALLS)))
    check("invalid subreddit -> None",
          mod.recurse("this_is_a_fake_subreddit") is None)
    check("network error -> None", mod.recurse("boom") is None)
    again = mod.recurse("programming")
    check("repeat call not polluted by mutable default",
          again == TITLES, str(None if again is None else len(again)))
    check_headers("task 2")
    calls_self, has_loop = is_recursive_no_loops("2-recurse.py", "recurse")
    check("recurse() calls itself", calls_self)
    check("recurse() has no for/while loop", not has_loop)
    check("2-main valid output",
          run_main("2-main.py", ["programming"]).strip() == str(len(TITLES)))
    check("2-main invalid output",
          run_main("2-main.py", ["this_is_a_fake_subreddit"]).strip()
          == "None")


def verify_task3():
    print("\n== Task 3: Count it! ==")
    mod = load("3-count")
    del CALLS[:]
    out = capture(mod.count_words, "programming",
                  ["react", "python", "java", "javascript", "scala",
                   "no_results_for_this_one"])
    expected = ("java: 6\n"
                "python: 3\n"
                "javascript: 1\n"
                "react: 1\n"
                "scala: 1\n")
    check("counts, ordering, skips zero-match words", out == expected,
          repr(out))
    check("java./java!/java_ not counted as java", "java: 6" in out)
    out = capture(mod.count_words, "programming", ["JavA", "java"])
    check("duplicate words are summed (case-insensitive)",
          out == "java: 12\n", repr(out))
    out = capture(mod.count_words, "programming", ["Python", "REACT"])
    check("output is lowercase", out == "python: 3\nreact: 1\n", repr(out))
    check("tie broken alphabetically",
          capture(mod.count_words, "programming", ["scala", "react"])
          == "react: 1\nscala: 1\n")
    check("invalid subreddit prints nothing",
          capture(mod.count_words, "this_is_a_fake_subreddit",
                  ["python", "java"]) == "")
    check("network error prints nothing",
          capture(mod.count_words, "boom", ["python"]) == "")
    check("no matches prints nothing",
          capture(mod.count_words, "programming", ["zzzz"]) == "")
    check_headers("task 3")
    calls_self, has_loop = is_recursive_no_loops("3-count.py", "count_words")
    check("count_words() calls itself", calls_self)
    check("count_words() has no for/while loop", not has_loop)
    out = run_main("3-main.py", ["programming", "JavA java"])
    check("3-main duplicate output", out == "java: 12\n", repr(out))
    check("3-main invalid prints nothing",
          run_main("3-main.py", ["not_a_valid_subreddit", "python java"])
          == "")


def verify_live():
    print("\n== Live Reddit API (optional) ==")
    try:
        subs = load("0-subs").number_of_subscribers("programming")
        check("live: programming has subscribers", subs > 0, str(subs))
        check("live: fake subreddit -> 0",
              load("0-subs").number_of_subscribers(
                  "this_is_a_fake_subreddit_xyz") == 0)
        out = capture(load("1-top_ten").top_ten, "programming")
        check("live: top_ten prints 10 lines",
              len(out.splitlines()) == 10, out)
        check("live: fake top_ten prints None",
              capture(load("1-top_ten").top_ten,
                      "this_is_a_fake_subreddit_xyz").strip() == "None")
    except Exception as exc:  # pylint: disable=broad-except
        check("live: network reachable", False, repr(exc))


def main():
    """Run every verification and print a summary."""
    verify_files()
    with mock.patch("requests.get", side_effect=fake_get):
        verify_task0()
        verify_task1()
        verify_task2()
        verify_task3()
    if "--live" in sys.argv:
        verify_live()
    print("\n==============================")
    print("Passed: {}   Failed: {}".format(len(PASSED), len(FAILED)))
    if FAILED:
        print("Failed checks:")
        for name in FAILED:
            print("  - {}".format(name))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
