import express from 'express';

const router = express.Router();

// GET /api/live/network - Get current network stats
router.get('/network', (req, res) => {
  const baseline_mb = 45;
  const current_mb = 45 + Math.random() * 200; // Simulate variance
  const is_alert = current_mb > baseline_mb * 5;
  
  res.json({
    baseline_mb_per_hour: baseline_mb,
    current_mb_per_hour: Math.round(current_mb * 10) / 10,
    is_alert,
    timestamp: new Date().toISOString()
  });
});

// GET /api/live/cameras - Get camera zone status
router.get('/cameras', (req, res) => {
  const zones = [
    { name: 'Server Room', status: Math.random() > 0.8 ? 'ALERT' : 'CLEAR', detection: Math.random() > 0.8 ? 'Person detected' : null },
    { name: 'Lobby', status: 'CLEAR', detection: null },
    { name: 'Data Center', status: 'CLEAR', detection: null },
    { name: 'Office', status: 'CLEAR', detection: null }
  ];
  
  res.json({ zones, timestamp: new Date().toISOString() });
});

// GET /api/live/logins - Get login attempt stats
router.get('/logins', (req, res) => {
  const success_count = Math.floor(Math.random() * 20) + 5;
  const failed_count = Math.floor(Math.random() * 50) + 10;
  const threshold = 5;
  
  res.json({
    success_count,
    failed_count,
    threshold_per_minute: threshold,
    is_alert: failed_count / 60 > threshold,
    timestamp: new Date().toISOString()
  });
});

// GET /api/live/rf - Get RF device monitor data
router.get('/rf', (req, res) => {
  const known_devices = 4;
  const unknown_devices = Math.random() > 0.7 ? 1 : 0;
  
  res.json({
    known_devices,
    unknown_devices,
    is_alert: unknown_devices > 0,
    devices: unknown_devices > 0 ? [{
      mac: 'AA:BB:CC:DD:EE:FF',
      type: 'WiFi',
      signal: '-45dBm',
      zone: 'Server Room'
    }] : [],
    timestamp: new Date().toISOString()
  });
});

// GET /api/live/files - Get file modification feed
router.get('/files', (req, res) => {
  const is_mass_modification = Math.random() > 0.85;
  const modifications = is_mass_modification ? 
    Array.from({ length: 5 }, (_, i) => ({
      timestamp: new Date(Date.now() - i * 1000).toISOString(),
      path: '/var/db/*.sql',
      operation: 'encrypt',
      is_alert: true
    })) :
    [{
      timestamp: new Date().toISOString(),
      path: '/home/user/document.txt',
      operation: 'write',
      is_alert: false
    }];
  
  res.json({
    modifications,
    is_alert: is_mass_modification,
    timestamp: new Date().toISOString()
  });
});

// GET /api/live/anomaly-scores - Get current anomaly scores
router.get('/anomaly-scores', (req, res) => {
  res.json({
    network: Math.floor(Math.random() * 30) + 70,
    camera: Math.floor(Math.random() * 30) + 70,
    rf: Math.floor(Math.random() * 30) + 70,
    logs: Math.floor(Math.random() * 30) + 60,
    files: Math.floor(Math.random() * 30) + 70,
    timestamp: new Date().toISOString()
  });
});

export default router;
