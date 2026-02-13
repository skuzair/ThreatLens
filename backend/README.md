# ThreatLens AI Backend

FastAPI-based backend for the ThreatLens AI cybersecurity monitoring platform.

## Architecture

```
Backend Stack:
- FastAPI (REST API + WebSocket)
- PostgreSQL (Incident storage)
- Redis (Caching)
- Kafka (Event streaming)
- Elasticsearch (Log search)
- MinIO (Evidence storage)
- Neo4j (Attack graph)
- Ollama (Local LLM)
- Web3.py (Blockchain)
```

## Quick Start

### 1. Start All Services

```powershell
cd backend
docker-compose up -d
```

This starts: PostgreSQL, Redis, Elasticsearch, MinIO, Kafka, Zookeeper, Neo4j, Ollama

### 2. Install Python Dependencies

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
# Copy example env file
copy .env.example .env

# Edit .env with your settings (blockchain keys, etc.)
```

### 4. Pull Ollama Model

```powershell
docker exec -it threatlens-ollama ollama pull mistral:7b
```

### 5. Run the API Server

```powershell
python main.py
```

API will be available at: http://localhost:8000

Interactive API docs: http://localhost:8000/docs

## API Endpoints

### Incidents
- `GET /api/incidents` - List incidents with filters
- `GET /api/incidents/{id}` - Get incident details
- `GET /api/incidents/{id}/timeline` - Get event timeline
- `GET /api/incidents/{id}/graph` - Get attack graph
- `PATCH /api/incidents/{id}/status` - Update incident status

### SOC Copilot
- `POST /api/copilot/query` - Query the LLM copilot

### Live Monitoring
- `GET /api/live/health` - System health status
- `GET /api/live/metrics/{source}` - Get source metrics

### WebSocket Endpoints
- `WS /ws/alerts` - Real-time alert feed
- `WS /ws/live/{source}` - Live data streams (network/camera/rf/logs/files)

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | localhost:5432 | admin / threatlens123 |
| Redis | localhost:6379 | - |
| Elasticsearch | localhost:9200 | - |
| MinIO Console | localhost:9001 | minioadmin / minioadmin123 |
| Kafka | localhost:9092 | - |
| Neo4j Browser | localhost:7474 | neo4j / threatlens123 |
| Ollama | localhost:11434 | - |

## Database Schema

Key tables:
- `incidents` - Correlated security incidents
- `evidence` - Evidence files with blockchain hashes
- `sandbox_results` - Malware analysis results
- `iocs` - Indicators of Compromise
- `alert_events` - Raw alert events

## Kafka Topics

The system expects these topics:
- `correlated-incidents` - Multi-source correlated incidents
- `evidence-manifest` - Evidence file manifests
- `sandbox-results` - Sandbox detonation results
- `nlg-explanations` - NLG explanations
- `blockchain-receipts` - Blockchain anchoring receipts
- `network-anomalies` - Network anomaly events
- `camera-alerts` - Camera detection alerts
- `rf-anomalies` - RF device anomalies
- `log-anomalies` - Log anomalies
- `file-events` - File system events

## Development

Run with auto-reload:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Test the API:
```powershell
# Health check
curl http://localhost:8000/health

# Get incidents
curl http://localhost:8000/api/incidents

# Query copilot
curl -X POST http://localhost:8000/api/copilot/query `
  -H "Content-Type: application/json" `
  -d '{\"question\": \"What are the critical incidents today?\"}'
```

## Docker Management

```powershell
# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Reset everything (WARNING: deletes data)
docker-compose down -v
```

## Blockchain Configuration

To enable blockchain evidence anchoring:

1. Get a Polygon Mumbai testnet account
2. Add test MATIC from faucet: https://faucet.polygon.technology/
3. Update `.env` with your private key and contract address
4. Deploy the evidence registry contract (not included in P1)

## Notes

- Kafka consumers are currently commented out in `main.py`
- Uncomment when you have Kafka topics set up
- MinIO bucket is auto-created on first run
- Database tables are auto-created on startup
