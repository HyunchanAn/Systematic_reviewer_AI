@echo off
:: (This script starts the core services required for the Systematic Reviewer AI project.)

echo.
echo --- Starting Core Services for Systematic Reviewer AI ---
echo.

:: --- 1. GROBID 서비스 시작 (Docker) ---
echo [1/2] Starting GROBID service using Docker...
echo      (This will run in the background)
cd tools\grobid
docker-compose up -d
cd ..\..
echo GROBID service started.
echo.

:: --- 2. Gemma-3 LLM 서버 시작 ---
echo [2/2] Starting Gemma-3 LLM Server...
echo      (A new window will open for the LLM server)
echo.

:: Please place your llamafile inside the 'models' folder of the project.
set LLM_PATH="models\google_gemma-3-12b-it-Q4_K_M.llamafile"

if not exist %LLM_PATH% (
    echo ERROR: LLM file not found at %LLM_PATH%
    echo Please make sure the file 'google_gemma-3-12b-it-Q4_K_M.llamafile' is inside the 'models' directory.
    goto :end
)

start "Gemma 3 LLM Server" %LLM_PATH% --server -ngl 999

echo.
echo --- All services have been launched. ---
echo You can now run 'python main.py' in this terminal.
echo Please keep the new 'Gemma 3 LLM Server' window open.

:end
echo.
pause