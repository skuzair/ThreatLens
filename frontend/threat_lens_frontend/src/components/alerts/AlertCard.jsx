import { useNavigate } from 'react-router-dom'
import styles from './AlertCard.module.css'

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: '#450a0a', icon: '🔴', border: '#7f1d1d' },
  HIGH: { color: '#f97316', bg: '#431407', icon: '🟠', border: '#7c2d12' },
  MEDIUM: { color: '#eab308', bg: '#422006', icon: '🟡', border: '#713f12' },
  LOW: { color: '#22c55e', bg: '#052e16', icon: '🟢', border: '#14532d' }
}

const SOURCE_ICONS = {
  camera: '📹',
  logs: '💻',
  network: '🌐',
  rf: '📡',
  file: '📁'
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export default function AlertCard({ incident }) {
  const navigate = useNavigate()
  const config = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG.MEDIUM

  return (
    <div
      className={styles.card}
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`
      }}
      onClick={() => navigate(`/incident/${incident.incident_id}`)}
    >
      {/* Header row */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.severityIcon}>{config.icon}</span>
          <div>
            <span className={styles.severity} style={{ color: config.color }}>
              {incident.severity}
            </span>
            <span className={styles.incidentId}>
              {incident.incident_id}
            </span>
          </div>
        </div>
        <div
          className={styles.riskBadge}
          style={{ background: config.color }}
        >
          {incident.risk_score}/100
        </div>
      </div>

      {/* Incident name */}
      <div className={styles.title}>
        {incident.rule_name}
      </div>

      {/* Source icons */}
      <div className={styles.sources}>
        {incident.sources_involved?.map(source => (
          <span key={source} className={styles.source}>
            {SOURCE_ICONS[source]} {source}
          </span>
        ))}
      </div>

      {/* Meta info */}
      <div className={styles.meta}>
        <span>🕐 {formatTime(incident.timestamp)}</span>
        <span>📍 {incident.zone || 'Unknown'}</span>
        <span>🔗 {incident.sources_involved?.length || 0} sources</span>
      </div>

      {/* Intent badge */}
      <div className={styles.intent}>
        <span className={styles.intentLabel}>Intent:</span>
        <span className={styles.intentValue}>
          {incident.intent_primary?.replace(/_/g, ' ') || 'Unknown'}
        </span>
        <span className={styles.confidence}>
          {Math.round((incident.intent_confidence || 0) * 100)}% confidence
        </span>
      </div>

      {/* Action buttons */}
      <div className={styles.actions} onClick={e => e.stopPropagation()}>
        <button onClick={() => navigate(`/incident/${incident.incident_id}`)}>
          View Details
        </button>
        <button className="danger">
          🔒 Isolate
        </button>
        <button className="danger">
          🚫 Block
        </button>
      </div>
    </div>
  )
}
