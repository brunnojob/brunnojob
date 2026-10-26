import base64
import html
import json
import os
import re
from urllib.request import Request, urlopen


QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    sponsorshipsAsMaintainer(first: 100, after: $cursor, activeOnly: false, includePrivate: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        isActive isOneTimePayment privacyLevel
        sponsorEntity {
          ... on User { login }
          ... on Organization { login }
        }
      }
    }
  }
}
"""


def api(path, token, payload=None, method=None):
    request = Request(
        "https://api.github.com/" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "brunnojob-sponsors-sync",
        },
        method=method,
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_sponsors(login, token):
    sponsors = set()
    cursor = None
    while True:
        result = api("graphql", token, {
            "query": QUERY, "variables": {"login": login, "cursor": cursor}
        })
        if result.get("errors"):
            raise RuntimeError("GitHub Sponsors query failed: " + json.dumps(result["errors"]))
        connection = result["data"]["user"]["sponsorshipsAsMaintainer"]
        for item in connection["nodes"]:
            if not item or item["privacyLevel"] != "PUBLIC":
                continue
            entity = item.get("sponsorEntity")
            if entity and (item["isActive"] or item["isOneTimePayment"]):
                handle = entity["login"]
                if not re.fullmatch(r"[A-Za-z0-9-]+", handle):
                    raise ValueError("Unexpected GitHub login")
                sponsors.add(handle)
        page = connection["pageInfo"]
        if not page["hasNextPage"]:
            return sorted(sponsors, key=str.casefold)
        if not page["endCursor"] or page["endCursor"] == cursor:
            raise RuntimeError("Invalid pagination cursor")
        cursor = page["endCursor"]


def render(sponsors):
    if not sponsors:
        return "<sub>Your support keeps these projects moving. Be the first to join.</sub>"
    cards = []
    for login in sponsors:
        label = html.escape(login, quote=True)
        cards.append(
            f'<a href="https://github.com/{login}" title="{label}">'
            f'<img src="https://github.com/{login}.png?size=96" width="48" height="48" '
            f'alt="@{label}" /></a>'
        )
    return '<p align="center">\n' + "\n".join(cards) + "\n</p>"


def replace_sponsors(readme, sponsors):
    start, end = "<!-- sponsors:start -->", "<!-- sponsors:end -->"
    if readme.count(start) != 1 or readme.count(end) != 1:
        raise ValueError("README must have exactly one sponsors block")
    before, rest = readme.split(start)
    _, after = rest.split(end)
    return before + start + "\n" + render(sponsors) + "\n" + end + after


def main():
    token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    sponsors = fetch_sponsors(repository.split("/")[0], token)
    path = f"repos/{repository}/contents/README.md"
    current = api(path, token)
    readme = base64.b64decode(current["content"]).decode("utf-8")
    updated = replace_sponsors(readme, sponsors)
    if updated == readme:
        print("Sponsors are up to date.")
        return
    api(path, token, {
        "message": "docs: update public sponsors",
        "sha": current["sha"],
        "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
    }, method="PUT")
    print(f"Updated {len(sponsors)} public supporters.")


if __name__ == "__main__":
    main()
