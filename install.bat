@echo off
chcp 65001 >nul
setlocal
rem YouTube Hunter — Windows o'rnatuvchi. Ishlatish: install.bat ni 2 marta bosing.
set "HERE=%~dp0"
if "%HUNTER_HOME%"=="" (set "HH=%USERPROFILE%\youtube-hunter") else (set "HH=%HUNTER_HOME%")
echo ===== YouTube Hunter o'rnatilyapti -^> %HH% =====

where winget >nul 2>nul || (echo winget topilmadi. Microsoft Store'dan "App Installer" ni o'rnating. & pause & exit /b 1)

where py >nul 2>nul
if errorlevel 1 (
  echo [1/5] Python o'rnatilyapti...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1"
) else (echo [1/5] Python bor.)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [2/5] FFmpeg o'rnatilyapti...
  winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
) else (echo [2/5] FFmpeg bor.)

set "PY=py -3"
where py >nul 2>nul || set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo [3/5] Skriptlar ko'chirilyapti...
mkdir "%HH%\scripts" 2>nul
xcopy /y /q "%HERE%scripts\*" "%HH%\scripts\" >nul
if not exist "%HH%\config.json" copy "%HERE%config.example.json" "%HH%\config.json" >nul
if not exist "%HH%\.env" copy "%HERE%.env.example" "%HH%\.env" >nul

echo [4/5] Python kutubxonalari o'rnatilyapti (bir necha daqiqa)...
%PY% -m venv "%HH%\.venv"
"%HH%\.venv\Scripts\python.exe" -m pip install -q --upgrade pip
"%HH%\.venv\Scripts\python.exe" -m pip install -q -r "%HH%\scripts\requirements.txt"
"%HH%\.venv\Scripts\python.exe" -m pip install -q -U yt-dlp

copy /y "%HERE%hunter.bat" "%HH%\hunter.bat" >nul

echo [5/5] Tekshiruv...
"%HH%\.venv\Scripts\python.exe" -m yt_dlp --version
"%HH%\.venv\Scripts\python.exe" -c "import faster_whisper, googleapiclient, anthropic; print('kutubxonalar OK')"
where ffmpeg >nul 2>nul || echo FFmpeg yangi oynada ko'rinadi (terminalni qayta oching)
echo.
echo TAYYOR! Papka: %HH%
echo Keyingi qadam: README.md -^> "YouTube'ga ulash" bo'limi (client_secret.json).
echo Sinov: "%HH%\hunter.bat" auto process VIDEO.mp4 --no-upload
pause
