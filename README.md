AI chatbot agent that helps job seekers and investors efficiently research companies by providing real-time data on company profiles, financials, and industry comparisons. It uses persistent memory to recall user interests and previous queries across sessions, ensuring personalized and up-to-date insights—even after chat resets.

# Company Research Chatbot

This project is a full-stack application designed to provide a chatbot interface for company research. It leverages modern web technologies for the frontend and a Python-based backend for data processing, embeddings, and chat memory management.

## Features
- Conversational AI chatbot for company research
- Data ingestion and embedding generation
- Persistent chat memory
- Modern frontend built with Next.js and Tailwind CSS
- Backend powered by FastAPI (or similar Python framework)

## Project Structure
```
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   ├── memory/
│   │   ├── scripts/
│   │   ├── tools/
│   │   ├── config.py
│   │   ├── data_ingestion.py
│   │   ├── embeddings.py
│   │   ├── main.py
│   │   └── utils.py
│   └── data/
│       └── chats/
├── frontend/
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── utils/
├── requirements.txt
├── package.json
├── start-app.bat
├── start-backend.bat
├── stop_app.bat
├── run.sh
└── Work-flow.png
```

## Getting Started

### Backend
1. **Set up Python environment**
   - Create and activate a virtual environment (see `env/` or use your own)
   - Install dependencies:
     ```sh
     pip install -r requirements.txt
     ```
2. **Run the backend**
   - On Windows:
     ```sh
     start-backend.bat
     ```
   - On Unix:
     ```sh
     ./run.sh
     ```

### Frontend
1. **Install dependencies**
   ```sh
   cd frontend
   npm install
   ```
2. **Run the frontend**
   ```sh
   npm run dev
   ```

## Scripts
- `start-app.bat`: Starts both frontend and backend (Windows)
- `start-backend.bat`: Starts backend only (Windows)
- `stop_app.bat`: Stops the application (Windows)
- `run.sh`: Starts backend (Unix)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE)
