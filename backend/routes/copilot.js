import express from 'express';
import pool from '../config/database.js';

const router = express.Router();

// POST /api/copilot/query - Ask the SOC copilot a question
router.post('/query', async (req, res) => {
  try {
    const { question } = req.body;
    
    if (!question) {
      return res.status(400).json({ error: 'Question is required' });
    }
    
    // Simple keyword-based responses for demo
    const lowerQuestion = question.toLowerCase();
    let response = '';
    let supporting_incidents = [];
    
    if (lowerQuestion.includes('server room') || lowerQuestion.includes('last night')) {
      // Get the most recent critical incident
      const result = await pool.query(
        `SELECT * FROM incidents 
         WHERE severity = 'CRITICAL' AND zone = 'Server Room'
         ORDER BY timestamp DESC LIMIT 1`
      );
      
      if (result.rows.length > 0) {
        const incident = result.rows[0];
        supporting_incidents.push(incident.incident_id);
        
        response = `Between ${new Date(incident.timestamp).toLocaleTimeString()} and ${new Date(new Date(incident.timestamp).getTime() + 4 * 60000).toLocaleTimeString()}, ThreatLens detected a coordinated attack in the server room (${incident.incident_id}, risk ${incident.risk_score}/100). `;
        
        const events = incident.correlated_events;
        response += `An unauthorized person entered at ${new Date(events[0].timestamp).toLocaleTimeString()}. `;
        response += `${events.length} correlated events were detected. Evidence is blockchain-verified.`;
      } else {
        response = 'No recent critical incidents detected in the server room.';
      }
    } else if (lowerQuestion.includes('block') && lowerQuestion.includes('ip')) {
      // Get malicious IPs from IOCs
      const result = await pool.query(
        `SELECT DISTINCT value, incident_id, confidence 
         FROM iocs 
         WHERE ioc_type = 'ip' AND blocked = false AND confidence > 0.8
         ORDER BY confidence DESC LIMIT 5`
      );
      
      if (result.rows.length > 0) {
        response = 'Based on active incidents, block these IPs immediately:\n';
        result.rows.forEach((ioc, i) => {
          response += `\n${i + 1}. ${ioc.value} (confidence: ${(ioc.confidence * 100).toFixed(0)}%, incident: ${ioc.incident_id})`;
          supporting_incidents.push(ioc.incident_id);
        });
      } else {
        response = 'No high-confidence malicious IPs found in current incidents.';
      }
    } else if (lowerQuestion.includes('critical') || lowerQuestion.includes('today')) {
      const result = await pool.query(
        `SELECT incident_id, rule_name, risk_score, zone, timestamp 
         FROM incidents 
         WHERE severity = 'CRITICAL' AND status = 'open'
         AND timestamp > NOW() - INTERVAL '24 hours'
         ORDER BY risk_score DESC`
      );
      
      if (result.rows.length > 0) {
        response = `Found ${result.rows.length} critical incident(s) today:\n`;
        result.rows.forEach((inc, i) => {
          response += `\n${i + 1}. ${inc.incident_id}: ${inc.rule_name} (Risk: ${inc.risk_score}/100, Zone: ${inc.zone})`;
          supporting_incidents.push(inc.incident_id);
        });
      } else {
        response = 'No critical incidents detected today.';
      }
    } else {
      response = `I understand you're asking about "${question}". Based on current incident data, I can help you with:\n\n• Recent incident analysis\n• IP blocking recommendations\n• Critical alerts today\n• Evidence verification\n• Attack pattern analysis\n\nPlease ask a more specific question about these topics.`;
    }
    
    res.json({
      question,
      response,
      supporting_incidents: [...new Set(supporting_incidents)],
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error in copilot query:', error);
    res.status(500).json({ error: 'Copilot query failed' });
  }
});

export default router;
