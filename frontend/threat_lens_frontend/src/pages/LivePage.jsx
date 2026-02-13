import styles from './LivePage.module.css'

export default function LivePage() {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>📹 Live Monitoring Dashboard</h1>
      
      <div className={styles.grid}>
        {/* Network Traffic */}
        <div className="card">
          <h3>🌐 Network Traffic</h3>
          <div className={styles.metric}>
            <span>Current: 45 MB/min</span>
            <span className={styles.normal}>Normal</span>
          </div>
          <p className={styles.placeholder}>Live chart visualization would go here</p>
        </div>

        {/* Login Attempts */}
        <div className="card">
          <h3>🔐 Login Attempts</h3>
          <div className={styles.metric}>
            <span>Success: 12 | Failed: 3</span>
            <span className={styles.normal}>Normal</span>
          </div>
          <p className={styles.placeholder}>Live heatmap would go here</p>
        </div>

        {/* Camera Zones */}
        <div className="card">
          <h3>📹 Camera Zones</h3>
          <div className={styles.zoneList}>
            {['Server Room', 'Lobby', 'Data Center', 'Office'].map(zone => (
              <div key={zone} className={styles.zone}>
                <span>{zone}</span>
                <span className={styles.statusOk}>🟢 CLEAR</span>
              </div>
            ))}
          </div>
        </div>

        {/* RF Devices */}
        <div className="card">
          <h3>📡 RF Device Monitor</h3>
          <div className={styles.metric}>
            <span>Known: 4 | Unknown: 0</span>
            <span className={styles.normal}>Normal</span>
          </div>
          <p className={styles.placeholder}>Device list would go here</p>
        </div>

        {/* File Events */}
        <div className="card">
          <h3>📁 File Modification Feed</h3>
          <div className={styles.eventList}>
            {['config.ini', 'database.db', 'access.log'].map(file => (
              <div key={file} className={styles.event}>
                <span>{file}</span>
                <span className={styles.eventTime}>2m ago</span>
              </div>
            ))}
          </div>
        </div>

        {/* Anomaly Meters */}
        <div className="card">
          <h3>📊 Anomaly Score Meters</h3>
          <div className={styles.meters}>
            {[
              { name: 'Network', score: 35 },
              { name: 'Camera', score: 42 },
              { name: 'RF', score: 28 },
              { name: 'Logs', score: 51 },
              { name: 'Files', score: 38 }
            ].map(meter => (
              <div key={meter.name} className={styles.meter}>
                <span>{meter.name}</span>
                <div className={styles.meterBar}>
                  <div
                    className={styles.meterFill}
                    style={{
                      width: `${meter.score}%`,
                      background: meter.score > 75 ? '#ef4444' : '#22c55e'
                    }}
                  />
                </div>
                <span>{meter.score}/100</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
