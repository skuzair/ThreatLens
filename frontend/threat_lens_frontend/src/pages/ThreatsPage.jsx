import styles from './ThreatsPage.module.css'

export default function ThreatsPage() {
  const mitreData = [
    { tactic: 'Initial Access', count: 3 },
    { tactic: 'Execution', count: 5 },
    { tactic: 'Persistence', count: 2 },
    { tactic: 'Privilege Escalation', count: 4 },
    { tactic: 'Defense Evasion', count: 3 },
    { tactic: 'Credential Access', count: 2 },
    { tactic: 'Discovery', count: 1 },
    { tactic: 'Lateral Movement', count: 2 },
    { tactic: 'Collection', count: 1 },
    { tactic: 'Exfiltration', count: 4 },
    { tactic: 'Impact', count: 3 }
  ]

  const mockIOCs = [
    { type: 'IP', value: '203.0.113.5', threat: 'C2 Server', level: 'critical' },
    { type: 'Domain', value: 'evil-c2.ru', threat: 'Command & Control', level: 'critical' },
    { type: 'Hash', value: 'deadbeef...', threat: 'Malware', level: 'high' }
  ]

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>🧬 Threat Intelligence</h1>

      <div className={styles.grid}>
        {/* MITRE ATT&CK Heatmap */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3>MITRE ATT&CK Heatmap</h3>
          <div className={styles.heatmap}>
            {mitreData.map(item => (
              <div key={item.tactic} className={styles.heatmapItem}>
                <span className={styles.tacticName}>{item.tactic}</span>
                <div className={styles.heatmapBar}>
                  <div
                    className={styles.heatmapFill}
                    style={{
                      width: `${(item.count / 5) * 100}%`,
                      background: item.count > 3 ? '#ef4444' : '#f97316'
                    }}
                  />
                </div>
                <span className={styles.tacticCount}>{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Active IOCs */}
        <div className="card">
          <h3>🚨 Active IOCs</h3>
          <div className={styles.iocList}>
            {mockIOCs.map((ioc, idx) => (
              <div key={idx} className={styles.ioc}>
                <div className={styles.iocHeader}>
                  <span className={`badge ${ioc.level}`}>{ioc.type}</span>
                  <span className={styles.iocThreat}>{ioc.threat}</span>
                </div>
                <div className={styles.iocValue}>{ioc.value}</div>
                <div className={styles.iocActions}>
                  <button className="danger">Block</button>
                  <button>Add to Watchlist</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Attack Intent Distribution */}
        <div className="card">
          <h3>🎯 Attack Intent Distribution</h3>
          <div className={styles.intentList}>
            {[
              { intent: 'Data Exfiltration', percent: 40 },
              { intent: 'Ransomware', percent: 30 },
              { intent: 'Reconnaissance', percent: 20 },
              { intent: 'Insider Threat', percent: 10 }
            ].map(item => (
              <div key={item.intent} className={styles.intentItem}>
                <span>{item.intent}</span>
                <div className={styles.intentBar}>
                  <div
                    className={styles.intentFill}
                    style={{ width: `${item.percent}%` }}
                  />
                </div>
                <span>{item.percent}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Threat Origins */}
        <div className="card">
          <h3>🌍 Threat Geographic Origins</h3>
          <div className={styles.origins}>
            {[
              { country: 'Russia', code: 'RU', count: 5 },
              { country: 'China', code: 'CN', count: 3 },
              { country: 'United States', code: 'US', count: 2 },
              { country: 'Unknown', code: '??', count: 1 }
            ].map(origin => (
              <div key={origin.code} className={styles.origin}>
                <span className={styles.countryCode}>{origin.code}</span>
                <span>{origin.country}</span>
                <span className={styles.originCount}>{origin.count} threats</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
