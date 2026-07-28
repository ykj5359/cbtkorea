@echo off
chcp 65001 > nul
title CBT Korea - 로컬 AI Voice Cloning 서버
cls
echo ========================================================
echo   CBT Korea 로컬 AI Voice Server (Port 9880)
echo ========================================================
echo.
echo [안내] 내 목소리 음성 샘플(my_voice_sample.wav)이 발견되면
echo        나만의 목소리로 숏츠 음성을 100% 무료로 자동 생성합니다!
echo.
echo  서버 주소: http://127.0.0.1:9880
echo  상태 점검: http://127.0.0.1:9880/health
echo.
echo  종료하려면 이 창에서 Ctrl + C 를 누르세요.
echo ========================================================
echo.

python local_voice_server.py

pause
