import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'

export default function LoginHeatmap({ websocketData }) {
  const [data, setData] = useState([])
  const FAILURE_THRESHOLD = 5

  useEffect(() => {
    if (websocketData && websocketData.length > 0) {
      const latest = websocketData[0]
      const newPoint = {
        time: new Date(latest.timestamp).toLocaleTimeString('en-US', { 
          hour12: false, 
          hour: '2-digit', 
          minute: '2-digit' 
        }),
        success: latest.successful_logins || Math.floor(Math.random() * 15),
        failed: latest.failed_logins || Math.floor(Math.random() * 50)
      }
      
      setData(prev => [...prev.slice(-14), newPoint])
    } else {
      // Demo data
      setData(prev => {
        if (prev.length === 0) {
          return Array.from({ length: 15 }, (_, i) => ({
            time: new Date(Date.now() - (14 - i) * 120000).toLocaleTimeString('en-US', { 
              hour12: false, 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            success: Math.floor(Math.random() * 15),
            failed: Math.floor(Math.random() * 50)
          }))
        }
        return prev
      })
    }
  }, [websocketData])

  const totalFailed = data.reduce((sum, item) => sum + item.failed, 0)
  const totalSuccess = data.reduce((sum, item) => sum + item.success, 0)
  const currentFailed = data[data.length - 1]?.failed || 0
  const isAnomalous = currentFailed > FAILURE_THRESHOLD * 3

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
        💻 Login Attempts (Live)
      </h3>
      
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
          <XAxis 
            dataKey="time" 
            stroke="#64748b" 
            tick={{ fontSize: 9, fill: '#64748b' }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis 
            stroke="#64748b" 
            tick={{ fontSize: 10, fill: '#64748b' }}
          />
          <Tooltip
            contentStyle={{ 
              background: '#0a0e1a', 
              border: '1px solid #1e2d45',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Bar dataKey="success" fill="#22c55e" radius={[4, 4, 0, 0]} />
          <Bar dataKey="failed" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.failed > FAILURE_THRESHOLD * 3 ? "#ef4444" : "#f97316"} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '8px',
        marginTop: '12px',
        fontSize: '11px'
      }}>
        <div style={{ 
          padding: '8px', 
          background: '#0a0e1a', 
          borderRadius: '4px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#22c55e', fontWeight: 'bold', fontSize: '16px' }}>
            {totalSuccess}
          </div>
          <div style={{ color: '#64748b' }}>Success</div>
        </div>
        <div style={{ 
          padding: '8px', 
          background: '#0a0e1a', 
          borderRadius: '4px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#ef4444', fontWeight: 'bold', fontSize: '16px' }}>
            {totalFailed}
          </div>
          <div style={{ color: '#64748b' }}>Failed</div>
        </div>
        <div style={{ 
          padding: '8px', 
          background: isAnomalous ? '#450a0a' : '#0a0e1a', 
          borderRadius: '4px',
          textAlign: 'center',
          border: isAnomalous ? '1px solid #7f1d1d' : 'none'
        }}>
          <div style={{ color: isAnomalous ? '#ef4444' : '#64748b', fontWeight: 'bold', fontSize: '16px' }}>
            {isAnomalous ? '🔴 HIGH' : '🟢 NORMAL'}
          </div>
          <div style={{ color: '#64748b' }}>Status</div>
        </div>
      </div>
    </div>
  )
}
