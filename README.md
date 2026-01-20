# 💰 Finance Companion

A full-stack personal finance management application with voice-enabled expense tracking, AI-powered insights, and budget goal management.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)

## ✨ Features

- **📊 Dashboard** - Real-time overview of income, expenses, and savings
- **🎤 Voice Entry** - Add expenses hands-free using speech recognition (Whisper AI)
- **🤖 AI Insights** - Smart spending analysis and personalized recommendations
- **🎯 Budget Goals** - Set savings targets with progress tracking
- **📈 Analytics** - Category breakdowns, spending trends, and month-over-month comparisons
- **🔐 Secure Auth** - JWT-based authentication with password hashing
- **🌙 Dark Mode** - Toggle between light and dark themes

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **OpenAI Whisper** - Speech-to-text for voice input
- **OpenRouter API** - AI-powered financial insights

### Frontend
- **React 19** - UI library
- **Vite** - Build tool
- **Tailwind CSS 4** - Styling
- **Zustand** - State management
- **Recharts** - Data visualization
- **Axios** - HTTP client

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Arhum19/Personal_Ai_Finance_Companion.git
cd Finance_companion

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:5173` for the app and `http://localhost:8000/docs` for API documentation.

## 📁 Project Structure

```
Finance_companion/
├── app/                    # FastAPI Backend
│   ├── main.py            # App entry point
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── dependencies.py    # Auth & DB dependencies
│   ├── routes/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── expense.py     # Expense CRUD
│   │   ├── income.py      # Income CRUD
│   │   ├── goals.py       # Savings goals
│   │   ├── insights.py    # AI analytics
│   │   └── voice.py       # Voice transcription
│   ├── services/          # Business logic
│   │   ├── insight_service.py  # Calculations
│   │   └── ai_insights.py      # OpenRouter integration
│   └── voice_client/      # NLP parsing
│
├── frontend/              # React Frontend
│   └── src/
│       ├── pages/         # Page components
│       ├── components/    # Reusable components
│       ├── services/      # API client
│       └── store/         # Zustand stores
│
└── requirements.txt       # Python dependencies
```

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/{YOUR_DB_NAME}
SECRET_KEY=your-secret-key-here
finance_companion_key=your-openrouter-api-key  # Optional, for AI insights
WHISPER_MODEL=small  # tiny, base, small, medium, large
```

# 📱 Screenshots
## Dashboard
![Dashboard](/frontend/public/dashboard.png)
## voice Entry
![Voice Entry](/frontend/public/voice.png)
## AI Insights 
![AI Insights](/frontend/public/ai.png)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

Built with ❤️ by [Muhammad Arhum]