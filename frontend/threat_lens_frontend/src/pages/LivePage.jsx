import { useState, useEffect } from 'react'
import styles from './LivePage.module.css'
import NetworkChart from '../components/live/NetworkChart'
import LoginHeatmap from '../components/live/LoginHeatmap'
import AnomalyMeters from '../components/live/AnomalyMeters'

export default function LivePage() {
  const [websocketData, setWebsocketData] = useState(null)

  // Simulate WebSocket updates every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setWebsocketData([{
        timestamp: new Date().toISOString(),
        bytes_per_minute: Math.random() * 200000000,
        successful_logins: Math.floor(Math.random() * 15),
        failed_logins: Math.floor(Math.random() * 50)
      }])
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>📹 Live Monitoring Dashboard</h1>
      
      <div className={styles.grid}>
        {/* Network Traffic */}
        <div>
          <NetworkChart websocketData={websocketData} />
        </div>

        {/* Login Attempts */}
        <div>
          <LoginHeatmap websocketData={websocketData} />
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
        <div>
          <AnomalyMeters websocketData={{
            network: 87,
            camera: 92,
            rf: 85,
            logs: 76,
            files: 91
          }} />
        </div>
      </div>
    </div>
  )
}
