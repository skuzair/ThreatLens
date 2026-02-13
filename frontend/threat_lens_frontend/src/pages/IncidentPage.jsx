import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { incidentsAPI } from '../services/api'
import styles from './IncidentPage.module.css'

export default function IncidentPage() {
  const { id } = useParams()
  const [incident, setIncident] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadIncident()
    loadTimeline()
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
        {['overview', 'timeline', 'evidence', 'xai'].map(tab => (
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
            <p className={styles.placeholder}>
              Evidence gallery would show video clips, log snippets, network captures, etc.
            </p>
          </div>
        )}

        {activeTab === 'xai' && (
          <div>
            <h3>Explainable AI Analysis</h3>
            {incident.nlg_explanation ? (
              <div className={styles.explanation}>
                <pre>{JSON.stringify(incident.nlg_explanation, null, 2)}</pre>
              </div>
            ) : (
              <p className={styles.placeholder}>
                XAI analysis in progress...
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
