#!/bin/bash

source env/Scripts/activate  # or env/bin/activate if using Unix-based venv
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
