import { useState, useEffect } from 'react'
import styles from './TopBar.module.css'

export default function TopBar() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [liveStatus, setLiveStatus] = useState(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        {liveStatus && (
          <div className={styles.liveIndicator}>
            <span className={`${styles.dot} pulse`}>●</span>
            LIVE
          </div>
        )}
      </div>

      <div className={styles.center}>
        <div className={styles.time}>
          {currentTime.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          })}
        </div>
        <div className={styles.date}>
          {currentTime.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          })}
        </div>
      </div>

      <div className={styles.right}>
        <button className={styles.actionBtn}>
          🔔 Alerts
        </button>
        <button className={styles.actionBtn}>
          ⚙️ Settings
        </button>
      </div>
    </header>
  )
}
