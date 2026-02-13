import { Link, useLocation } from 'react-router-dom'
import styles from './Sidebar.module.css'

const menuItems = [
  { path: '/', icon: '🚨', label: 'Alerts' },
  { path: '/live', icon: '📹', label: 'Live Monitor' },
  { path: '/copilot', icon: '🤖', label: 'Copilot' },
  { path: '/threats', icon: '🧬', label: 'Threats' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.icon}>🛡️</span>
        <span className={styles.name}>ThreatLens AI</span>
      </div>

      <nav className={styles.nav}>
        {menuItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            className={location.pathname === item.path ? styles.active : ''}
          >
            <span className={styles.itemIcon}>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className={styles.systemHealth}>
        <div className={styles.healthTitle}>SYSTEM HEALTH</div>
        {['Network', 'Camera', 'RF', 'Logs', 'Files'].map(source => (
          <div key={source} className={styles.healthItem}>
            <span>{source}</span>
            <span className={styles.statusDot}>✅</span>
          </div>
        ))}
      </div>
    </aside>
  )
}
