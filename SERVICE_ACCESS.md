# 🔐 Service Access Configuration

## Environment Configuration File

All service configurations are stored in:
```
backend/.env
```

## 🌐 Service URLs & Credentials

### Application Services

| Service | URL | Username | Password | Notes |
|---------|-----|----------|----------|-------|
| **Frontend** | http://localhost:3000 | - | - | React Dashboard |
| **Backend API** | http://localhost:8000 | - | - | FastAPI Server |
| **API Docs** | http://localhost:8000/docs | - | - | Swagger UI |

### Data Services

| Service | URL | Username | Password | Connection String |
|---------|-----|----------|----------|-------------------|
| **PostgreSQL** | localhost:5432 | `admin` | `threatlens123` | `postgresql://admin:threatlens123@localhost:5432/threatlens` |
| **Redis** | localhost:6379 | - | - | `redis://localhost:6379` |
| **Elasticsearch** | http://localhost:9200 | - | - | `http://localhost:9200` |
| **MinIO Console** | http://localhost:9001 | `minioadmin` | `minioadmin123` | S3-compatible storage |
| **MinIO API** | http://localhost:9000 | `minioadmin` | `minioadmin123` | Object storage endpoint |
| **Kafka** | localhost:9092 | - | - | `localhost:9092` |
| **Zookeeper** | localhost:2181 | - | - | Kafka coordination |
| **Neo4j Browser** | http://localhost:7474 | `neo4j` | `threatlens123` | Graph database UI |
| **Neo4j Bolt** | bolt://localhost:7687 | `neo4j` | `threatlens123` | Database connection |
| **Ollama** | http://localhost:11434 | - | - | Local LLM API |

---

## 🔧 Command-Line Access

### PostgreSQL (psql)
```powershell
docker exec -it threatlens-postgres psql -U admin -d threatlens
```

### Redis CLI
```powershell
docker exec -it threatlens-redis redis-cli
```

Common Redis commands:
```redis
PING                    # Test connection
KEYS *                  # List all keys
GET key_name           # Get value
SET key_name value     # Set value
FLUSHALL               # Clear all data (use carefully!)
```

### MinIO CLI (mc)
```powershell
docker exec -it threatlens-minio mc alias set local http://localhost:9000 minioadmin minioadmin123
docker exec -it threatlens-minio mc ls local
```

### Elasticsearch
```powershell
# Health check
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices

# Search
curl http://localhost:9200/your_index/_search
```

### Neo4j Cypher Shell
```powershell
docker exec -it threatlens-neo4j cypher-shell -u neo4j -p threatlens123
```

Example queries:
```cypher
MATCH (n) RETURN n LIMIT 10;              // Get 10 nodes
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 5;  // Get relationships
```

### Kafka Topics
```powershell
# List topics
docker exec -it threatlens-kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic
docker exec -it threatlens-kafka kafka-topics --create --topic test-topic --bootstrap-server localhost:9092

# Consume messages
docker exec -it threatlens-kafka kafka-console-consumer --topic correlated-incidents --bootstrap-server localhost:9092 --from-beginning
```

### Ollama
```powershell
# List models
docker exec -it threatlens-ollama ollama list

# Pull a model
docker exec -it threatlens-ollama ollama pull mistral:7b

# Run a query
docker exec -it threatlens-ollama ollama run mistral:7b "Explain what a SOC analyst does"
```

---

## 🐍 Python Access (from backend code)

### Redis
```python
import redis

# Using config from .env
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.set('test_key', 'test_value')
value = r.get('test_key')
```

### PostgreSQL
```python
from sqlalchemy import create_engine
from config import settings

engine = create_engine(settings.DATABASE_URL)
# Already configured in backend/database/postgres.py
```

### Elasticsearch
```python
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])
es.info()
```

### MinIO
```python
from minio import Minio

client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin123',
    secure=False
)
# Already configured in backend/services/evidence_service.py
```

---

## 📊 Monitoring & Health Checks

### Check All Docker Services
```powershell
docker ps
docker-compose ps  # From backend/ directory
```

### Service Health Endpoints
```powershell
# Backend health
curl http://localhost:8000/health

# Elasticsearch
curl http://localhost:9200/_cluster/health

# MinIO
curl http://localhost:9000/minio/health/live
```

### View Logs
```powershell
# All services
cd backend
docker-compose logs -f

# Specific service
docker logs -f threatlens-postgres
docker logs -f threatlens-redis
docker logs -f threatlens-kafka
```

### Resource Usage
```powershell
docker stats
```

---

## 🔒 Security Notes

### Development Environment
- ⚠️ These credentials are for **local development only**
- **Never commit** `.env` file to Git (already in .gitignore)
- **Never use these credentials** in production

### Production Deployment
When deploying to production:

1. **Change all passwords** to strong, unique values
2. **Use environment variables** or secret management (Azure Key Vault, AWS Secrets Manager, etc.)
3. **Enable TLS/SSL** for all services
4. **Configure firewalls** to restrict access
5. **Enable authentication** on Elasticsearch and Redis
6. **Use managed services** when possible (RDS, ElastiCache, etc.)

---

## 🛠️ Troubleshooting

### Can't connect to PostgreSQL
```powershell
# Check if container is running
docker ps | findstr postgres

# Check logs
docker logs threatlens-postgres

# Test connection
docker exec -it threatlens-postgres psql -U admin -d threatlens -c "SELECT version();"
```

### Redis not responding
```powershell
docker exec -it threatlens-redis redis-cli ping
# Should return: PONG
```

### MinIO access denied
- Check credentials in `.env` file match MinIO configuration
- Default: `minioadmin` / `minioadmin123`
- Access console: http://localhost:9001

### Elasticsearch yellow/red status
```powershell
curl http://localhost:9200/_cluster/health?pretty
# Single-node clusters are always yellow (expected)
```

### Neo4j authentication failed
- First login uses default password
- Change via browser at http://localhost:7474
- Update password in `.env` file

---

## 📝 Quick Reference

**Start Everything:**
```powershell
.\start.ps1
```

**Stop Everything:**
```powershell
.\stop.ps1
```

**View .env file:**
```powershell
cat backend\.env
```

**Edit .env file:**
```powershell
code backend\.env  # VS Code
notepad backend\.env  # Notepad
```

---

**Last Updated:** February 14, 2026  
**Environment:** Development (Local)
