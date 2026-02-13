# 🛡️ ThreatLens AI - Complete Project

**XAI-Enabled Cyber Defense Monitor with Multi-Source Correlation**

A full-stack cybersecurity SOC dashboard that correlates threats across network, camera, RF, logs, and file systems using AI/ML with explainable AI (XAI) capabilities.

---

## 🎯 Project Overview

ThreatLens AI is a comprehensive security monitoring platform that:

- **Correlates multi-source security events** (network, camera, RF, logs, files)
- **Provides real-time threat detection** with risk scoring
- **Offers explainable AI** with SHAP values and natural language explanations
- **Anchors evidence to blockchain** for tamper-proof chain of custody
- **Includes SOC Copilot** powered by local LLM (Mistral-7B)
- **Visualizes attack progression** with causal graphs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                  │
│  Alert Feed | Incident Details | Live Monitor | Copilot    │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST + WebSocket
┌─────────────────────┴───────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  API Endpoints | WebSocket Streams | Kafka Consumers       │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Elasticsearch  │  MinIO  │ Neo4j │
├─────────────────────────────────────────────────────────────┤
│  Kafka Event Bus  │  Ollama (LLM)  │  Polygon (Blockchain) │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop
- Git

### 1. Clone Repository

```powershell
git clone <your-repo-url>
cd ThreatLens
```

### 2. Start Backend Services

```powershell
cd backend

# Start all infrastructure services
docker-compose up -d

# Wait 30 seconds for services to initialize
Start-Sleep -Seconds 30

# Pull Ollama LLM model
docker exec -it threatlens-ollama ollama pull mistral:7b

# Create Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment config
copy .env.example .env

# Start FastAPI server
python main.py
```

Backend API will be at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### 3. Start Frontend

```powershell
# Open new terminal
cd frontend/threat_lens_frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be at: **http://localhost:3000**

---

## 📊 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | admin / threatlens123 |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin123 |
| Neo4j Browser | http://localhost:7474 | neo4j / threatlens123 |
| Elasticsearch | http://localhost:9200 | - |
| Kafka | localhost:9092 | - |

---

## 🎨 Features Implemented

### ✅ Backend (FastAPI)

- [x] Docker Compose with all services
- [x] PostgreSQL database with full schema
- [x] Pydantic models for all entities
- [x] REST API endpoints for incidents
- [x] WebSocket manager for real-time updates
- [x] Kafka consumer infrastructure
- [x] MinIO evidence storage service
- [x] Blockchain anchoring service (Web3.py)
- [x] SOC Copilot service (Ollama integration)
- [x] Live monitoring endpoints

### ✅ Frontend (React)

- [x] Dark theme optimized for SOC
- [x] Layout with sidebar navigation
- [x] Real-time alert feed with filters
- [x] Incident detail page with tabs
- [x] Timeline visualization
- [x] Live monitoring dashboard
- [x] SOC Copilot chat interface
- [x] Threat intelligence page
- [x] WebSocket integration
- [x] Responsive design

---

## 📁 Project Structure

```
ThreatLens/
├── backend/
│   ├── main.py                     # FastAPI app
│   ├── config.py                   # Settings
│   ├── docker-compose.yml          # All services
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── routes/                 # REST endpoints
│   │   └── websockets/             # WebSocket handlers
│   │
│   ├── consumers/                  # Kafka consumers
│   ├── database/                   # SQLAlchemy models
│   ├── models/                     # Pydantic schemas
│   └── services/                   # Business logic
│
├── frontend/
│   └── threat_lens_frontend/
│       ├── src/
│       │   ├── components/         # React components
│       │   ├── pages/              # Page components
│       │   ├── services/           # API & WebSocket
│       │   └── App.jsx             # Router
│       │
│       ├── package.json
│       └── vite.config.js
│
└── README.md (this file)
```

---

## 🔧 Configuration

### Backend Environment Variables

Edit `backend/.env`:

```ini
# Database
DATABASE_URL=postgresql+asyncpg://admin:threatlens123@localhost:5432/threatlens

# Blockchain (Polygon Mumbai Testnet)
POLYGON_RPC_URL=https://rpc-mumbai.polygon.technology
POLYGON_PRIVATE_KEY=your_private_key_here
POLYGON_CONTRACT_ADDRESS=your_contract_address

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

---

## 🧪 Testing the System

### 1. Check Backend Health

```powershell
curl http://localhost:8000/health
```

### 2. Test API Endpoints

```powershell
# Get incidents
curl http://localhost:8000/api/incidents

# Get system health
curl http://localhost:8000/api/live/health

# Query copilot
curl -X POST http://localhost:8000/api/copilot/query `
  -H "Content-Type: application/json" `
  -d '{\"question\": \"Show me critical incidents\"}'
```

### 3. Test WebSocket

Open browser console on http://localhost:3000 and check for:
```
✅ WebSocket connected: /ws/alerts
```

### 4. Add Sample Data

The system needs incident data from Kafka topics. To manually test:

```python
# Run this in Python to insert sample incident
import asyncio
from database.postgres import AsyncSessionLocal
from database.schemas import Incident
from datetime import datetime

async def add_sample():
    async with AsyncSessionLocal() as db:
        incident = Incident(
            incident_id="INC-2024-001",
            timestamp=datetime.now(),
            risk_score=94,
            severity="CRITICAL",
            rule_name="Coordinated Insider Data Theft",
            sources_involved=["camera", "logs", "network", "file"],
            correlated_events=[],
            intent_primary="DATA_EXFILTRATION",
            intent_confidence=0.94,
            mitre_ttps=["T1078", "T1041", "T1486"],
            zone="Server Room"
        )
        db.add(incident)
        await db.commit()
        print("✅ Sample incident added!")

asyncio.run(add_sample())
```

---

## 📖 User Guide

### Navigation

**Sidebar Menu:**
- 🚨 **Alerts** - Main incident feed
- 📹 **Live Monitor** - Real-time metrics
- 🤖 **Copilot** - AI assistant
- 🧬 **Threats** - Threat intelligence

### Alert Feed Page

1. View all security incidents sorted by risk score
2. Filter by severity (Critical/High/Medium/Low)
3. Filter by source (camera/network/logs/rf/file)
4. Click any incident card to view details
5. Quick actions: Isolate Host, Block IP

### Incident Detail Page

**Tabs:**
- **Overview** - Summary, sources, MITRE TTPs, status
- **Timeline** - Chronological event sequence
- **Evidence** - Files, videos, logs (requires MinIO)
- **XAI** - Explainable AI analysis

### Live Monitoring Page

Real-time metrics for:
- Network traffic
- Login attempts
- Camera zones
- RF devices
- File modifications
- Anomaly scores

### SOC Copilot

Ask natural language questions:
- "What are the critical incidents today?"
- "Show me all data exfiltration attempts"
- "Which hosts should be isolated?"

The copilot uses Mistral-7B running locally via Ollama.

---

## 🔗 Integration Points

### For Full System Integration

To integrate with the complete ThreatLens pipeline (Part 2):

1. **Kafka Topics** - Backend consumers listen to:
   - `correlated-incidents`
   - `evidence-manifest`
   - `sandbox-results`
   - `nlg-explanations`
   - `blockchain-receipts`
   - `network-anomalies`, `camera-alerts`, etc.

2. **Uncomment Consumers** in `backend/main.py`:
   ```python
   from consumers.incident_consumer import IncidentConsumer
   from consumers.live_consumer import LiveConsumer
   asyncio.create_task(IncidentConsumer().run())
   asyncio.create_task(LiveConsumer().run())
   ```

3. **Neo4j Attack Graph** - Implement graph queries in incident service

4. **Blockchain Contract** - Deploy evidence registry contract to Polygon Mumbai

---

## 🐛 Troubleshooting

### Backend Issues

**Services not starting?**
```powershell
docker-compose down -v
docker-compose up -d
```

**Database connection error?**
- Wait 30 seconds for PostgreSQL to initialize
- Check logs: `docker-compose logs postgres`

**Ollama model not found?**
```powershell
docker exec -it threatlens-ollama ollama pull mistral:7b
```

### Frontend Issues

**WebSocket not connecting?**
- Ensure backend is running on port 8000
- Check browser console for errors

**API calls failing (CORS)?**
- Backend CORS is configured for localhost:3000
- Check if you're running on correct port

**Blank page?**
```powershell
npm install
npm run dev -- --force
```

---

## 📝 Development Notes

### Adding New Features

**Backend:**
1. Create route in `api/routes/`
2. Add to router imports in `main.py`
3. Create corresponding Pydantic models in `models/`
4. Update database schema if needed in `database/schemas.py`

**Frontend:**
1. Create component in `src/components/` or page in `src/pages/`
2. Add route in `src/App.jsx`
3. Add sidebar menu item in `src/components/layout/Sidebar.jsx`
4. Create corresponding CSS module

### Code Style

- Backend: Python with type hints, async/await
- Frontend: React hooks, CSS Modules
- API: RESTful with WebSocket for real-time

---

## 🎯 Roadmap / TODO

### Priority Enhancements

- [ ] Complete evidence gallery with video player
- [ ] D3.js attack graph visualization
- [ ] SHAP feature importance charts
- [ ] Sandbox screenshot carousel
- [ ] Live chart components (Recharts)
- [ ] Additional API endpoints (evidence, sandbox, IOCs, blockchain)
- [ ] Authentication & authorization
- [ ] User management system
- [ ] Notification system
- [ ] Export functionality (PDF reports)

### Advanced Features

- [ ] Machine learning model integration
- [ ] Automated response actions
- [ ] Integration with SIEM systems
- [ ] Mobile app version
- [ ] Multi-tenancy support

---

## 📄 License

[Add your license here]

## 👥 Contributors

[Add contributors]

## 📧 Contact

[Add contact information]

---

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- React - UI library
- Polygon - Blockchain infrastructure
- Ollama - Local LLM serving
- Docker - Containerization

---

**Version:** 1.0.0  
**Last Updated:** February 2026

🛡️ **ThreatLens AI** - Securing your infrastructure with intelligence.
