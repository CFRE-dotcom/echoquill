@echo off
REM ============================================================
REM  EchoQuill - one-time setup
REM  Requires Python 3.10+ from https://www.python.org/downloads/
REM  (check "Add python.exe to PATH" during Python install)
REM ============================================================
echo.
echo Installing EchoQuill...
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Please install Python 3.10 or newer from
    echo https://www.python.org/downloads/ and check "Add python.exe to PATH".
    pause
    exit /b 1
)
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo Something went wrong installing dependencies. See messages above.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo  Done! Double-click EchoQuill.bat to start dictating.
echo  Default hotkey: Ctrl+Alt+Space  (change it in Settings)
echo ============================================================
pause
