@echo off
REM ============================================================
REM  Build EchoQuill.exe - a single standalone executable.
REM  Run install.bat first (one time), then double-click this.
REM  Result: dist\EchoQuill.exe
REM ============================================================
cd /d "%~dp0"
python -m pip install pyinstaller
python scripts\gen_icon.py
python -m PyInstaller --noconsole --name EchoQuill ^
  --icon icon.ico ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --collect-all pystray ^
  --hidden-import pyperclip ^
  --hidden-import keyboard ^
  --collect-all tkinterdnd2 ^
  --collect-all yt_dlp ^
  --collect-all keyring ^
  --hidden-import keyring.backends.Windows ^
  --hidden-import win32ctypes.core ^
  --hidden-import win32ctypes.core.ctypes ^
  run.py
if errorlevel 1 (
    echo Build failed - see messages above.
    pause
    exit /b 1
)
set /p EQVER=<version.txt
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\EchoQuill.lnk'); $sc.TargetPath = '%~dp0dist\\EchoQuill\\EchoQuill.exe'; $sc.IconLocation = '%~dp0dist\\EchoQuill\\EchoQuill.exe,0'; $sc.Description = 'EchoQuill v%EQVER% - free local voice dictation'; $sc.Save()"
REM refresh the Windows icon cache so the new version badge shows up
ie4uinit.exe -show >nul 2>&1
echo Desktop shortcut created (EchoQuill v%EQVER%).
echo.
echo ============================================================
echo  Done! Your program is at:  dist\EchoQuill\EchoQuill.exe
echo  You can copy it anywhere and run it directly.
echo ============================================================
pause
