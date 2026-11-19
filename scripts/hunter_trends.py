"""Trend tahlili: mavzu bo'yicha oxirgi N kunda eng ko'p ko'rilgan videolarning nomi, teglari, ko'rishlari.

python hunter_trends.py "how jet engine works" [--days 30] [--region US] [--lang en] [--n 25]
--region bermasangiz va config'da trend_region bo'sh bo'lsa: butun dunyo bo'yicha.
YT_API_KEY bo'lsa YouTube Data API (tez, aniq), bo'lmasa yt-dlp qidiruv (kalitsiz).
Natija: ~/youtube-hunter/trends/<mavzu>.json + ekranda xulosa (top teglar, top sarlavhalar).
"""
import argparse, json, os, re, subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from hunter_common import ROOT, load_config, ytdlp_base


def via_api(q, days, region, lang, n, key):
    import requests
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    p = {"part": "snippet", "q": q, "type": "video", "order": "viewCount", "maxResults": min(n, 50),
         "publishedAfter": after, "key": key}
    if region:
        p["regionCode"] = region
    if lang and lang != "auto":
        p["relevanceLanguage"] = lang
    ids = [i["id"]["videoId"] for i in
           requests.get("https://www.googleapis.com/youtube/v3/search", params=p, timeout=30).json().get("items", [])]
    if not ids:
        return []
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=30, params={
        "part": "snippet,statistics,contentDetails", "id": ",".join(ids), "key": key}).json()
    return [{"id": v["id"], "title": v["snippet"]["title"], "tags": v["snippet"].get("tags", []),
             "views": int(v["statistics"].get("viewCount", 0)),
             "published": v["snippet"]["publishedAt"][:10], "channel": v["snippet"]["channelTitle"],
             "duration": v["contentDetails"]["duration"]} for v in r.get("items", [])]


def via_ytdlp(q, days, n, cfg):
    cmd = ytdlp_base(cfg) + ["-j", "--skip-download", "--ignore-errors",
                             "--dateafter", f"now-{days}days", f"ytsearch{n}:{q}"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        try:
            v = json.loads(line)
        except ValueError:
            continue
        res.append({"id": v["id"], "title": v.get("title", ""), "tags": v.get("tags") or [],
                    "views": v.get("view_count") or 0, "published": v.get("upload_date", ""),
                    "channel": v.get("channel", ""), "duration": v.get("duration")})
    return sorted(res, key=lambda x: -x["views"])


def trend_report(query, days=30, region=None, lang="", n=25):
    cfg = load_config()
    key = os.environ.get("YT_API_KEY")
    vids = (via_api(query, days, region or cfg["trend_region"], lang, n, key) if key
            else via_ytdlp(query, days, min(n, 20), cfg))
    tags = Counter(t.lower() for v in vids for t in v["tags"])
    words = Counter(w for v in vids for w in re.findall(r"[^\W\d_]{4,}", v["title"].lower()))
    rep = {"query": query, "date": datetime.now().isoformat(timespec="minutes"),
           "top_tags": tags.most_common(30), "title_words": words.most_common(20), "videos": vids}
    d = ROOT / "trends"; d.mkdir(parents=True, exist_ok=True)
    f = d / (re.sub(r"\W+", "_", query)[:60] + ".json")
    f.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--region"); ap.add_argument("--lang", default=""); ap.add_argument("--n", type=int, default=25)
    a = ap.parse_args()
    rep, f = trend_report(a.query, a.days, a.region, a.lang, a.n)
    vids, tags, words = rep["videos"], rep["top_tags"], rep["title_words"]
    print(f"\n== TOP VIDEOLAR ({len(vids)}) ==")
    for v in vids[:10]:
        print(f"{v['views']:>12,}  {v['title'][:90]}")
    print("\n== TOP TEGLAR ==\n" + ", ".join(f"{t}({c})" for t, c in tags[:25]))
    print("\n== SARLAVHA SO'ZLARI ==\n" + ", ".join(f"{t}({c})" for t, c in words[:15]))
    print(f"\nSaqlandi: {f}")


if __name__ == "__main__":
    main()
