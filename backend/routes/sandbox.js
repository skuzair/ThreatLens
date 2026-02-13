import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// GET /api/sandbox/:incident_id - Get sandbox results for an incident
router.get('/:incident_id', async (req, res) => {
  try {
    const { incident_id } = req.params;
    const result = await pool.query(
      'SELECT * FROM sandbox_results WHERE incident_id = $1',
      [incident_id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'No sandbox results found' });
    }
    
    // Add screenshot URLs
    const sandboxResult = result.rows[0];
    sandboxResult.screenshot_sequence = Array.from(
      { length: sandboxResult.screenshot_count },
      (_, i) => ({
        frame: i,
        timestamp_seconds: i * 2,
        url: `/api/sandbox/screenshots/${incident_id}/${i}.png`
      })
    );
    
    res.json(sandboxResult);
  } catch (error) {
    console.error('Error fetching sandbox results:', error);
    res.status(500).json({ error: 'Failed to fetch sandbox results' });
  }
});

export default router;
