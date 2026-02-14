import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { incidentsAPI } from '../services/api'
import styles from './IncidentPage.module.css'
import AttackGraph from '../components/incident/AttackGraph'
import VideoPlayer from '../components/evidence/VideoPlayer'
import SHAPChart from '../components/xai/SHAPChart'

export default function IncidentPage() {
  const { id } = useParams()
  const [incident, setIncident] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadIncident()
    loadTimeline()
    loadGraphData()
  }, [id])

  async function loadIncident() {
    try {
      setLoading(true)
      const data = await incidentsAPI.getById(id)
      setIncident(data)
    } catch (error) {
      console.error('Error loading incident:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadTimeline() {
    try {
      const data = await incidentsAPI.getTimeline(id)
      setTimeline(data)
    } catch (error) {
      console.error('Error loading timeline:', error)
    }
  }

  async function loadGraphData() {
    try {
      const data = await incidentsAPI.getGraph(id)
      setGraphData(data)
    } catch (error) {
      console.error('Error loading graph:', error)
      // Fallback to demo data
      setGraphData({
        nodes: [
          { id: '1', source_type: 'camera', score: 92, label: 'Zone Entry', timestamp: '14:32:10' },
          { id: '2', source_type: 'logs', score: 85, label: 'Failed Login', timestamp: '14:32:45' },
          { id: '3', source_type: 'network', score: 78, label: 'Port Scan', timestamp: '14:33:20' },
          { id: '4', source_type: 'rf', score: 88, label: 'Device Beacon', timestamp: '14:33:55' },
          { id: '5', source_type: 'file', score: 95, label: 'File Modified', timestamp: '14:34:30' }
        ],
        edges: [
          { source: '1', target: '2', confidence: 0.87 },
          { source: '2', target: '3', confidence: 0.92 },
          { source: '3', target: '4', confidence: 0.75 },
          { source: '4', target: '5', confidence: 0.89 }
        ]
      })
    }
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className="spinner"></div>
        <div>Loading incident details...</div>
      </div>
    )
  }

  if (!incident) {
    return <div className={styles.empty}>Incident not found</div>
  }

  const getSeverityColor = () => {
    const colors = {
      CRITICAL: '#ef4444',
      HIGH: '#f97316',
      MEDIUM: '#eab308',
      LOW: '#22c55e'
    }
    return colors[incident.severity] || colors.MEDIUM
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header} style={{ borderLeftColor: getSeverityColor() }}>
        <div className={styles.headerTop}>
          <h1>{incident.rule_name}</h1>
          <div className={styles.riskScore} style={{ background: getSeverityColor() }}>
            {incident.risk_score}/100
          </div>
        </div>
        <div className={styles.headerMeta}>
          <span className="badge" style={{ background: getSeverityColor() }}>
            {incident.severity}
          </span>
          <span>ID: {incident.incident_id}</span>
          <span>📍 {incident.zone}</span>
          <span>🕐 {new Date(incident.timestamp).toLocaleString()}</span>
        </div>
        <div className={styles.intent}>
          <strong>Intent:</strong> {incident.intent_primary?.replace(/_/g, ' ')}
          <span className={styles.confidence}>
            ({Math.round(incident.intent_confidence * 100)}% confidence)
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        {['overview', 'graph', 'timeline', 'evidence', 'xai'].map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? styles.tabActive : ''}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className={styles.tabContent}>
        {activeTab === 'overview' && (
          <div>
            <h3>Correlated Sources</h3>
            <div className={styles.sources}>
              {incident.sources_involved?.map(source => (
                <div key={source} className="badge">
                  {source}
                </div>
              ))}
            </div>

            <h3>MITRE ATT&CK Techniques</h3>
            <div className={styles.techniques}>
              {incident.mitre_ttps?.map(ttp => (
                <div key={ttp} className={styles.technique}>
                  {ttp}
                </div>
              ))}
            </div>

            <h3>Current Status</h3>
            <div className={styles.statusGrid}>
              <div className={styles.statusItem}>
                <span>Evidence Captured:</span>
                <strong>{incident.evidence_captured ? '✅' : '⏳'}</strong>
              </div>
              <div className={styles.statusItem}>
                <span>Sandbox Triggered:</span>
                <strong>{incident.sandbox_triggered ? '✅' : '⏳'}</strong>
              </div>
              <div className={styles.statusItem}>
                <span>Blockchain Anchored:</span>
                <strong>{incident.blockchain_anchored ? '✅' : '⏳'}</strong>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'graph' && (
          <div>
            <h3>Attack Correlation Graph</h3>
            {graphData ? (
              <AttackGraph graphData={graphData} />
            ) : (
              <p className={styles.placeholder}>Loading graph visualization...</p>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div>
            <h3>Attack Timeline</h3>
            <div className={styles.timeline}>
              {timeline.map((event, idx) => (
                <div key={event.event_id} className={styles.timelineEvent}>
                  <div className={styles.timelineDot}></div>
                  <div className={styles.timelineContent}>
                    <div className={styles.timelineTime}>
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <div className={styles.timelineTitle}>
                      {event.source_type.toUpperCase()} | Score: {event.score}
                    </div>
                    <div className={styles.timelineDesc}>
                      {event.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'evidence' && (
          <div>
            <h3>Evidence Files</h3>
            <VideoPlayer 
              videoUrl={incident.evidence_video_url || 'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4'}
              evidenceName={`Evidence_${incident.incident_id}.mp4`}
              timestamp={incident.timestamp}
            />
            <div style={{ marginTop: '16px' }}>
              <p style={{ color: '#64748b', fontSize: '13px' }}>
                Additional evidence files (network captures, log files) can be accessed via the Evidence API.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'xai' && (
          <div>
            <h3>Explainable AI Analysis</h3>
            {incident.nlg_explanation?.shap_values ? (
              <SHAPChart 
                shapData={{
                  features: incident.nlg_explanation.shap_values.features || incident.nlg_explanation.features || [
                    'camera_movement_detected',
                    'failed_login_count',
                    'network_traffic_spike',
                    'rf_signal_strength',
                    'file_access_unauthorized',
                    'time_of_day_unusual',
                    'user_behavior_anomaly',
                    'geolocation_mismatch'
                  ],
                  values: incident.nlg_explanation.shap_values.values || incident.nlg_explanation.values || [
                    0.234, 0.189, 0.156, 0.142, 0.098, -0.045, -0.078, -0.092
                  ],
                  base_value: incident.nlg_explanation.shap_values.base_value || incident.nlg_explanation.base_value || 0.5
                }}
                incidentId={incident.incident_id}
              />
            ) : (
              <SHAPChart 
                shapData={{
                  features: [
                    'camera_movement_detected',
                    'failed_login_count',
                    'network_traffic_spike',
                    'rf_signal_strength',
                    'file_access_unauthorized',
                    'time_of_day_unusual',
                    'user_behavior_anomaly',
                    'geolocation_mismatch'
                  ],
                  values: [0.234, 0.189, 0.156, 0.142, 0.098, -0.045, -0.078, -0.092],
                  base_value: 0.5
                }}
                incidentId={incident.incident_id}
              />
            )}
            
            {incident.nlg_explanation?.natural_language && (
              <div style={{
                marginTop: '16px',
                background: '#1a2233',
                borderRadius: '8px',
                padding: '16px',
                border: '1px solid #1e2d45'
              }}>
                <h4 style={{ color: '#e2e8f0', marginBottom: '8px' }}>Natural Language Explanation</h4>
                <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
                  {incident.nlg_explanation.natural_language}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
