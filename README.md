# 🎯 YouTube Hunter

YouTube jonli efirlarini yozib oladi, videolarni yuklab oladi, ulardan **9:16 Shorts** yasaydi (karaoke subtitr, hook yozuvi, ovozni tekislash), **trend asosida** nom/tavsif/teg yozadi va **YouTube'ga avtomatik joylaydi**. Har qanday til va auditoriya uchun.

Claude skill sifatida ham, oddiy buyruqlar to'plami sifatida ham ishlaydi.

*English summary below.*

---

## Imkoniyatlar

| | |
|---|---|
| 🔴 Jonli efir | Efirni bo'laklab yozadi, uzilsa qayta ulanadi; efirni boshidan yozish ham mumkin |
| ⬇️ Yuklab olish | Bitta video, playlist yoki butun kanal; qayta yuklamaydi |
| 🗣 Transkripsiya | faster-whisper, so'zma-so'z vaqt, **tilni o'zi aniqlaydi** |
| ✂️ Shorts | 9:16 (xira fon / kesish / qora chiziq), karaoke subtitr, hook, loudnorm |
| 📈 Trend | Mavzu bo'yicha oxirgi 30 kundagi top videolar, teglar, sarlavha so'zlari (dunyo yoki davlat bo'yicha) |
| 🚀 Joylash | YouTube Data API, jadval (`publishAt`), kunlik limit |
| 🤖 Avtomat | Kanallarni kuzatadi: efir / yangi video → Shorts → matn → joylash |

## O'rnatish

Repo'ni yuklab oling (`Code → Download ZIP` yoki `git clone`), keyin:

**Windows:** `install.bat` ni 2 marta bosing.
**Mac / Linux:** `bash install.sh`

O'rnatuvchi o'zi tekshiradi va kerak bo'lsa o'rnatadi:

| Nima | Nega kerak |
|---|---|
| Python 3.10+ | skriptlar |
| FFmpeg | kesish, 9:16, subtitr |
| yt-dlp | efir yozish, video yuklash, trend qidiruv |
| faster-whisper | nutqni matnga aylantirish |
| requests | trend (YouTube Data API) |
| google-api-python-client, google-auth-oauthlib, google-auth-httplib2 | YouTube'ga yuklash |
| anthropic | ixtiyoriy: avto rejimda Claude lahza tanlaydi |

Hammasi `~/youtube-hunter/` (Windows: `C:\Users\<siz>\youtube-hunter\`) ichiga, alohida `.venv` muhitiga o'rnatiladi — tizimingizdagi Python'ga tegmaydi.

### Claude skill sifatida
Bu papkani Claude'ga skill qilib qo'shing (masalan Claude Code: `~/.claude/skills/youtube-hunter/`, yoki claude.ai'da ZIP qilib yuklang). Claude birinchi ishlatishda o'rnatuvchini o'zi ishga tushiradi va qolgan qadamlarda yo'l ko'rsatadi.

## YouTube'ga ulash (faqat joylash uchun, bir marta)

1. [Google Cloud Console](https://console.cloud.google.com) → yangi loyiha → **APIs & Services → Library** → **YouTube Data API v3** → Enable.
2. **OAuth consent screen** → External → ilova nomi, email → **Test users** ga kanal egasi bo'lgan Google akkauntni qo'shing.
3. **Credentials / Clients** → Create OAuth client ID → **Desktop app** → **Download JSON**.
4. Faylni `~/youtube-hunter/client_secret.json` qilib saqlang. Birinchi yuklashda brauzer ochiladi, ruxsat berasiz.

> "Testing" holatida Google ruxsatni taxminan haftada bir yangilashni so'rashi mumkin. Tekshirilmagan (audit qilinmagan) loyihadan yuklangan videolar private qolishi mumkin.

### Ixtiyoriy kalitlar — `~/youtube-hunter/.env`
```
YT_API_KEY=          # trend tahlili tezroq va aniqroq
ANTHROPIC_API_KEY=   # avto rejimda Claude lahza va matn tanlaydi
```
Bo'sh qolsa ham ishlaydi. **`.env`, `client_secret.json`, `token.json` ni hech qachon GitHub'ga yuklamang** (`.gitignore` ularni bloklaydi).

## Ishlatish

Mac/Linux: `~/youtube-hunter/hunter ...` · Windows: `%USERPROFILE%\youtube-hunter\hunter.bat ...`

```bash
hunter record https://www.youtube.com/@kanal/live --wait     # efirni yozish
hunter download "https://youtu.be/VIDEO_ID"                   # video yuklash
hunter auto process ~/youtube-hunter/downloads/VIDEO_ID.mp4 --no-upload   # Shorts (joylamasdan)
hunter trends "how jet engines work" --region US              # trend
hunter upload short_01.mp4 --meta short_01.json --shorts      # joylash
hunter auto watch --no-upload                                 # to'liq avtomat
```

## Sozlamalar — `~/youtube-hunter/config.json`

| Kalit | Standart | Izoh |
|---|---|---|
| `language` | `auto` | video tili; `auto` = o'zi aniqlaydi |
| `output_language` | `auto` | nom/tavsif/teg tili |
| `trend_region` | `""` | bo'sh = butun dunyo; `US`, `IN`, `UZ`... |
| `whisper_model` | `large-v3` | kuchsiz kompyuterda `medium` / `small` |
| `short_min_sec` / `short_max_sec` | 20 / 59 | Shorts uzunligi |
| `clips_per_video` | 5 | bitta videodan nechta Shorts |
| `layout` | `blur` | `blur` / `crop` / `fit` |
| `privacy` | `private` | `private` / `unlisted` / `public` |
| `schedule_every_hours` | 4 | Shorts orasidagi vaqt |
| `max_uploads_per_day` | 6 | API kvotasi |
| `channels_to_watch` | `[]` | avto rejim kuzatadigan kanallar |
| `cookies` | `""` | YouTube bloklasa `cookies.txt` yo'li |

## ⚠️ Mualliflik huquqi
Faqat o'zingizning yoki ruxsat olingan kontent bilan ishlating. Boshqalarning videolarini ruxsatsiz qayta yuklash copyright strike va kanal o'chirilishiga olib keladi. Foydalanish uchun javobgarlik foydalanuvchida.

---

## English summary

YouTube Hunter records YouTube live streams, downloads videos, turns them into 9:16 Shorts (karaoke captions, hook text, loudness normalization), writes trend-based titles/descriptions/tags in any language, and uploads to YouTube on a schedule — manually or fully automatic.

**Install:** Windows → run `install.bat`; Mac/Linux → `bash install.sh`. Everything goes into `~/youtube-hunter/` with its own virtualenv.
**Upload setup:** create a Google Cloud project, enable YouTube Data API v3, create an OAuth **Desktop app** client, save the JSON as `~/youtube-hunter/client_secret.json`.
**Optional keys** in `~/youtube-hunter/.env`: `YT_API_KEY`, `ANTHROPIC_API_KEY`.
**Use:** `hunter record|download|transcribe|short|trends|upload|auto ...`. Works as a Claude skill too (`SKILL.md`).
Only use content you own or have rights to.

## Litsenziya
MIT — `LICENSE` faylida.
