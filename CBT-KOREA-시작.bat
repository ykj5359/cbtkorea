@echo off
chcp 65001 >nul
title CBT KOREA 로컬 서버
cd /d "%~dp0"
echo.
echo  ============================================
echo    CBT KOREA 로컬 서버를 시작합니다
echo    브라우저가 자동으로 열립니다
echo    (이 창을 닫으면 서버가 종료됩니다)
echo  ============================================
echo.
start "" "http://localhost:8130/index.html"
python -m http.server 8130
pause
