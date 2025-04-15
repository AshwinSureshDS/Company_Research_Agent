@echo off
echo Starting Company Research Chatbot Backend...
cd d:\College\Company_Research_Chatbot
set PYTHONPATH=d:\College\Company_Research_Chatbot
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000