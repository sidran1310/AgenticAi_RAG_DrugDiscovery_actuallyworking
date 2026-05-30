@echo off
setlocal enabledelayedexpansion

:: Ensure Node.js/npm are on PATH (user PATH often missing in non-interactive scripts)
set PATH=%APPDATA%\npm;%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%PATH%

set ROOT=%~dp0
set BACKEND=%ROOT%app\backend
set FRONTEND=%ROOT%app\frontend

echo ============================================
echo   Drug Discovery AI Agent - Windows Setup
echo ============================================
echo.

:: ── Backend setup ──────────────────────────────────────────────────────────
cd /d "%BACKEND%"

if not exist "venv\Scripts\activate.bat" (
    echo [1/4] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERROR: Python not found or failed to create venv.
        echo Install Python 3.11 from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo       Done.
    echo.
)

call venv\Scripts\activate.bat

echo [2/4] Installing backend dependencies (using pre-built wheels where available)...
echo       This may take a few minutes on first run.
echo.

pip install --upgrade pip
echo.

:: --prefer-binary forces pip to use pre-compiled wheels, avoiding C compiler
:: requirements for packages like Pillow, gevent, lxml, etc. on Windows.
pip install --prefer-binary -r requirements-no-gpu.txt
if errorlevel 1 (
    echo.
    echo ERROR: pip install failed. See errors above.
    pause
    exit /b 1
)
echo.
echo       Dependencies installed.
echo.

:: ── .env setup ─────────────────────────────────────────────────────────────
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created .env from .env.example.
    ) else (
        echo WARNING: No .env.example found. Creating blank .env.
        type nul > .env
    )
)

:: Check if GEMINI and GROQ keys are real (non-dummy, non-empty)
set GROQ_REAL=0
set GEMINI_REAL=0

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "KEY=%%A"
    set "VAL=%%B"
    if "!KEY!"=="GROQ_API_KEY" (
        if not "!VAL!"=="" if not "!VAL!"=="your_groq_api_key_here" set GROQ_REAL=1
    )
    if "!KEY!"=="GEMINI_API_KEY" (
        if not "!VAL!"=="" if not "!VAL!"=="your_gemini_api_key_here" set GEMINI_REAL=1
    )
)

if !GROQ_REAL!==0 (
    echo GROQ_API_KEY is missing or not configured.
    echo Get a free key at: https://console.groq.com
    set /p GROQ_INPUT="  Enter GROQ_API_KEY (or press Enter to skip): "
    if not "!GROQ_INPUT!"=="" (
        set TMPFILE=%TEMP%\env_tmp_%RANDOM%.txt
        %SystemRoot%\System32\findstr.exe /v "^GROQ_API_KEY=" ".env" > "!TMPFILE!"
        echo GROQ_API_KEY=!GROQ_INPUT!>> "!TMPFILE!"
        move /y "!TMPFILE!" ".env" >nul
        echo   Saved.
    )
    echo.
)

if !GEMINI_REAL!==0 (
    echo GEMINI_API_KEY is missing or not configured.
    echo Get a free key at: https://aistudio.google.com
    set /p GEMINI_INPUT="  Enter GEMINI_API_KEY (or press Enter to skip): "
    if not "!GEMINI_INPUT!"=="" (
        set TMPFILE=%TEMP%\env_tmp_%RANDOM%.txt
        %SystemRoot%\System32\findstr.exe /v "^GEMINI_API_KEY=" ".env" > "!TMPFILE!"
        echo GEMINI_API_KEY=!GEMINI_INPUT!>> "!TMPFILE!"
        move /y "!TMPFILE!" ".env" >nul
        echo   Saved.
    )
    echo.
)

:: ── Start backend ──────────────────────────────────────────────────────────
echo [3/4] Starting backend on http://localhost:5001 ...
start "Drug Discovery - Backend" cmd /k "cd /d "%BACKEND%" && call venv\Scripts\activate.bat && echo Backend starting... && python app.py"
echo       Backend window opened.
echo.

:: ── Frontend setup ─────────────────────────────────────────────────────────
cd /d "%FRONTEND%"

echo [4/4] Setting up frontend...
where node >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Node.js not found. Install Node.js 18+ from https://nodejs.org
    echo        Frontend cannot start without Node.js.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo       Installing Node dependencies (first run only)...
    npm install
    if errorlevel 1 (
        echo.
        echo ERROR: npm install failed. See errors above.
        pause
        exit /b 1
    )
    echo       Done.
)

echo       Starting frontend on http://localhost:5173 ...
echo       (browser will open in 8 seconds once Vite is ready)
echo.

:: Open browser after 8s in background while npm run dev runs inline
start /b cmd /c "timeout /t 8 /nobreak >nul && start "" http://localhost:5173"

npm run dev

echo.
echo ============================================
echo   App running at http://localhost:5173
echo   Close the Backend and Frontend windows to stop.
echo ============================================
endlocal
