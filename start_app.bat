@echo off
echo Starting Company Research Chatbot...
echo.

REM Check if dependencies are installed
if not exist "d:\College\Company_Research_Chatbot\frontend\node_modules\lucide-react" (
  echo Missing dependencies detected. Running dependency installation...
  call d:\College\Company_Research_Chatbot\install_dependencies.bat
)

echo Starting backend server...
start cmd /k "cd /d d:\College\Company_Research_Chatbot && python -m backend.app.main"
echo.
echo Starting frontend server...
start cmd /k "cd /d d:\College\Company_Research_Chatbot\frontend && npm run dev"
echo.
echo Both servers are starting in separate windows.
echo To close them, press Ctrl+C in each window or close the windows.
echo.
echo Once servers are running:
echo - Backend will be available at: http://localhost:8000
echo - Frontend will be available at: http://localhost:3000
echo.
echo If the page doesn't load automatically, please:
echo 1. Wait 30-60 seconds for both servers to fully start
echo 2. Open http://localhost:3000 manually in your browser
echo 3. If you see any errors, check the terminal windows for details