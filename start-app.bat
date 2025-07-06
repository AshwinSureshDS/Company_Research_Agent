@echo off
echo Starting Company Research Chatbot...

start cmd /k "cd d:\College\Company_Research_Chatbot && python -m backend.app.main"
echo Backend server starting...
timeout /t 5

start cmd /k "cd d:\College\Company_Research_Chatbot\frontend && npm run dev"
echo Frontend server starting...

echo Both servers are now running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000