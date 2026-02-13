import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// GET /api/incidents - List all incidents with filters
router.get('/', async (req, res) => {
  try {
    const { 
      page = 1, 
      limit = 20, 
      severity, 
      source, 
      min_risk, 
      status = 'open' 
    } = req.query;
    
    let query = 'SELECT * FROM incidents WHERE status = $1';
    const params = [status];
    let paramIndex = 2;
    
    if (severity) {
      query += ` AND severity = $${paramIndex}`;
      params.push(severity);
      paramIndex++;
    }
    
    if (min_risk) {
      query += ` AND risk_score >= $${paramIndex}`;
      params.push(parseInt(min_risk));
      paramIndex++;
    }
    
    if (source) {
      query += ` AND sources_involved @> $${paramIndex}::jsonb`;
      params.push(JSON.stringify([source]));
      paramIndex++;
    }
    
    query += ' ORDER BY risk_score DESC, timestamp DESC';
    
    const offset = (page - 1) * limit;
    query += ` LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(parseInt(limit), offset);
    
    const result = await pool.query(query, params);
    
    res.json({
      incidents: result.rows,
      page: parseInt(page),
      limit: parseInt(limit),
      total: result.rows.length
    });
  } catch (error) {
    console.error('Error fetching incidents:', error);
    res.status(500).json({ error: 'Failed to fetch incidents' });
  }
});

// GET /api/incidents/:id - Get single incident
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      'SELECT * FROM incidents WHERE incident_id = $1',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Incident not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching incident:', error);
    res.status(500).json({ error: 'Failed to fetch incident' });
  }
});

// GET /api/incidents/:id/timeline - Get incident timeline
router.get('/:id/timeline', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      'SELECT correlated_events, timestamp FROM incidents WHERE incident_id = $1',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Incident not found' });
    }
    
    const incident = result.rows[0];
    res.json({
      incident_id: id,
      events: incident.correlated_events,
      timeline_duration_minutes: incident.correlated_events.length * 2
    });
  } catch (error) {
    console.error('Error fetching timeline:', error);
    res.status(500).json({ error: 'Failed to fetch timeline' });
  }
});

// GET /api/incidents/:id/graph - Get attack graph
router.get('/:id/graph', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query(
      'SELECT correlated_events FROM incidents WHERE incident_id = $1',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Incident not found' });
    }
    
    const events = result.rows[0].correlated_events;
    const nodes = events.map((event, index) => ({
      id: event.event_id,
      label: event.source.toUpperCase(),
      source_type: event.source,
      score: event.score,
      timestamp: event.timestamp,
      description: event.description
    }));
    
    const edges = [];
    for (let i = 1; i < events.length; i++) {
      edges.push({
        source: events[i - 1].event_id,
        target: events[i].event_id,
        confidence: 0.85 + Math.random() * 0.14,
        relationship: 'leads_to'
      });
    }
    
    res.json({ nodes, edges });
  } catch (error) {
    console.error('Error fetching graph:', error);
    res.status(500).json({ error: 'Failed to fetch graph' });
  }
});

// PATCH /api/incidents/:id/status - Update incident status
router.patch('/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;
    
    const result = await pool.query(
      'UPDATE incidents SET status = $1 WHERE incident_id = $2 RETURNING *',
      [status, id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Incident not found' });
    }
    
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error updating status:', error);
    res.status(500).json({ error: 'Failed to update status' });
  }
});

export default router;
