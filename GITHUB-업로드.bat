@echo off
title CBT Korea GitHub Push
echo ====================================================
echo Uploading files to GitHub...
echo ====================================================
echo.
cd /d "%~dp0"
git push -u origin main
echo.
echo ====================================================
echo Upload finished! You can close this window.
echo ====================================================
pause
