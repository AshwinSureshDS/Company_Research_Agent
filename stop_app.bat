@echo off
echo Stopping Company Research Chatbot...
echo.
echo Stopping backend server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F
echo.
echo Stopping frontend server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /PID %%a /F
echo.
echo All servers have been stopped.