"""Jonli efirni yozib olish (bo'laklab).

python hunter_record.py URL [--segment 600] [--wait] [--from-start]
URL: efir havolasi yoki kanal: https://www.youtube.com/@kanal/live
Bo'laklar: ~/youtube-hunter/live/<sana>_<id>/part_YYYYmmdd_HHMMSS.ts
"""
import argparse, json, subprocess, time
from datetime import datetime
from hunter_common import ROOT, load_config, ytdlp_base, need, run


def live_info(cfg, url):
    r = subprocess.run(ytdlp_base(cfg) + ["-j", "--skip-download", url],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return json.loads(r.stdout.splitlines()[0])


def stream_url(cfg, url):
    r = subprocess.run(ytdlp_base(cfg) + ["-g", "-f", "b[height<=1080]/b", url],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip().splitlines()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--segment", type=int, default=600, help="bo'lak uzunligi, soniya")
    ap.add_argument("--wait", action="store_true", help="efir boshlanishini kutish")
    ap.add_argument("--from-start", action="store_true",
                    help="efirni boshidan bitta faylga yozish (DVR kerak)")
    a = ap.parse_args()
    cfg = load_config(); need("ffmpeg")

    info = live_info(cfg, a.url)
    while a.wait and (not info or not info.get("is_live")):
        print("Efir hali boshlanmadi, 60 s kutyapman..."); time.sleep(60)
        info = live_info(cfg, a.url)
    if not info or not info.get("is_live"):
        raise SystemExit("Bu havolada hozir jonli efir yo'q.")

    out = ROOT / "live" / f"{datetime.now():%Y%m%d}_{info['id']}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "info.json").write_text(json.dumps(
        {k: info.get(k) for k in ("id", "title", "channel", "webpage_url")},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Yozilyapti: {info.get('title')} -> {out}")

    if a.from_start:
        run(ytdlp_base(cfg) + ["--live-from-start", "-f", "bv*[height<=1080]+ba/b",
                               "--merge-output-format", "mp4",
                               "-o", str(out / "full.%(ext)s"), info["webpage_url"]])
        return

    # URL bir necha soatda eskiradi -> ffmpeg to'xtasa, efir davom etsa qayta ulanadi
    while True:
        src = stream_url(cfg, info["webpage_url"])
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-i", src,
                        "-c", "copy", "-f", "segment", "-segment_time", str(a.segment),
                        "-reset_timestamps", "1", "-strftime", "1",
                        str(out / "part_%Y%m%d_%H%M%S.ts")])
        time.sleep(5)
        again = live_info(cfg, info["webpage_url"])
        if not again or not again.get("is_live"):
            print("Efir tugadi."); break
        print("Ulanish uzildi, qayta ulanyapman...")
    (out / "DONE").touch()


if __name__ == "__main__":
    main()
