# Skill Pilot AI v3.0 - Career Readiness Platform

**Comprehensive career-readiness platform with AI-powered adaptive learning, mock interviews, job matching, college integration, and personalized mentorship.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🚀 Features

### Section 1: Core Learning & Career Readiness
- **Adaptive Learning Roadmaps**: AI-generated, skill-gap-driven roadmaps
- **Career Role Profiling**: 12+ tech roles with skill requirements
- **Diagnostic Assessments**: Dynamic skill evaluation with mastery tracking
- **Coding Practice Lab**: LeetCode-style problems with AI feedback
- **Project Portfolio**: GitHub project evaluation with rubric-based scoring

### Section 2: AI Mentorship & Collaboration
- **AI Mentor Chat**: Context-aware career copilot powered by Grok
- **Human Mentor Matching**: Connect with industry mentors
- **Doubt Resolution**: 1-on-1 coding help with queue management
- **Peer Learning**: Study groups and collaboration features
- **Real-time Analytics**: Progress tracking and insights dashboard

### Section 3: Career Intelligence & College Connect
- **Resume AI Analysis**: Skills extraction, ATS optimization, gap identification
- **Job Description Matching**: AI-powered fit analysis with learning plans
- **Mock Interview Studio**: Technical interviews with instant AI feedback
- **Career Advisor Agent**: Alternative career path recommendations
- **Weekly Study Planner**: Balanced schedules with college integration
- **College Connect**: Course sync, assignment tracking, attendance alerts
- **Portfolio Builder**: Showcase projects, coding stats, leaderboards
- **Career Readiness Reports**: PDF/JSON exports with narrative summaries

## 🛠 Tech Stack

**Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Pydantic  
**Frontend**: React, TypeScript, TailwindCSS, Vite  
**AI**: xAI Grok (grok-2-1212) for all intelligent features  
**Deployment**: Render (PostgreSQL + Web Services)

## 📦 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use SQLite for dev)
- xAI API key (get from https://console.x.ai)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env: add XAI_API_KEY, set DATABASE_URL

# Run database migrations and seed data
python -m app.db.seed

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000  
API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env
# Verify VITE_API_BASE_URL=http://localhost:8000/api/v1

npm run dev
```

Frontend runs at: http://localhost:5173

## 🚀 Deploy to Render

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.**

### Quick Deploy (Using render.yaml)

1. Push to GitHub
2. Connect to Render via Blueprint
3. Set `XAI_API_KEY` environment variable
4. Services auto-deploy in ~15 minutes

### What Gets Deployed

- **PostgreSQL Database** (free tier, 256MB)
- **Backend API** (Python, auto-scales, health checks)
- **Frontend** (Static site, CDN-served)

All services configured via `render.yaml` — zero manual setup required!

## 📝 Default Accounts (After Seeding)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@skillpilot.ai | admin123 |
| Mentor | sarah.mentor@skillpilot.ai | mentor123 |
| Student | alex.student@skillpilot.ai | student123 |

## 🎯 Project Structure

```
skill-pilot-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents (Grok-powered)
│   │   ├── api/v1/          # REST endpoints
│   │   ├── core/            # Config, security, AI client
│   │   ├── db/              # Database, seeds
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── data/            # Static JSON data
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios API calls
│   │   ├── components/      # React components
│   │   ├── pages/           # Route pages
│   │   ├── context/         # Auth context
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── .env.example
├── render.yaml              # Render deployment config
├── DEPLOYMENT.md            # Deployment guide
└── README.md
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### API Health Check
```bash
curl http://localhost:8000/api/v1/health
```

## 🔑 Environment Variables

### Backend (.env)

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (32+ chars)
- `XAI_API_KEY` - xAI Grok API key

**Optional:**
- `XAI_MODEL` - Default: `grok-2-1212`
- `ENVIRONMENT` - `development` or `production`
- `BACKEND_CORS_ORIGINS` - Comma-separated allowed origins
- `MAX_FILE_SIZE_MB` - Default: `5`

### Frontend (.env)

**Required:**
- `VITE_API_BASE_URL` - Backend API URL with `/api/v1`

Example: `http://localhost:8000/api/v1` (dev) or `https://skillpilot-backend.onrender.com/api/v1` (prod)

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **xAI Grok** for powering all AI features
- **Render** for seamless deployment
- Built for the xAI Hackathon 2025

## 🐛 Issues & Support

- GitHub Issues: [Create an issue](https://github.com/YOUR_USERNAME/skill-pilot-ai/issues)
- Documentation: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Made with ❤️ using xAI Grok**
