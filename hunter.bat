@echo off
rem hunter record^|download^|transcribe^|short^|trends^|upload^|auto [argumentlar]
set "HCMD=%~1"
if "%HCMD%"=="" (
  echo Ishlatish: hunter record / download / transcribe / short / trends / upload / auto  [argumentlar]
  exit /b 1
)
shift
set "ARGS="
:loop
if "%~1"=="" goto run
set ARGS=%ARGS% %1
shift
goto loop
:run
pushd "%~dp0scripts"
"%~dp0.venv\Scripts\python.exe" "hunter_%HCMD%.py" %ARGS%
set ERR=%ERRORLEVEL%
popd
exit /b %ERR%
