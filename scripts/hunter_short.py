"""Bitta Shorts yasash: kesish + 9:16 + karaoke subtitr + hook matni + ovozni tekislash.

python hunter_short.py VIDEO --start 123.4 --end 170 --out short1.mp4
       [--words VIDEO.words.json] [--hook "Bu qanday ishlaydi?"] [--layout blur|crop|fit] [--x 0.5]
"""
import argparse, json, subprocess, tempfile
from pathlib import Path
from hunter_common import load_config, need

W, H = 1080, 1920


def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(words, start, end, hook, font):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,520,1
Style: Hook,{font},74,&H00FFFFFF,&H00FFFFFF,&H001E1EE6,&H00000000,1,0,0,0,100,100,0,0,3,18,0,8,70,70,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if hook:
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(min(3.5, end-start))},Hook,,0,0,0,,{esc(hook)}")
    ws = [w for w in words if w["e"] > start and w["s"] < end and w["w"]]
    for i in range(0, len(ws), 3):           # 3 so'zdan guruh, joriy so'z sariq
        grp = ws[i:i + 3]
        for j, w in enumerate(grp):
            s = w["s"] - start
            e = (grp[j + 1]["s"] if j + 1 < len(grp) else w["e"]) - start
            txt = " ".join(("{\\c&H00E6FF&}" + esc(x["w"]).upper() + "{\\c&HFFFFFF&}") if k == j
                           else esc(x["w"]).upper() for k, x in enumerate(grp))
            ev.append(f"Dialogue: 0,{ass_time(s)},{ass_time(max(e, s + 0.05))},Sub,,0,0,0,,{txt}")
    return head + "\n".join(ev) + "\n"


def make_short(video, start, end, out, words_file=None, hook="", layout=None, x=0.5):
    cfg = load_config(); need("ffmpeg")
    layout = layout or cfg["layout"]
    dur = end - start
    if dur > 180:
        raise SystemExit("Shorts 3 daqiqadan oshmasin.")
    words = []
    if words_file and Path(words_file).exists():
        words = json.loads(Path(words_file).read_text(encoding="utf-8"))["words"]
    tmp = Path(tempfile.mkdtemp())
    ass = tmp / "s.ass"
    ass.write_text(build_ass(words, start, end, hook, cfg["font"]), encoding="utf-8")
    ass_path = ass.as_posix().replace(":", "\\:")   # Windows C:\ uchun
    sub = "ass=" + ass_path
    if layout == "crop":
        vf = f"[0:v]scale=-2:{H},crop={W}:{H}:(iw-{W})*{x}:0,{sub}[v]"
    elif layout == "fit":
        vf = f"[0:v]scale={W}:-2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,{sub}[v]"
    else:  # blur: orqa fon xira, o'rtada asl kadr
        vf = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},boxblur=25:5[bg];[b]scale={W}:-2[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{sub}[v]")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(start), "-t", str(dur),
           "-i", str(video), "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"Shorts tayyor: {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--words"); ap.add_argument("--hook", default="")
    ap.add_argument("--layout"); ap.add_argument("--x", type=float, default=0.5)
    a = ap.parse_args()
    make_short(a.video, a.start, a.end, a.out, a.words, a.hook, a.layout, a.x)
