import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

QUERY = """
query($login:String!, $from:DateTime, $to:DateTime) {
  user(login:$login) {
    createdAt
    contributionsCollection(from:$from,to:$to) {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""
def fetch(**variables):
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Content-Type": "application/json", "User-Agent": "profile-activity"},
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors") or not result.get("data", {}).get("user"):
        raise RuntimeError(result.get("errors", "GitHub user not found"))
    return result["data"]["user"]

def render(values):
    labels = ("Commits", "Pull requests", "Code reviews", "Contributions")
    cells = []
    for i, (label, value) in enumerate(zip(labels, values)):
        x, y = 30 + i % 2 * 270, 82 + i // 2 * 82
        number = f"{value:,}" if value is not None else "—"
        cells.append(f'''<g transform="translate({x} {y})">
  <text class="label" y="0">{label}</text>
  <text class="number" y="34">{number}</text>
  <rect y="45" width="220" height="3" rx="1.5" fill="#294866"/>
  <rect class="signal" y="45" width="32" height="3" rx="1.5" fill="#70c6ff" style="animation-delay:{i * -0.5}s"/>
</g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 248" width="560" height="248" role="img" aria-labelledby="title">
<title id="title">GitHub activity totals</title>
<style>
.label {{font: 15px system-ui,sans-serif; fill:#a9c4df}}
.number {{font: bold 28px system-ui,sans-serif; fill:#f3f8ff}}
.signal {{animation:sweep 2.8s ease-in-out infinite alternate}}
@keyframes sweep {{to {{transform:translateX(188px)}}}}
@media(prefers-reduced-motion:reduce) {{.signal {{animation:none}}}}
</style>
<rect x="1" y="1" width="558" height="246" rx="17" fill="#101c2b" stroke="#2a4766" stroke-width="2"/>
<text x="30" y="37" style="font:16px monospace;fill:#79c4ff">GITHUB ACTIVITY TOTALS</text>
<path d="M30 53H530" stroke="#2a4766"/>
{"".join(cells)}
<text x="30" y="229" style="font:12px system-ui,sans-serif;fill:#a9c4df">Public contribution history recorded by GitHub</text>
</svg>
'''

def main():
    login = "brunnojob"
    now = datetime.now(timezone.utc)
    created = datetime.fromisoformat(fetch(login=login)["createdAt"])
    totals = [0, 0, 0, 0]
    for year in range(created.year, now.year + 1):
        start = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        end = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        data = fetch(login=login, **{"from": start.isoformat(), "to": end.isoformat()})["contributionsCollection"]
        values = (data["totalCommitContributions"], data["totalPullRequestContributions"],
                  data["totalPullRequestReviewContributions"], data["contributionCalendar"]["totalContributions"])
        totals = [a + b for a, b in zip(totals, values)]
    Path("assets/profile/profile-activity.svg").write_text(render(totals), encoding="utf-8")

if __name__ == "__main__":
    main()
