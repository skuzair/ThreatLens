import pg from 'pg';
const { Pool } = pg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://admin:threatlens123@localhost:5432/threatlens',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Initialize database tables
export async function initDatabase() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS incidents (
        incident_id VARCHAR(50) PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT NOW(),
        risk_score INTEGER,
        severity VARCHAR(20),
        rule_name VARCHAR(255),
        sources_involved JSONB,
        correlated_events JSONB,
        intent_primary VARCHAR(100),
        intent_confidence DECIMAL(5,2),
        mitre_ttps JSONB,
        current_attack_stage VARCHAR(100),
        predicted_next_move JSONB,
        nlg_explanation JSONB,
        status VARCHAR(20) DEFAULT 'open',
        zone VARCHAR(100)
      );

      CREATE TABLE IF NOT EXISTS evidence (
        evidence_id VARCHAR(50) PRIMARY KEY,
        incident_id VARCHAR(50),
        capture_timestamp TIMESTAMP,
        evidence_type VARCHAR(50),
        file_path VARCHAR(500),
        sha256_hash VARCHAR(64),
        blockchain_tx_hash VARCHAR(100),
        blockchain_block_number INTEGER,
        verified BOOLEAN DEFAULT true,
        metadata JSONB
      );

      CREATE TABLE IF NOT EXISTS sandbox_results (
        result_id VARCHAR(50) PRIMARY KEY,
        incident_id VARCHAR(50),
        file_hash VARCHAR(64),
        verdict VARCHAR(20),
        confidence_score INTEGER,
        behavioral_summary JSONB,
        extracted_iocs JSONB,
        screenshot_count INTEGER,
        mitre_behaviors JSONB,
        detonation_timestamp TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS iocs (
        ioc_id VARCHAR(50) PRIMARY KEY,
        incident_id VARCHAR(50),
        ioc_type VARCHAR(20),
        value VARCHAR(500),
        confidence DECIMAL(5,2),
        source VARCHAR(50),
        first_seen TIMESTAMP DEFAULT NOW(),
        times_seen INTEGER DEFAULT 1,
        blocked BOOLEAN DEFAULT false
      );

      CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
      CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
      CREATE INDEX IF NOT EXISTS idx_incidents_risk ON incidents(risk_score DESC);
    `);
    console.log('✅ Database tables initialized');
  } catch (error) {
    console.error('❌ Database initialization error:', error);
  } finally {
    client.release();
  }
}

export default pool;
