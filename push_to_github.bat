@echo off
chcp 65001 >nul
echo ========================================================
echo  🧵 Tewabu ERP - GitHub & Render Deploy Helper
echo ========================================================
echo.

set GIT_CMD=git
where git >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :found_git

if exist "C:\Users\Admin\.gemini\antigravity\tools\git\cmd\git.exe" (
    set GIT_CMD="C:\Users\Admin\.gemini\antigravity\tools\git\cmd\git.exe"
    goto :found_git
)

if exist "C:\Program Files\Git\cmd\git.exe" (
    set GIT_CMD="C:\Program Files\Git\cmd\git.exe"
    goto :found_git
)

if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
    set GIT_CMD="%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
    goto :found_git
)

echo [!] Git is not found yet on your system.
echo Please install Git from https://git-scm.com/download/win or wait a moment for setup to finish.
pause
exit /b 1

:found_git
echo [✓] Git detected: %GIT_CMD%
echo.

echo [1/4] Initializing Git repository...
%GIT_CMD% init
echo [2/4] Adding project files...
%GIT_CMD% add .
echo [3/4] Creating initial commit...
%GIT_CMD% commit -m "Initial commit for Tewabu ERP Render deploy"
%GIT_CMD% branch -M main

echo.
echo [4/4] Remote repository setup:
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/yourname/tewabu-erp.git): "

if "%REPO_URL%"=="" (
    echo [!] No URL provided. You can run git push later.
    pause
    exit /b 0
)

%GIT_CMD% remote remove origin >nul 2>&1
%GIT_CMD% remote add origin %REPO_URL%
echo.
echo [*] Pushing to GitHub...
%GIT_CMD% push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo ✅ Code successfully pushed to GitHub!
    echo Next step: Go to https://render.com and connect this repo.
    echo ========================================================
) else (
    echo.
    echo [!] Push encountered an issue. Please check your GitHub repository permissions.
)
pause
