import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

TOKEN = os.environ["GH_TOKEN"]
USERNAME = "brunnojob"
NOW = datetime.now(timezone.utc)
SINCE = NOW - timedelta(days=60)
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "brunnodev-profile-metrics"}

def request(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={**HEADERS, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)

query = """query($login:String!,$start:DateTime!,$end:DateTime!){
 user(login:$login){
 contributionsCollection(from:$start,to:$end){
 contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}
 totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
 }
 repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER){
 nodes{isFork languages(first:15,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}
 pageInfo{hasNextPage}
 }
 }
}"""
data = request("https://api.github.com/graphql", {"query": query, "variables": {"login": USERNAME, "start": SINCE.isoformat(), "end": NOW.isoformat()}})
if data.get("errors"):
    raise RuntimeError(str(data["errors"]))
user = data["data"]["user"]
if not user:
    raise RuntimeError("GitHub user not found")
coll = user["contributionsCollection"]
days = sorted((d for w in coll["contributionCalendar"]["weeks"] for d in w["contributionDays"] if SINCE.date().isoformat() <= d["date"] <= NOW.date().isoformat()), key=lambda d: d["date"])
total = sum(d["contributionCount"] for d in days)
languages = Counter()
for repo in user["repositories"]["nodes"]:
    if not repo["isFork"]:
        for edge in repo["languages"]["edges"]:
            languages[edge["node"]["name"]] += edge["size"]
top = languages.most_common(6)
hours = [0] * 24
observed = 0
q = f"author:{USERNAME} committer-date:>={SINCE.date().isoformat()} committer-date:<={NOW.date().isoformat()}"
for page in range(1, 11):
    result = request("https://api.github.com/search/commits?" + urllib.parse.urlencode({"q": q, "per_page": 100, "page": page}))
    items = result.get("items", [])
    for item in items:
        when = item.get("commit", {}).get("committer", {}).get("date")
        if when:
            local = datetime.fromisoformat(when.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Sao_Paulo"))
            if local.astimezone(timezone.utc) >= SINCE:
                hours[local.hour] += 1
                observed += 1
    if len(items) < 100:
        break

parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="550" viewBox="0 0 960 550" role="img" aria-label="Brunno Dev GitHub activity over the last 60 days">','<rect width="960" height="550" rx="18" fill="#0d1117" stroke="#30363d"/>']
def text(x,y,s,size=14,color="#c9d1d9",weight="400"):
    parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" font-family="Arial, Helvetica, sans-serif">{escape(str(s))}</text>')
def rect(x,y,w,h,fill,rx=3):
    parts.append(f'<rect x="{x}" y="{y}" width="{max(w,0):.1f}" height="{max(h,0):.1f}" rx="{rx}" fill="{fill}"/>')
text(32,43,"ENGINEERING / ACTIVITY REPORT",20,"#e6edf3","700")
text(32,69,f"Rolling 60 days  /  {SINCE.date().isoformat()} — {NOW.date().isoformat()}",13,"#8b949e")
rect(32,90,284,98,"#161b22",10)
rect(338,90,284,98,"#161b22",10)
rect(644,90,284,98,"#161b22",10)
text(50,122,"CONTRIBUTIONS",12,"#8b949e","700")
text(50,167,total,34,"#58a6ff","700")
text(356,122,"COMMIT CONTRIBUTIONS",12,"#8b949e","700")
text(356,167,coll["totalCommitContributions"],34,"#3fb950","700")
text(662,122,"PULL REQUESTS / REVIEWS",12,"#8b949e","700")
text(662,167,f'{coll["totalPullRequestContributions"]} / {coll["totalPullRequestReviewContributions"]}',34,"#e6edf3","700")
text(32,228,"CONTRIBUTION ACTIVITY",14,"#e6edf3","700")
weekly = [sum(d["contributionCount"] for d in days[i:i+7]) for i in range(0,len(days),7)]
maximum = max(weekly,default=1) or 1
for i,v in enumerate(weekly):
    x=38+i*54
    h=round(85*v/maximum)
    rect(x,334-h,32,h,"#238636" if i%2==0 else "#3fb950",4)
    text(x+7,354,str(i+1),11,"#8b949e")
text(38,374,"Contributions by consecutive 7-day windows (oldest to newest)",12,"#8b949e")
text(32,415,"MOST USED LANGUAGES",14,"#e6edf3","700")
colors=["#58a6ff","#3fb950","#f78166","#d2a8ff","#e3b341","#79c0ff"]
langtotal=sum(v for _,v in top) or 1
for i,(name,value) in enumerate(top):
    x=32+(i%3)*305
    y=447+(i//3)*44
    text(x,y,name[:24],12,"#c9d1d9")
    rect(x,y+8,255,7,"#21262d",3)
    rect(x,y+8,255*value/langtotal,7,colors[i],3)
text(32,539,f"Source: GitHub GraphQL API · Public owned repositories · Updated {NOW.strftime('%Y-%m-%d %H:%M')} UTC",11,"#8b949e")
parts.append("</svg>")
out=Path("assets/analytics/activity.svg")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text("\n".join(parts),encoding="utf-8")
print(f"60-day contributions: {total}; commit contributions: {coll['totalCommitContributions']}; sampled authored commits: {observed}")
