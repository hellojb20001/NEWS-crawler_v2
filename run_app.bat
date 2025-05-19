@echo off
echo Flask 앱 서버를 시작합니다...

rem Flask 앱 시작 (백그라운드에서 실행)
start /B python C:\webapp\news-crawler-pro-main\news-crawler-pro-main\app.py

rem 서버가 시작될 때까지 잠시 대기 (필요에 따라 시간 조정)
timeout /t 3 /nobreak > nul

rem 브라우저에서 로컬 서버 열기
start "" http://127.0.0.1:5000/

echo 앱이 시작되었습니다.