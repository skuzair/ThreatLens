import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// GET /api/iocs - Get all IOCs
router.get('/', async (req, res) => {
  try {
    const { incident_id, ioc_type, blocked } = req.query;
    
    let query = 'SELECT * FROM iocs WHERE 1=1';
    const params = [];
    let paramIndex = 1;
    
    if (incident_id) {
      query += ` AND incident_id = $${paramIndex}`;
      params.push(incident_id);
      paramIndex++;
    }
    
    if (ioc_type) {
      query += ` AND ioc_type = $${paramIndex}`;
      params.push(ioc_type);
      paramIndex++;
    }
    
    if (blocked !== undefined) {
      query += ` AND blocked = $${paramIndex}`;
      params.push(blocked === 'true');
      paramIndex++;
    }
    
    query += ' ORDER BY confidence DESC, first_seen DESC';
    
    const result = await pool.query(query, params);
    res.json({ iocs: result.rows });
  } catch (error) {
    console.error('Error fetching IOCs:', error);
    res.status(500).json({ error: 'Failed to fetch IOCs' });
  }
});

// POST /api/iocs/:id/block - Block an IOC
router.post('/:id/block', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      'UPDATE iocs SET blocked = true WHERE ioc_id = $1 RETURNING *',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'IOC not found' });
    }
    
    res.json({
      success: true,
      ioc: result.rows[0],
      message: `IOC ${result.rows[0].value} has been blocked`
    });
  } catch (error) {
    console.error('Error blocking IOC:', error);
    res.status(500).json({ error: 'Failed to block IOC' });
  }
});

export default router;
