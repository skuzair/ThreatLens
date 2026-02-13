import { useState, useEffect } from 'react'
import AlertCard from '../components/alerts/AlertCard'
import { incidentsAPI } from '../services/api'
import { alertsWebSocket } from '../services/websocket'
import styles from './AlertsPage.module.css'

const FILTER_SEVERITIES = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const FILTER_SOURCES = ['All', 'camera', 'network', 'logs', 'rf', 'file']

export default function AlertsPage() {
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState('All')
  const [sourceFilter, setSourceFilter] = useState('All')
  const [stats, setStats] = useState(null)

  useEffect(() => {
    loadIncidents()
    loadStats()
    
    // Connect to WebSocket for real-time updates
    alertsWebSocket.connect()
    const unsubscribe = alertsWebSocket.subscribe((message) => {
      if (message.type === 'new_incident') {
        setIncidents(prev => [message.data, ...prev])
      }
    })

    return () => {
      unsubscribe()
    }
  }, [])

  useEffect(() => {
    loadIncidents()
  }, [severityFilter, sourceFilter])

  async function loadIncidents() {
    try {
      setLoading(true)
      const params = {
        page: 1,
        limit: 20,
        status: 'open'
      }
      
      if (severityFilter !== 'All') {
        params.severity = severityFilter
      }
      if (sourceFilter !== 'All') {
        params.source = sourceFilter
      }

      const data = await incidentsAPI.getAll(params)
      setIncidents(data.incidents || [])
    } catch (error) {
      console.error('Error loading incidents:', error)
      setIncidents([])
    } finally {
      setLoading(false)
    }
  }

  async function loadStats() {
    try {
      const data = await incidentsAPI.getStats()
      setStats(data)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>🚨 Alert Feed</h1>
        {stats && (
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statLabel}>Open</span>
              <span className={styles.statValue}>{stats.total_open || 0}</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statLabel}>Critical</span>
              <span className={styles.statValue} style={{ color: '#ef4444' }}>
                {stats.by_severity?.CRITICAL || 0}
              </span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statLabel}>High</span>
              <span className={styles.statValue} style={{ color: '#f97316' }}>
                {stats.by_severity?.HIGH || 0}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className={styles.filters}>
        <div className={styles.filterGroup}>
          <span className={styles.filterLabel}>Severity:</span>
          {FILTER_SEVERITIES.map(sev => (
            <button
              key={sev}
              className={severityFilter === sev ? styles.filterActive : ''}
              onClick={() => setSeverityFilter(sev)}
            >
              {sev}
            </button>
          ))}
        </div>
        <div className={styles.filterGroup}>
          <span className={styles.filterLabel}>Source:</span>
          {FILTER_SOURCES.map(src => (
            <button
              key={src}
              className={sourceFilter === src ? styles.filterActive : ''}
              onClick={() => setSourceFilter(src)}
            >
              {src}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.feed}>
        {loading ? (
          <div className={styles.loading}>
            <div className="spinner"></div>
            <div>Loading incidents...</div>
          </div>
        ) : incidents.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>✅</div>
            <div>No incidents matching filters</div>
          </div>
        ) : (
          incidents.map(incident => (
            <AlertCard key={incident.incident_id} incident={incident} />
          ))
        )}
      </div>
    </div>
  )
}
