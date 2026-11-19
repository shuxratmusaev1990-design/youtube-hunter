"""Video/audio -> so'zma-so'z vaqtli transkripsiya (faster-whisper).

python hunter_transcribe.py VIDEO [--lang auto|en|hi|uz|ru...] [--model large-v3]
Natija: VIDEO.words.json (Shorts subtitri uchun) va VIDEO.transcript.txt ([mm:ss] qatorlar)
"""
import argparse, json
from pathlib import Path
from hunter_common import load_config, ts


def transcribe(path, lang=None, model_name=None):
    from faster_whisper import WhisperModel
    cfg = load_config()
    lang = lang or cfg["language"]
    lang = None if lang in ("", "auto") else lang   # None = whisper tilni o'zi aniqlaydi
    model_name = model_name or cfg["whisper_model"]
    try:
        model = WhisperModel(model_name, device="cuda", compute_type="float16")
    except Exception:
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, info = model.transcribe(str(path), language=lang, vad_filter=True, word_timestamps=True)
    segments, words = [], []
    for s in segs:
        segments.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
        for w in (s.words or []):
            words.append({"s": round(w.start, 2), "e": round(w.end, 2), "w": w.word.strip()})
        print(f"[{ts(s.start)}] {s.text.strip()}", flush=True)
    p = Path(path)
    p.with_suffix(".words.json").write_text(
        json.dumps({"language": info.language, "segments": segments, "words": words}, ensure_ascii=False), encoding="utf-8")
    p.with_suffix(".transcript.txt").write_text(
        "\n".join(f"[{ts(s['start'])}-{ts(s['end'])}] {s['text']}" for s in segments), encoding="utf-8")
    print(f"Aniqlangan til: {info.language} ({info.language_probability:.0%})")
    return segments, words, info.language


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--lang"); ap.add_argument("--model")
    a = ap.parse_args()
    transcribe(a.video, a.lang, a.model)
