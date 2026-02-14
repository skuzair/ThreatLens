export default function AnomalyMeters({ websocketData }) {
  // Use websocket data or demo values
  const scores = websocketData || {
    network: 87,
    camera: 92,
    rf: 85,
    logs: 76,
    files: 91
  }

  const getColor = (score) => {
    if (score >= 90) return '#ef4444'  // Critical
    if (score >= 75) return '#f97316'  // High
    if (score >= 50) return '#eab308'  // Medium
    return '#22c55e'  // Low
  }

  const getLabel = (score) => {
    if (score >= 90) return 'CRITICAL'
    if (score >= 75) return 'HIGH'
    if (score >= 50) return 'MEDIUM'
    return 'LOW'
  }

  const sources = [
    { name: 'Network', key: 'network', icon: '🌐', score: scores.network },
    { name: 'Camera', key: 'camera', icon: '📹', score: scores.camera },
    { name: 'RF Devices', key: 'rf', icon: '📡', score: scores.rf },
    { name: 'Logs', key: 'logs', icon: '💻', score: scores.logs },
    { name: 'Files', key: 'files', icon: '📁', score: scores.files }
  ]

  return (
    <div style={{ 
      background: '#1a2233', 
      borderRadius: '8px', 
      padding: '16px',
      border: '1px solid #1e2d45'
    }}>
      <h3 style={{ 
        color: '#e2e8f0', 
        marginBottom: '16px',
        fontSize: '16px',
        fontWeight: '600'
      }}>
        📊 Anomaly Score Meters
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {sources.map(source => (
          <div key={source.key}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '6px'
            }}>
              <span style={{ 
                color: '#e2e8f0', 
                fontSize: '13px',
                fontWeight: '500'
              }}>
                {source.icon} {source.name}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ 
                  color: getColor(source.score), 
                  fontSize: '18px',
                  fontWeight: 'bold'
                }}>
                  {source.score}
                </span>
                <span style={{ 
                  fontSize: '10px',
                  color: getColor(source.score),
                  background: `${getColor(source.score)}20`,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontWeight: 'bold'
                }}>
                  {getLabel(source.score)}
                </span>
              </div>
            </div>
            
            <div style={{ 
              width: '100%', 
              height: '8px', 
              background: '#0a0e1a', 
              borderRadius: '4px',
              overflow: 'hidden',
              position: 'relative'
            }}>
              <div style={{ 
                width: `${source.score}%`, 
                height: '100%', 
                background: `linear-gradient(90deg, ${getColor(source.score)}80, ${getColor(source.score)})`,
                borderRadius: '4px',
                transition: 'width 0.5s ease',
                boxShadow: source.score >= 75 ? `0 0 8px ${getColor(source.score)}` : 'none'
              }} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ 
        marginTop: '16px',
        padding: '12px',
        background: '#0a0e1a',
        borderRadius: '4px',
        fontSize: '11px',
        color: '#64748b',
        textAlign: 'center'
      }}>
        Average Risk Score: <span style={{ 
          color: getColor(sources.reduce((sum, s) => sum + s.score, 0) / sources.length),
          fontWeight: 'bold',
          fontSize: '13px'
        }}>
          {Math.round(sources.reduce((sum, s) => sum + s.score, 0) / sources.length)}/100
        </span>
      </div>
    </div>
  )
}
