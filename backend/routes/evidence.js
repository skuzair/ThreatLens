import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// GET /api/evidence/:incident_id - Get all evidence for an incident
router.get('/:incident_id', async (req, res) => {
  try {
    const { incident_id } = req.params;
    const result = await pool.query(
      'SELECT * FROM evidence WHERE incident_id = $1 ORDER BY capture_timestamp DESC',
      [incident_id]
    );
    
    res.json({
      incident_id,
      evidence: result.rows,
      total_count: result.rows.length
    });
  } catch (error) {
    console.error('Error fetching evidence:', error);
    res.status(500).json({ error: 'Failed to fetch evidence' });
  }
});

// GET /api/evidence/:incident_id/verify - Verify evidence integrity
router.get('/:incident_id/verify', async (req, res) => {
  try {
    const { incident_id } = req.params;
    const result = await pool.query(
      'SELECT evidence_id, sha256_hash, blockchain_tx_hash, blockchain_block_number, verified FROM evidence WHERE incident_id = $1',
      [incident_id]
    );
    
    const verification_results = result.rows.map(evidence => ({
      evidence_id: evidence.evidence_id,
      hash: evidence.sha256_hash,
      blockchain_verified: evidence.verified,
      tx_hash: evidence.blockchain_tx_hash,
      block_number: evidence.blockchain_block_number,
      polygonscan_url: `https://mumbai.polygonscan.com/tx/${evidence.blockchain_tx_hash}`
    }));
    
    res.json({
      incident_id,
      all_verified: result.rows.every(e => e.verified),
      evidence: verification_results
    });
  } catch (error) {
    console.error('Error verifying evidence:', error);
    res.status(500).json({ error: 'Failed to verify evidence' });
  }
});

export default router;
