import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'

export default function SHAPChart({ shapData, incidentId }) {
  // Transform SHAP data for visualization
  // Expected format: { features: [...], values: [...], base_value: number }
  const chartData = shapData?.features?.map((feature, index) => ({
    feature: feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: shapData.values[index],
    absValue: Math.abs(shapData.values[index])
  })).sort((a, b) => b.absValue - a.absValue) || []

  const baseValue = shapData?.base_value || 0
  const maxAbsValue = Math.max(...chartData.map(d => Math.abs(d.value)), 0.1)

  const getColor = (value) => {
    if (value > 0) return '#ef4444'  // Positive contribution (increases risk)
    return '#22c55e'  // Negative contribution (decreases risk)
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div style={{
          background: '#0a0e1a',
          border: '1px solid #1e2d45',
          borderRadius: '4px',
          padding: '8px 12px',
          fontSize: '12px'
        }}>
          <div style={{ color: '#e2e8f0', fontWeight: 'bold', marginBottom: '4px' }}>
            {data.feature}
          </div>
          <div style={{ color: data.value > 0 ? '#ef4444' : '#22c55e' }}>
            SHAP Value: {data.value > 0 ? '+' : ''}{data.value.toFixed(4)}
          </div>
          <div style={{ color: '#64748b', fontSize: '10px', marginTop: '4px' }}>
            {data.value > 0 ? '↑ Increases risk score' : '↓ Decreases risk score'}
          </div>
        </div>
      )
    }
    return null
  }

  if (!shapData || !shapData.features || shapData.features.length === 0) {
    return (
      <div style={{
        background: '#1a2233',
        borderRadius: '8px',
        padding: '20px',
        border: '1px solid #1e2d45',
        textAlign: 'center'
      }}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '8px' }}>📊 SHAP Feature Importance</h3>
        <p style={{ color: '#64748b', fontSize: '14px' }}>
          No SHAP data available for this incident.
        </p>
      </div>
    )
  }

  return (
    <div style={{
      background: '#1a2233',
      borderRadius: '8px',
      padding: '16px',
      border: '1px solid #1e2d45'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ 
          color: '#e2e8f0', 
          fontSize: '16px',
          fontWeight: '600',
          margin: 0
        }}>
          📊 SHAP Feature Importance
        </h3>
        <div style={{
          background: '#0a0e1a',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          color: '#64748b'
        }}>
          Base Value: {baseValue.toFixed(2)}
        </div>
      </div>

      <div style={{
        marginBottom: '12px',
        padding: '10px',
        background: '#0a0e1a',
        borderRadius: '4px',
        fontSize: '12px',
        color: '#94a3b8'
      }}>
        <span style={{ color: '#ef4444' }}>🔴 Positive values</span> increase risk score | 
        <span style={{ color: '#22c55e', marginLeft: '8px' }}> 🟢 Negative values</span> decrease risk score
      </div>

      <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 35)}>
        <BarChart 
          data={chartData} 
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <XAxis 
            type="number" 
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#64748b' }}
            domain={[-maxAbsValue * 1.1, maxAbsValue * 1.1]}
          />
          <YAxis 
            type="category" 
            dataKey="feature" 
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#e2e8f0' }}
            width={110}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e2d45' }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
            ))}
            <LabelList 
              dataKey="value" 
              position="right" 
              formatter={(value) => (value > 0 ? '+' : '') + value.toFixed(3)}
              style={{ fontSize: 10, fill: '#e2e8f0' }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div style={{
        marginTop: '16px',
        padding: '12px',
        background: '#0a0e1a',
        borderRadius: '4px',
        fontSize: '11px',
        color: '#64748b'
      }}>
        <div style={{ marginBottom: '6px', color: '#94a3b8', fontWeight: '600' }}>
          Interpretation:
        </div>
        <div>
          Top contributing feature: <span style={{ 
            color: '#e2e8f0', 
            fontWeight: 'bold' 
          }}>
            {chartData[0]?.feature}
          </span> ({chartData[0]?.value > 0 ? 'increases' : 'decreases'} risk by {Math.abs(chartData[0]?.value || 0).toFixed(3)})
        </div>
        {chartData.length > 1 && (
          <div style={{ marginTop: '4px' }}>
            Second: <span style={{ color: '#e2e8f0' }}>{chartData[1]?.feature}</span> 
            ({chartData[1]?.value > 0 ? '+' : ''}{chartData[1]?.value.toFixed(3)})
          </div>
        )}
      </div>
    </div>
  )
}
