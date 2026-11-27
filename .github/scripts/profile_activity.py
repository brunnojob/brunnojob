import html
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

LOGIN = "brunnojob"
TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com/graphql"

def graphql(query, variables=None):
    request = Request(
        API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "brunnojob-profile-sync",
        },
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result["data"]

def contributions():
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        createdAt
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    now = datetime.now(timezone.utc)
    user = graphql(query, {
        "login": LOGIN,
        "from": (now - timedelta(days=365)).isoformat(),
        "to": now.isoformat(),
    })["user"]
    totals = [0, 0, 0, 0]
    calendar_days = []
    for year in range(datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).year, now.year + 1):
        start = max(datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")),
                    datetime(year, 1, 1, tzinfo=timezone.utc))
        end = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        data = graphql(query, {
            "login": LOGIN, "from": start.isoformat(), "to": end.isoformat(),
        })["user"]["contributionsCollection"]
        totals[0] += data["totalCommitContributions"]
        totals[1] += data["totalPullRequestContributions"]
        totals[2] += data["totalPullRequestReviewContributions"]
        totals[3] += data["contributionCalendar"]["totalContributions"]
        if year == now.year:
            calendar_days = [day for week in data["contributionCalendar"]["weeks"]
                             for day in week["contributionDays"]]
    active = {day["date"]: day["contributionCount"] for day in calendar_days}
    today = now.date()
    cursor = today if active.get(today.isoformat(), 0) else today - timedelta(days=1)
    streak = 0
    while active.get(cursor.isoformat(), 0):
        streak += 1
        cursor -= timedelta(days=1)
    return totals, streak

def languages():
    query = """
    query($login: String!, $after: String) {
      user(login: $login) {
        repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                     privacy: PUBLIC, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo { hasNextPage endCursor }
          nodes { name languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
            edges { size node { name color } }
          }}
        }
      }
    }
    """
    totals = {}
    colors = {}
    cursor = None
    while True:
        repos = graphql(query, {"login": LOGIN, "after": cursor})["user"]["repositories"]
        for repo in repos["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                totals[name] = totals.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"] or "#79c4ff"
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]
    return sorted(totals.items(), key=lambda item: (-item[1], item[0])), colors

def render(activity, streak, language_totals, colors, updated):
    labels = ("Commits", "Pull requests", "Code reviews", "Contributions")
    cells = []
    for index, (label, number) in enumerate(zip(labels, activity)):
        x, y = 30 + index % 2 * 270, 82 + index // 2 * 69
        cells.append(f'<g transform="translate({x} {y})"><text class="label">{label}</text>'
                     f'<text class="number" y="29">{number:,}</text></g>')
    entries = language_totals[:6]
    language_text = " · ".join(html.escape(name) for name, _ in entries) or "No public repository language data"
    bars = []
    if entries:
        maximum = max(size for _, size in entries)
        for index, (name, size) in enumerate(entries):
            y = 302 + index * 23
            width = max(2, round(220 * size / maximum))
            bars.append(f'<text class="small" x="30" y="{y}">{html.escape(name)}</text>'
                        f'<rect x="154" y="{y-10}" width="220" height="7" rx="3" fill="#20364c"/>'
                        f'<rect x="154" y="{y-10}" width="{width}" height="7" rx="3" fill="{colors[name]}"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 470" width="560" height="470" role="img" aria-labelledby="title">
<title id="title">GitHub activity and repository languages, synchronized from GitHub</title>
<style>
.label {{font:14px system-ui,sans-serif;fill:#a9c4df}}
.number {{font:bold 25px system-ui,sans-serif;fill:#f3f8ff}}
.small {{font:12px system-ui,sans-serif;fill:#a9c4df}}
</style>
<rect x="1" y="1" width="558" height="468" rx="17" fill="#101c2b" stroke="#2a4766" stroke-width="2"/>
<text x="30" y="37" style="font:16px monospace;fill:#79c4ff">GITHUB ACTIVITY · LIVE DATA</text>
<path d="M30 53H530" stroke="#2a4766"/>
{''.join(cells)}
<text class="label" x="30" y="190">Current contribution streak</text>
<text class="number" x="30" y="224">{streak} days</text>
<text class="label" x="30" y="267">Top languages across public, non-fork repositories</text>
{''.join(bars)}
<text class="small" x="30" y="455">GitHub GraphQL · Updated {updated} UTC · Languages: {language_text}</text>
</svg>
"""

def main():
    activity, streak = contributions()
    language_totals, colors = languages()
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    Path("assets/profile/profile-live.svg").write_text(
        render(activity, streak, language_totals, colors, updated), encoding="utf-8"
    )

if __name__ == "__main__":
    main()
