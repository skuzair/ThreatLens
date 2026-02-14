import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function NetworkChart({ websocketData }) {
  const [data, setData] = useState([])
  const BASELINE_MB = 45

  useEffect(() => {
    if (websocketData && websocketData.length > 0) {
      const latest = websocketData[0]
      const newPoint = {
        time: new Date(latest.timestamp).toLocaleTimeString('en-US', { 
          hour12: false, 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        volume_mb: (latest.bytes_per_minute || Math.random() * 2000) / 1000000,
        baseline: BASELINE_MB
      }
      
      setData(prev => [...prev.slice(-29), newPoint])  // Keep last 30 points
    } else {
      // Demo data for testing
      const now = new Date()
      setData(prev => {
        if (prev.length === 0) {
          // Initialize with mock data
          return Array.from({ length: 30 }, (_, i) => ({
            time: new Date(now - (29 - i) * 2000).toLocaleTimeString('en-US', { 
              hour12: false, 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            volume_mb: 30 + Math.random() * 100,
            baseline: BASELINE_MB
          }))
        }
        return prev
      })
    }
  }, [websocketData])

  const currentVolume = data[data.length - 1]?.volume_mb || 0
  const isAnomalous = currentVolume > BASELINE_MB * 5

  return (
    <div style={{ 
      background: '#1a2233', 
      borderRadius: '8px', 
      padding: '16px',
      border: '1px solid #1e2d45'
    }}>
      <h3 style={{ 
        color: '#e2e8f0', 
        marginBottom: '12px',
        fontSize: '16px',
        fontWeight: '600'
      }}>
        🌐 Network Traffic (Live)
      </h3>
      
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
          <XAxis 
            dataKey="time" 
            stroke="#64748b" 
            tick={{ fontSize: 10, fill: '#64748b' }}            
            tickLine={{ stroke: '#1e2d45' }}
          />
          <YAxis 
            stroke="#64748b" 
            tick={{ fontSize: 10, fill: '#64748b' }}
            tickLine={{ stroke: '#1e2d45' }}
            label={{ value: 'MB/min', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#64748b' } }}
          />
          <Tooltip
            contentStyle={{ 
              background: '#0a0e1a', 
              border: '1px solid #1e2d45',
              borderRadius: '4px',
              fontSize: '12px'
            }}
            labelStyle={{ color: '#94a3b8' }}
          />
          <ReferenceLine 
            y={BASELINE_MB} 
            stroke="#22c55e" 
            strokeDasharray="4 4"
            label={{ value: 'Baseline', position: 'right', fill: '#22c55e', fontSize: 10 }}
          />
          <Line
            type="monotone"
            dataKey="volume_mb"
            stroke={isAnomalous ? "#ef4444" : "#3b82f6"}
            dot={false}
            strokeWidth={2}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        fontSize: '12px', 
        marginTop: '8px',
        padding: '8px',
        background: '#0a0e1a',
        borderRadius: '4px'
      }}>
        <span style={{ color: '#64748b' }}>
          Baseline: <span style={{ color: '#22c55e', fontWeight: 'bold' }}>{BASELINE_MB} MB/min</span>
        </span>
        <span style={{ color: '#64748b' }}>
          Current: <span style={{ 
            color: isAnomalous ? '#ef4444' : '#22c55e', 
            fontWeight: 'bold' 
          }}>
            {currentVolume.toFixed(1)} MB/min
          </span>
          {isAnomalous && <span style={{ color: '#ef4444', marginLeft: '8px' }}>🔴 ALERT</span>}
        </span>
      </div>
    </div>
  )
}
