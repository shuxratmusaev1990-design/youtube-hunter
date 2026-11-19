"""YouTube Hunter — to'liq avtomat rejim.

python hunter_auto.py process VIDEO [--topic "jet engine"] [--region US] [--no-upload]   # bitta fayl
python hunter_auto.py watch [--interval 300] [--no-upload]                 # kanallarni kuzatish (to'xtovsiz)

Har bir video uchun: transkripsiya -> eng yaxshi lahzalar -> Shorts -> trend asosida nom/tavsif/teg
-> jadval bo'yicha YouTube'ga (yoki --no-upload bo'lsa ~/youtube-hunter/queue/ ga).
ANTHROPIC_API_KEY bo'lsa lahza va matnlarni Claude tanlaydi, bo'lmasa oddiy evristika.
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from hunter_common import ROOT, load_config, ytdlp_base, ts, out_lang

HERE = Path(__file__).parent
STATE = ROOT / "state.json"


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "uploads": {}, "next_slot": None}


def save(st):
    STATE.write_text(json.dumps(st, indent=1))


# ---------- lahza tanlash va matn ----------
PROMPT = """You are a YouTube Shorts editor. Below is a timestamped transcript of a video and trend data
for its topic. Pick the {n} best self-contained moments for Shorts ({mn}-{mx} seconds each):
strong hook in first 2 seconds, one complete idea, ends cleanly. Do not overlap clips.
For each clip write metadata in language "{lang}", using the trend tags/title patterns where they
fit honestly (no clickbait that the clip does not deliver):
- hook: on-screen text, max 6 words
- title: max 70 chars, curiosity + main keyword, may end with 1 emoji
- description: 2-3 sentences + 3-5 hashtags incl. #Shorts
- tags: 10-15 tags, mix of trend tags and specific ones
Return ONLY JSON: {{"clips":[{{"start":sec,"end":sec,"hook":"","title":"","description":"","tags":[]}}]}}

SOURCE TITLE: {title}
TREND TOP TAGS: {tags}
TREND TOP TITLES: {titles}

TRANSCRIPT:
{tr}"""


def pick_with_claude(cfg, segments, title, trend, lang):
    import anthropic
    tr = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments)[:150000]
    msg = anthropic.Anthropic().messages.create(
        model=cfg["claude_model"], max_tokens=4000,
        messages=[{"role": "user", "content": PROMPT.format(
            n=cfg["clips_per_video"], mn=cfg["short_min_sec"], mx=cfg["short_max_sec"],
            lang=lang, title=title,
            tags=", ".join(t for t, _ in trend.get("top_tags", [])[:25]),
            titles=" | ".join(v["title"] for v in trend.get("videos", [])[:10]), tr=tr)}])
    txt = msg.content[0].text
    return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])["clips"]


def pick_heuristic(cfg, segments, title, trend, lang):
    """API kalitsiz: so'z zichligi, savol/undov belgilari bo'yicha oyna tanlash."""
    mn, mx, cands = cfg["short_min_sec"], cfg["short_max_sec"], []
    for i, s in enumerate(segments):
        j, txt = i, []
        while j < len(segments) and segments[j]["end"] - s["start"] <= mx:
            txt.append(segments[j]["text"]); j += 1
            dur = segments[j - 1]["end"] - s["start"]
            if dur >= mn:
                t = " ".join(txt)
                score = len(t.split()) / dur + 2 * t.count("?") + t.count("!") + (1.5 if "?" in txt[0] else 0)
                cands.append((score, s["start"], segments[j - 1]["end"], txt[0]))
    cands.sort(reverse=True); chosen = []
    for sc, a, b, first in cands:
        if all(b <= c["start"] or a >= c["end"] for c in chosen):
            tags = [t for t, _ in trend.get("top_tags", [])[:12]]
            chosen.append({"start": a, "end": b, "hook": " ".join(first.split()[:6]),
                           "title": (first[:65] or title[:65]),
                           "description": f"{first}\n\n#Shorts " + " ".join("#" + re.sub(r'\W', '', t) for t in tags[:3]),
                           "tags": tags})
        if len(chosen) >= cfg["clips_per_video"]:
            break
    return sorted(chosen, key=lambda c: c["start"])


# ---------- jadval ----------
def next_publish_time(cfg, st):
    now = datetime.now(timezone.utc)
    slot = datetime.fromisoformat(st["next_slot"]) if st.get("next_slot") else now
    slot = max(slot, now + timedelta(minutes=20))
    while st["uploads"].get(slot.strftime("%Y-%m-%d"), 0) >= cfg["max_uploads_per_day"]:
        slot = (slot + timedelta(days=1)).replace(hour=12, minute=0, second=0)
    st["uploads"][slot.strftime("%Y-%m-%d")] = st["uploads"].get(slot.strftime("%Y-%m-%d"), 0) + 1
    st["next_slot"] = (slot + timedelta(hours=cfg["schedule_every_hours"])).isoformat()
    return slot.replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------- asosiy ishlov ----------
def process(video, topic=None, upload=True, region=None):
    from hunter_transcribe import transcribe
    from hunter_short import make_short
    from hunter_trends import trend_report
    cfg, st = load_config(), state()
    video = Path(video)
    if str(video) in st["done"]:
        print("Allaqachon ishlangan:", video); return
    info_f = next((p for p in (video.with_suffix(".info.json"), video.parent / "info.json") if p.exists()), None)
    title = json.loads(info_f.read_text(encoding="utf-8")).get("title", video.stem) if info_f else video.stem
    words_f = video.with_suffix(".words.json")
    if words_f.exists():
        wj = json.loads(words_f.read_text(encoding="utf-8"))
        segs, detected = wj["segments"], wj.get("language")
    else:
        segs, _, detected = transcribe(video)
    lang = out_lang(cfg, detected)
    print(f"Video tili: {detected} | matn tili: {lang}")
    if not segs:
        print("Nutq topilmadi:", video); st["done"].append(str(video)); save(st); return
    try:
        trend, _ = trend_report(topic or title, region=region, lang=lang)
    except Exception as e:
        print("Trend olinmadi:", e); trend = {}
    picker = pick_with_claude if os.environ.get("ANTHROPIC_API_KEY") else pick_heuristic
    clips = picker(cfg, segs, title, trend, lang)
    out_dir = ROOT / ("shorts" if upload else "queue") / video.stem
    for k, c in enumerate(clips, 1):
        mp4 = out_dir / f"short_{k:02d}.mp4"
        make_short(video, float(c["start"]), float(c["end"]), mp4, words_f, c.get("hook", ""))
        meta = {k2: c[k2] for k2 in ("title", "description", "tags")}
        meta["source"] = f"{title} @ {ts(c['start'])}-{ts(c['end'])}"
        meta["language"] = detected or lang
        meta["output_language"] = lang
        if upload:
            from hunter_upload import upload as yt_upload
            meta["publish_at"] = next_publish_time(cfg, st); save(st)
            meta["url"] = yt_upload(mp4, meta, shorts=True)
        mp4.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    st["done"].append(str(video)); save(st)
    print(f"\n✅ {len(clips)} ta Shorts: {out_dir}")


def watch(interval, upload):
    cfg = load_config(); recorders = {}
    if not cfg["channels_to_watch"]:
        sys.exit("config.json -> channels_to_watch ga kanal havolalarini yozing.")
    while True:
        for ch in cfg["channels_to_watch"]:
            ch = ch.rstrip("/")
            # 1) jonli efir bo'lsa yozishni boshlash
            if ch not in recorders or recorders[ch].poll() is not None:
                r = subprocess.run(ytdlp_base(cfg) + ["-j", "--skip-download", ch + "/live"],
                                   capture_output=True, text=True)
                if r.returncode == 0 and '"is_live": true' in r.stdout:
                    print("🔴 Efir topildi:", ch)
                    recorders[ch] = subprocess.Popen([sys.executable, str(HERE / "hunter_record.py"), ch + "/live"])
            # 2) yangi yuklangan videolar
            subprocess.run([sys.executable, str(HERE / "hunter_download.py"), ch + "/videos", "--max", "3",
                            "--after", (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")])
        # 3) tayyor fayllarni ishlash (yozilayotgan oxirgi bo'lakni tegmaymiz)
        files = sorted((ROOT / "downloads").glob("*.mp4"))
        for d in (ROOT / "live").glob("*"):
            parts = sorted(d.glob("part_*.ts"))
            files += parts if (d / "DONE").exists() else parts[:-1]
        for f in files:
            try:
                process(f, upload=upload)
            except Exception as e:
                print("XATO", f, e)
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("process"); p.add_argument("video"); p.add_argument("--topic"); p.add_argument("--region")
    p.add_argument("--no-upload", action="store_true")
    w = sub.add_parser("watch"); w.add_argument("--interval", type=int, default=300)
    w.add_argument("--no-upload", action="store_true")
    a = ap.parse_args()
    if a.cmd == "process":
        process(a.video, a.topic, upload=not a.no_upload, region=a.region)
    else:
        watch(a.interval, upload=not a.no_upload)
