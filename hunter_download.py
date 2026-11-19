"""YouTube video / playlist / kanaldan yuklab olish.

python hunter_download.py URL [--max 5] [--after 20261101] [--height 1080] [--subs hi,en]
Natija: ~/youtube-hunter/downloads/<id>.mp4 (+ .info.json, subtitr bo'lsa .vtt)
"""
import argparse
from hunter_common import ROOT, load_config, ytdlp_base, run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--max", type=int, default=0, help="playlist/kanaldan nechta video")
    ap.add_argument("--after", default="", help="faqat shu sanadan keyingilar, YYYYMMDD")
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--subs", default="", help="subtitr tillari, masalan hi,en")
    a = ap.parse_args()
    cfg = load_config()
    out = ROOT / "downloads"; out.mkdir(parents=True, exist_ok=True)
    archive = ROOT / "downloaded.txt"

    cmd = ytdlp_base(cfg) + [
        "-f", f"bv*[height<={a.height}]+ba/b[height<={a.height}]/b",
        "--merge-output-format", "mp4", "--write-info-json",
        "--download-archive", str(archive),
        "-o", str(out / "%(id)s.%(ext)s")]
    if a.max:
        cmd += ["--playlist-end", str(a.max)]
    if a.after:
        cmd += ["--dateafter", a.after]
    if a.subs:
        cmd += ["--write-subs", "--write-auto-subs", "--sub-langs", a.subs, "--sub-format", "vtt"]
    run(cmd + [a.url])
    print(f"Tayyor: {out}")


if __name__ == "__main__":
    main()
