"""YouTube'ga yuklash (YouTube Data API v3, OAuth).

Birinchi marta: ~/youtube-hunter/client_secret.json qo'ying -> brauzerda kanalga ruxsat bering.
python hunter_upload.py VIDEO --meta meta.json
python hunter_upload.py VIDEO --title "..." --desc "..." --tags "a,b,c" [--privacy private]
       [--publish-at 2026-11-20T18:00:00+05:30] [--thumb thumb.jpg] [--shorts]
meta.json: {"title","description","tags":[...],"privacy","publish_at","category_id","language"}
"""
import argparse, json, sys
from pathlib import Path
from hunter_common import ROOT, load_config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok, sec = ROOT / "token.json", ROOT / "client_secret.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not sec.exists():
                sys.exit(f"XATO: {sec} yo'q. Google Cloud'dan OAuth (Desktop app) kalitini yuklab qo'ying.")
            creds = InstalledAppFlow.from_client_secrets_file(str(sec), SCOPES).run_local_server(port=0)
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def clean_tags(tags):
    out, total = [], 0
    for t in tags:
        t = t.strip().replace("<", "").replace(">", "").lstrip("#")
        cost = len(t) + (2 if " " in t else 0) + 1
        if t and total + cost <= 490:
            out.append(t); total += cost
    return out


def upload(video, meta, shorts=False):
    from googleapiclient.http import MediaFileUpload
    cfg = load_config()
    title = meta["title"].replace("<", "").replace(">", "")[:100]
    desc = meta.get("description", "")[:4900]
    if shorts and "#shorts" not in (title + desc).lower():
        desc += "\n\n#Shorts"
    status = {"privacyStatus": meta.get("privacy", cfg["privacy"]), "selfDeclaredMadeForKids": False}
    if meta.get("publish_at"):
        status.update(privacyStatus="private", publishAt=meta["publish_at"])
    snip = {"title": title, "description": desc, "tags": clean_tags(meta.get("tags", [])),
            "categoryId": str(meta.get("category_id", cfg["category_id"]))}
    lang = meta.get("language") or (cfg["language"] if cfg["language"] != "auto" else "")
    if lang:
        snip["defaultLanguage"] = meta.get("output_language", lang)
        snip["defaultAudioLanguage"] = lang
    body = {"snippet": snip, "status": status}
    yt = service()
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"Yuklanyapti {int(st.progress() * 100)}%", flush=True)
    vid = resp["id"]
    if meta.get("thumbnail") and Path(meta["thumbnail"]).exists():
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(meta["thumbnail"])).execute()
    url = f"https://youtu.be/{vid}"
    print(f"JOYLANDI: {url}  ({status['privacyStatus']}{', ' + status.get('publishAt', '') if status.get('publishAt') else ''})")
    log = ROOT / "uploads.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"file": str(video), "url": url, "title": title}, ensure_ascii=False) + "\n")
    return url


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--meta"); ap.add_argument("--title")
    ap.add_argument("--desc", default=""); ap.add_argument("--tags", default="")
    ap.add_argument("--privacy"); ap.add_argument("--publish-at"); ap.add_argument("--thumb")
    ap.add_argument("--shorts", action="store_true")
    a = ap.parse_args()
    if a.meta:
        m = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    else:
        if not a.title:
            sys.exit("--title yoki --meta kerak")
        m = {"title": a.title, "description": a.desc, "tags": [t for t in a.tags.split(",") if t]}
    for k, v in (("privacy", a.privacy), ("publish_at", a.publish_at), ("thumbnail", a.thumb)):
        if v:
            m[k] = v
    upload(a.video, m, shorts=a.shorts)
