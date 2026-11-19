"""YouTube Hunter — umumiy yordamchi funksiyalar."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(os.environ.get("HUNTER_HOME", Path.home() / "youtube-hunter"))
CONFIG = ROOT / "config.json"


def _load_env():
    """~/youtube-hunter/.env dagi kalitlarni (YT_API_KEY, ANTHROPIC_API_KEY) o'qish."""
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if v and not os.environ.get(k.strip()):
                os.environ[k.strip()] = v


_load_env()

DEFAULT_CONFIG = {
    "language": "auto",               # video tili: auto (o'zi aniqlaydi) yoki en, hi, uz, ru, es ...
    "output_language": "auto",        # nom/tavsif/teg tili: auto (video tili bilan bir xil) yoki aniq til
    "whisper_model": "large-v3",      # tezroq: medium / small
    "short_min_sec": 20,
    "short_max_sec": 59,
    "clips_per_video": 5,
    "layout": "blur",                 # blur | crop | fit
    "font": "Arial",
    "privacy": "private",             # private | unlisted | public
    "schedule_every_hours": 4,        # avto rejimda Shorts orasidagi interval
    "max_uploads_per_day": 6,         # YouTube API kvotasi
    "category_id": "28",              # 28 = Science & Technology
    "channels_to_watch": [],          # ["https://www.youtube.com/@kanal"]
    "trend_region": "",               # bo'sh = butun dunyo; yoki US, IN, RU, UZ, BR ...
    "claude_model": "claude-sonnet-5-5",
    "cookies": "",                    # cookies.txt yo'li (bloklansa)
}


def load_config():
    ROOT.mkdir(parents=True, exist_ok=True)
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    else:
        CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return cfg


def need(tool):
    if not shutil.which(tool):
        sys.exit(f"XATO: '{tool}' topilmadi. O'rnating (SKILL.md -> O'rnatish).")


def ytdlp_base(cfg):
    # PATH'da bo'lmasa ham ishlaydi: python -m yt_dlp
    cmd = (["yt-dlp"] if shutil.which("yt-dlp") else [sys.executable, "-m", "yt_dlp"]) + ["--no-warnings"]
    if cfg.get("cookies"):
        cmd += ["--cookies", cfg["cookies"]]
    return cmd


def run(cmd, **kw):
    print("▶", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)


def out_lang(cfg, detected=None):
    """Matn (nom/tavsif/teg) qaysi tilda yozilishini aniqlash."""
    if cfg.get("output_language", "auto") not in ("", "auto"):
        return cfg["output_language"]
    if cfg.get("language", "auto") not in ("", "auto"):
        return cfg["language"]
    return detected or "en"


def ts(sec):
    sec = max(0.0, float(sec))
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"
