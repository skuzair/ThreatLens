import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { incidentsAPI, evidenceAPI, sandboxAPI, copilotAPI, liveAPI } from './services/api';
import { useWebSocket } from './hooks/useWebSocket';
import { SEVERITY_CONFIG, SOURCE_ICONS, SOURCE_COLORS, formatTime, getRiskColor, timeAgo } from './utils/helpers';

// Layout Component
function Layout({ children }) {
  const [systemHealth, setSystemHealth] = useState({
    network: true,
    camera: true,
    rf: true,
    logs: true,
    files: true,
    sandbox: true
  });
  
  const { connected } = useWebSocket();
  
  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <div style={{
        width: '250px',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        <div style={{ marginBottom: '30px' }}>
          <h1 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '5px' }}>
            🛡️ ThreatLens AI
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: connected ? '#22c55e' : '#ef4444',
              animation: connected ? 'pulse 2s infinite' : 'none'
            }} />
            <span style={{ color: connected ? '#22c55e' : '#ef4444' }}>
              {connected ? 'LIVE' : 'OFFLINE'}
            </span>
            <span style={{ color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
              {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
        
        <NavLink to="/" icon="🚨">Alerts</NavLink>
        <NavLink to="/live" icon="📹">Live Monitoring</NavLink>
        <NavLink to="/copilot" icon="🤖">SOC Copilot</NavLink>
        <NavLink to="/threats" icon="🧬">Threat Intel</NavLink>
        
        <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '12px', textTransform: 'uppercase', fontWeight: '600' }}>
            System Health
          </div>
          {Object.entries(systemHealth).map(([system, status]) => (
            <div key={system} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', fontSize: '13px' }}>
              <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{system}</span>
              <span style={{ color: status ? '#22c55e' : '#ef4444' }}>{status ? '✅' : '❌'}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Main Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {children}
      </div>
    </div>
  );
}

function NavLink({ to, icon, children }) {
  return (
    <Link
      to={to}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        borderRadius: '8px',
        textDecoration: 'none',
        color: 'var(--text-secondary)',
        transition: 'all 0.2s',
        fontSize: '14px',
        fontWeight: '500'
      }}
      onMouseEnter={e => {
        e.target.style.background = 'var(--bg-hover)';
        e.target.style.color = 'var(--text-primary)';
      }}
      onMouseLeave={e => {
        e.target.style.background = 'transparent';
        e.target.style.color = 'var(--text-secondary)';
      }}
    >
      <span style={{ fontSize: '18px' }}>{icon}</span>
      {children}
    </Link>
  );
}

// Alert Card Component
function AlertCard({ incident, onClick }) {
  const config = SEVERITY_CONFIG[incident.severity];
  
  return (
    <div
      onClick={onClick}
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s'
      }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateX(4px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'translateX(0)'}
      className="slide-in"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>{config.icon}</span>
          <div>
            <span style={{ color: config.color, fontWeight: '700', fontSize: '12px' }}>
              {incident.severity}
            </span>
            <span style={{ color: 'var(--text-tertiary)', fontSize: '11px', marginLeft: '12px' }}>
              {incident.incident_id}
            </span>
          </div>
        </div>
        <div style={{
          background: config.color,
          color: 'white',
          borderRadius: '20px',
          padding: '4px 12px',
          fontWeight: '700',
          fontSize: '16px'
        }}>
          {incident.risk_score}/100
        </div>
      </div>
      
      <div style={{ fontSize: '15px', fontWeight: '600', margin: '8px 0', color: 'var(--text-primary)' }}>
        {incident.rule_name}
      </div>
      
      <div style={{ display: 'flex', gap: '6px', margin: '8px 0', flexWrap: 'wrap' }}>
        {incident.sources_involved.map(source => (
          <span key={source} style={{
            background: 'var(--bg-hover)',
            padding: '4px 10px',
            borderRadius: '4px',
            fontSize: '11px',
            color: 'var(--text-secondary)'
          }}>
            {SOURCE_ICONS[source]} {source}
          </span>
        ))}
      </div>
      
      <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '8px' }}>
        <span>🕐 {timeAgo(incident.timestamp)}</span>
        <span>📍 {incident.zone}</span>
        <span>🔗 {incident.sources_involved.length} sources</span>
      </div>
      
      <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Intent:</span>
        <span style={{
          background: 'var(--accent-bg)',
          color: 'var(--accent)',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: '600'
        }}>
          {incident.intent_primary.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
          {Math.round(incident.intent_confidence * 100)}%
        </span>
      </div>
    </div>
  );
}

// Alerts Page (Homepage)
function AlertsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ severity: null, source: null });
  const navigate = useNavigate();
  const { messages } = useWebSocket();
  
  useEffect(() => {
    loadIncidents();
  }, [filter]);
  
  // Listen for new incidents from WebSocket
  useEffect(() => {
    const newIncidents = messages.filter(m => m.type === 'new_incident');
    if (newIncidents.length > 0) {
      setIncidents(prev => {
        const newData = newIncidents.map(m => m.data);
        const combined = [...newData, ...prev];
        // Remove duplicates
        const unique = combined.filter((v, i, a) => 
          a.findIndex(t => t.incident_id === v.incident_id) === i
        );
        return unique.slice(0, 50); // Keep last 50
      });
    }
  }, [messages]);
  
  async function loadIncidents() {
    try {
      setLoading(true);
      const response = await incidentsAPI.getAll({ 
        limit: 20, 
        ...filter 
      });
      setIncidents(response.data.incidents);
    } catch (error) {
      console.error('Error loading incidents:', error);
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <div style={{ padding: '30px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>
          🚨 Security Alerts
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Real-time incident monitoring with AI-powered correlation and risk scoring
        </p>
      </div>
      
      {/* Filters */}
      <div style={{ 
        display: 'flex', 
        gap: '12px', 
        marginBottom: '24px',
        padding: '16px',
        background: 'var(--bg-card)',
        borderRadius: '8px',
        border: '1px solid var(--border)'
      }}>
        <button
          onClick={() => setFilter({ ...filter, severity: null })}
          style={{ background: !filter.severity ? 'var(--accent)' : 'var(--bg-secondary)' }}
        >
          All
        </button>
        {Object.keys(SEVERITY_CONFIG).map(sev => (
          <button
            key={sev}
            onClick={() => setFilter({ ...filter, severity: sev })}
            style={{ 
              background: filter.severity === sev ? SEVERITY_CONFIG[sev].color : 'var(--bg-secondary)',
              color: 'white'
            }}
          >
            {SEVERITY_CONFIG[sev].icon} {sev}
          </button>
        ))}
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
          <p style={{ marginTop: '20px', color: 'var(--text-secondary)' }}>Loading incidents...</p>
        </div>
      ) : incidents.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px',
          background: 'var(--bg-card)',
          borderRadius: '8px',
          border: '1px solid var(--border)'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>No Active Incidents</h3>
          <p style={{ color: 'var(--text-secondary)' }}>All systems operating normally</p>
        </div>
      ) : (
        <div>
          {incidents.map(incident => (
            <AlertCard 
              key={incident.incident_id} 
              incident={incident}
              onClick={() => navigate(`/incident/${incident.incident_id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Incident Detail Page
function IncidentPage() {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [sandbox, setSandbox] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    loadIncidentData();
  }, [id]);
  
  async function loadIncidentData() {
    try {
      setLoading(true);
      const [incidentRes, evidenceRes] = await Promise.all([
        incidentsAPI.getById(id),
        evidenceAPI.getByIncident(id)
      ]);
      
      setIncident(incidentRes.data);
      setEvidence(evidenceRes.data.evidence || []);
      
      // Try to load sandbox data
      try {
        const sandboxRes = await sandboxAPI.getByIncident(id);
        setSandbox(sandboxRes.data);
      } catch (err) {
        // Sandbox data might not exist for all incidents
      }
    } catch (error) {
      console.error('Error loading incident:', error);
    } finally {
      setLoading(false);
    }
  }
  
  if (loading || !incident) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="spinner" />
      </div>
    );
  }
  
  const config = SEVERITY_CONFIG[incident.severity];
  
  return (
    <div style={{ padding: '30px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <button 
          onClick={() => navigate('/')}
          style={{ marginBottom: '20px', background: 'var(--bg-card)' }}
        >
          ← Back to Alerts
        </button>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
              <h1 style={{ fontSize: '28px', fontWeight: '700' }}>{incident.incident_id}</h1>
              <span className="badge" style={{ 
                background: config.bg,
                color: config.color,
                border: `1px solid ${config.border}`,
                fontSize: '14px',
                padding: '6px 14px'
              }}>
                {config.icon} {incident.severity}
              </span>
              <span style={{
                background: config.color,
                color: 'white',
                borderRadius: '20px',
                padding: '6px 16px',
                fontWeight: '700',
                fontSize: '18px'
              }}>
                Risk: {incident.risk_score}/100
              </span>
            </div>
            <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-primary)' }}>
              {incident.rule_name}
            </h2>
            <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              <span>🕐 {new Date(incident.timestamp).toLocaleString()}</span>
              <span>📍 {incident.zone}</span>
              <span>🔗 {incident.sources_involved.length} Sources Correlated</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div style={{ borderBottom: '2px solid var(--border)', marginBottom: '30px' }}>
        <div style={{ display: 'flex', gap: '30px' }}>
          {['overview', 'evidence', 'sandbox', 'xai'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                background: 'transparent',
                border: 'none',
                padding: '12px 0',
                color: activeTab === tab ? 'var(--accent)' : 'var(--text-secondary)',
                borderBottom: activeTab === tab ? '2px solid var(--accent)' : '2px solid transparent',
                fontWeight: activeTab === tab ? '600' : '400',
                textTransform: 'capitalize',
                marginBottom: '-2px'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab Content */}
      {activeTab === 'overview' && (
        <OverviewTab incident={incident} />
      )}
      {activeTab === 'evidence' && (
        <EvidenceTab evidence={evidence} incidentId={id} />
      )}
      {activeTab === 'sandbox' && (
        <SandboxTab sandbox={sandbox} />
      )}
      {activeTab === 'xai' && (
        <XAITab incident={incident} />
      )}
    </div>
  );
}

function OverviewTab({ incident }) {
  return (
    <div>
      {/* Timeline */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px' }}>
          Attack Timeline
        </h3>
        <div style={{ position: 'relative' }}>
          {incident.correlated_events.map((event, i) => (
            <div key={event.event_id} style={{ marginBottom: '24px', position: 'relative', paddingLeft: '40px' }}>
              <div style={{
                position: 'absolute',
                left: '0',
                top: '0',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: SOURCE_COLORS[event.source],
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: '700',
                color: 'white',
                zIndex: 2
              }}>
                {i + 1}
              </div>
              {i < incident.correlated_events.length - 1 && (
                <div style={{
                  position: 'absolute',
                  left: '11px',
                  top: '24px',
                  bottom: '-24px',
                  width: '2px',
                  background: 'var(--border)',
                  zIndex: 1
                }} />
              )}
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '18px' }}>{SOURCE_ICONS[event.source]}</span>
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                      {event.source.toUpperCase()}
                    </span>
                  </div>
                  <span style={{ 
                    background: getRiskColor(event.score) + '33',
                    color: getRiskColor(event.score),
                    padding: '2px 10px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    Score: {event.score}/100
                  </span>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '4px' }}>
                  {event.description}
                </p>
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                  🕐 {formatTime(event.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Predicted Next Move */}
      {incident.predicted_next_move && (
        <div style={{
          background: '#2d1f00',
          border: '2px solid #92400e',
          borderRadius: '8px',
          padding: '20px',
          marginTop: '24px'
        }}>
          <h4 style={{ color: '#fbbf24', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '20px' }}>⚠️</span>
            Predicted Next Move
          </h4>
          <div style={{ color: '#fde68a', fontSize: '15px', marginBottom: '8px' }}>
            <strong>{incident.predicted_next_move.name}</strong> ({incident.predicted_next_move.technique})
          </div>
          <div style={{ fontSize: '13px', color: '#fcd34d' }}>
            Expected within {incident.predicted_next_move.time_estimate_minutes} minutes
            <span style={{ marginLeft: '12px' }}>
              Confidence: {Math.round(incident.predicted_next_move.confidence * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function EvidenceTab({ evidence, incidentId }) {
  const [verifying, setVerifying] = useState(false);
  const [verification, setVerification] = useState(null);
  
  async function verifyEvidence() {
    try {
      setVerifying(true);
      const response = await evidenceAPI.verify(incidentId);
      setVerification(response.data);
    } catch (error) {
      console.error('Error verifying evidence:', error);
    } finally {
      setVerifying(false);
    }
  }
  
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '20px', fontWeight: '600' }}>
          Evidence Gallery ({evidence.length} items)
        </h3>
        <button onClick={verifyEvidence} disabled={verifying}>
          {verifying ? 'Verifying...' : '🔗 Verify Blockchain'}
        </button>
      </div>
      
      {verification && (
        <div style={{
          background: verification.all_verified ? 'var(--low-bg)' : 'var(--critical-bg)',
          border: `1px solid ${verification.all_verified ? 'var(--low-border)' : 'var(--critical-border)'}`,
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>{verification.all_verified ? '✅' : '❌'}</span>
            <div>
              <div style={{ fontWeight: '600', color: verification.all_verified ? 'var(--low)' : 'var(--critical)' }}>
                {verification.all_verified ? 'All Evidence Verified' : 'Verification Failed'}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Blockchain verification complete for {verification.evidence.length} items
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
        {evidence.map(ev => (
          <div key={ev.evidence_id} style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
                📁 {ev.evidence_type.toUpperCase()}
              </span>
              {ev.verified && <span style={{ color: '#22c55e' }}>✅ Verified</span>}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '8px', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              {ev.sha256_hash}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Block #{ev.blockchain_block_number}
            </div>
            <a 
              href={`https://mumbai.polygonscan.com/tx/${ev.blockchain_tx_hash}`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: '12px', color: 'var(--accent)' }}
            >
              View on Polygonscan ↗
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

function SandboxTab({ sandbox }) {
  if (!sandbox) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📦</div>
        <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>No Sandbox Results</h3>
        <p style={{ color: 'var(--text-secondary)' }}>
          Sandbox analysis was not triggered for this incident
        </p>
      </div>
    );
  }
  
  const verdictConfig = {
    MALICIOUS: { color: '#ef4444', bg: '#450a0a' },
    SUSPICIOUS: { color: '#f97316', bg: '#431407' },
    BENIGN: { color: '#22c55e', bg: '#052e16' }
  };
  
  const config = verdictConfig[sandbox.verdict];
  
  return (
    <div>
      {/* Verdict Banner */}
      <div style={{
        background: config.bg,
        border: `2px solid ${config.color}`,
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '30px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <span style={{ fontSize: '32px' }}>{sandbox.verdict === 'MALICIOUS' ? '🔴' : sandbox.verdict === 'SUSPICIOUS' ? '🟠' : '🟢'}</span>
              <div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: config.color }}>
                  {sandbox.verdict}
                </div>
                <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                  Confidence: {sandbox.confidence_score}%
                </div>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-tertiary)' }}>
            <div>File: {sandbox.file_hash.substring(0, 16)}...</div>
            <div>{new Date(sandbox.detonation_timestamp).toLocaleString()}</div>
          </div>
        </div>
      </div>
      
      {/* Behavioral Summary & IOCs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            Behavioral Summary
          </h4>
          {Object.entries(sandbox.behavioral_summary).map(([key, value]) => (
            <div key={key} style={{ display: 'flex', gap: '8px', marginBottom: '8px', fontSize: '13px' }}>
              <span style={{ color: '#ef4444' }}>✗</span>
              <span style={{ color: 'var(--text-secondary)' }}>
                {key.replace(/_/g, ' ')}: <strong>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</strong>
              </span>
            </div>
          ))}
        </div>
        
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            Extracted IOCs
          </h4>
          {Object.entries(sandbox.extracted_iocs).map(([type, values]) => (
            type !== 'mitre_behaviors' && (
              <div key={type} style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  {type}
                </div>
                {(Array.isArray(values) ? values : [values]).map((val, i) => (
                  <div key={i} style={{
                    background: 'var(--bg-primary)',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                    color: '#f97316',
                    marginBottom: '4px',
                    wordBreak: 'break-all'
                  }}>
                    {val}
                  </div>
                ))}
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
}

function XAITab({ incident }) {
  const explanation = incident.nlg_explanation;
  
  return (
    <div>
      {/* Summary */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <h3 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px', color: '#ef4444' }}>
          Why Risk Score = {explanation.risk_score}?
        </h3>
        
        {explanation.sections.map((section, i) => (
          <div key={i} style={{
            borderLeft: `3px solid ${SOURCE_COLORS[section.source.toLowerCase()]}`,
            paddingLeft: '16px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <strong style={{ fontSize: '14px' }}>
                {section.icon} {section.source}
              </strong>
              <span style={{ color: getRiskColor(section.score), fontWeight: '600' }}>
                {section.score}/100
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              {section.text}
            </p>
          </div>
        ))}
        
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', marginTop: '16px' }}>
          <p style={{ color: 'var(--accent)', fontSize: '14px', marginBottom: '8px' }}>
            {explanation.correlation_statement}
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            MITRE ATT&CK: {explanation.mitre_statement}
          </p>
        </div>
      </div>
      
      {/* Recommended Actions */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
          Recommended Actions
        </h4>
        {explanation.recommended_actions.map((action, i) => (
          <div key={i} style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
            <span style={{ color: 'var(--accent)', fontWeight: '700' }}>{i + 1}.</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{action}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Live Monitoring Page
function LivePage() {
  const [networkData, setNetworkData] = useState({ current_mb_per_hour: 45, baseline_mb_per_hour: 45 });
  const [cameras, setCameras] = useState({ zones: [] });
  const [anomalyScores, setAnomalyScores] = useState({ network: 75, camera: 80, rf: 70, logs: 65, files: 85 });
  const { messages } = useWebSocket();
  
  useEffect(() => {
    loadLiveData();
    const interval = setInterval(loadLiveData, 10000);
    return () => clearInterval(interval);
  }, []);
  
  useEffect(() => {
    const liveNetwork = messages.filter(m => m.type === 'live_network');
    if (liveNetwork.length > 0) {
      setNetworkData(liveNetwork[0].data);
    }
    
    const scores = messages.filter(m => m.type === 'anomaly_scores');
    if (scores.length > 0) {
      setAnomalyScores(scores[0].data);
    }
  }, [messages]);
  
  async function loadLiveData() {
    try {
      const [networkRes, cameraRes, scoresRes] = await Promise.all([
        liveAPI.getNetwork(),
        liveAPI.getCameras(),
        liveAPI.getAnomalyScores()
      ]);
      setNetworkData(networkRes.data);
      setCameras(cameraRes.data);
      setAnomalyScores(scoresRes.data);
    } catch (error) {
      console.error('Error loading live data:', error);
    }
  }
  
  return (
    <div style={{ padding: '30px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>
        📹 Live Monitoring Dashboard
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '30px' }}>
        Real-time system monitoring across all data sources
      </p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {/* Network Traffic */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            🌐 Network Traffic
          </h3>
          <div style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px', color: networkData.is_alert ? '#ef4444' : '#22c55e' }}>
            {networkData.current_mb_per_hour} MB/hr
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Baseline: {networkData.baseline_mb_per_hour} MB/hr
          </div>
          {networkData.is_alert && (
            <div style={{ marginTop: '12px', padding: '8px', background: '#450a0a', borderRadius: '4px', fontSize: '12px', color: '#ef4444' }}>
              ⚠️ Traffic {Math.round(networkData.current_mb_per_hour / networkData.baseline_mb_per_hour)}x above baseline
            </div>
          )}
        </div>
        
        {/* Camera Zones */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
            📹 Camera Zone Status
          </h3>
          {cameras.zones && cameras.zones.map(zone => (
            <div key={zone.name} style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '8px 0',
              borderBottom: '1px solid var(--border)'
            }}>
              <span style={{ fontSize: '14px' }}>{zone.name}</span>
              <span style={{
                color: zone.status === 'ALERT' ? '#ef4444' : '#22c55e',
                fontSize: '13px',
                fontWeight: '600'
              }}>
                {zone.status === 'ALERT' ? '🔴 ALERT' : '🟢 CLEAR'}
              </span>
            </div>
          ))}
        </div>
        
        {/* Anomaly Scores */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '20px',
          gridColumn: 'span 2'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '20px' }}>
            🎯 Anomaly Score Meters
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
            {Object.entries(anomalyScores).filter(([key]) => key !== 'timestamp').map(([source, score]) => (
              <div key={source}>
                <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginBottom: '8px', textTransform: 'capitalize' }}>
                  {SOURCE_ICONS[source]} {source}
                </div>
                <div style={{ height: '120px', background: 'var(--bg-secondary)', borderRadius: '8px', position: 'relative', overflow: 'hidden' }}>
                  <div style={{
                    position: 'absolute',
                    bottom: 0,
                    width: '100%',
                    height: `${score}%`,
                    background: `linear-gradient(to top, ${getRiskColor(score)}, ${getRiskColor(score)}aa)`,
                    transition: 'height 0.5s'
                  }} />
                </div>
                <div style={{ textAlign: 'center', marginTop: '8px', fontWeight: '700', color: getRiskColor(score) }}>
                  {score}/100
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Copilot Page
function CopilotPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const suggestions = [
    "What happened in the server room last night?",
    "What IPs should I block right now?",
    "Show all critical incidents today",
    "Which hosts should be isolated?"
  ];
  
  async function sendMessage(question = input) {
    if (!question.trim()) return;
    
    const userMessage = { role: 'user', content: question };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await copilotAPI.query(question);
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        supporting_incidents: response.data.supporting_incidents
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error querying copilot:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <div style={{ padding: '30px', maxWidth: '900px', margin: '0 auto', height: 'calc(100vh - 60px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>
          🤖 SOC Copilot
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          AI-powered incident investigation assistant
        </p>
      </div>
      
      {/* Messages */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
            <h3 style={{ marginBottom: '8px' }}>How can I help you today?</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px' }}>
              Ask me about incidents, threats, or security recommendations
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              {suggestions.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(sug)}
                  style={{
                    background: 'var(--bg-secondary)',
                    fontSize: '13px',
                    padding: '8px 12px'
                  }}
                >
                  {sug}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} style={{
              marginBottom: '16px',
              padding: '12px',
              borderRadius: '8px',
              background: msg.role === 'user' ? 'var(--accent-bg)' : 'var(--bg-secondary)',
              border: `1px solid ${msg.role === 'user' ? 'var(--accent)' : 'var(--border)'}`
            }}>
              <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: msg.role === 'user' ? 'var(--accent)' : 'var(--text-secondary)' }}>
                {msg.role === 'user' ? 'YOU' : '🤖 THREATLENS AI'}
              </div>
              <div style={{ fontSize: '14px', whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div style={{ display: 'flex', gap: '8px', padding: '12px' }}>
            <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '2px' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Thinking...</span>
          </div>
        )}
      </div>
      
      {/* Input */}
      <div style={{ display: 'flex', gap: '12px' }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask a question..."
          style={{ flex: 1, padding: '12px' }}
        />
        <button onClick={() => sendMessage()} disabled={loading || !input.trim()}>
          Send ↵
        </button>
      </div>
    </div>
  );
}

// Threat Intel Page
function ThreatsPage() {
  const [iocs, setIocs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadIOCs();
  }, []);
  
  async function loadIOCs() {
    try {
      const response = await iocsAPI.getAll({ limit: 50 });
      setIocs(response.data.iocs);
    } catch (error) {
      console.error('Error loading IOCs:', error);
    } finally {
      setLoading(false);
    }
  }
  
  async function blockIOC(iocId) {
    try {
      await iocsAPI.block(iocId);
      loadIOCs(); // Reload
    } catch (error) {
      console.error('Error blocking IOC:', error);
    }
  }
  
  return (
    <div style={{ padding: '30px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>
        🧬 Threat Intelligence
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '30px' }}>
        Indicators of Compromise (IOCs) and threat data
      </p>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '2px solid var(--border)' }}>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>TYPE</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>VALUE</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>CONFIDENCE</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>SEEN</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>STATUS</th>
                <th style={{ padding: '16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: 'var(--text-tertiary)' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {iocs.map(ioc => (
                <tr key={ioc.ioc_id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '16px' }}>
                    <span className="badge" style={{ fontSize: '10px', padding: '4px 8px' }}>
                      {ioc.ioc_type.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '16px', fontFamily: 'monospace', fontSize: '13px' }}>
                    {ioc.value}
                  </td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ color: getRiskColor(ioc.confidence * 100) }}>
                      {Math.round(ioc.confidence * 100)}%
                    </span>
                  </td>
                  <td style={{ padding: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                    {ioc.times_seen}x
                  </td>
                  <td style={{ padding: '16px' }}>
                    {ioc.blocked ? (
                      <span style={{ color: '#ef4444' }}>🚫 Blocked</span>
                    ) : (
                      <span style={{ color: '#22c55e' }}>✅ Active</span>
                    )}
                  </td>
                  <td style={{ padding: '16px' }}>
                    {!ioc.blocked && (
                      <button 
                        onClick={() => blockIOC(ioc.ioc_id)}
                        style={{ 
                          background: 'var(--critical)',
                          fontSize: '12px',
                          padding: '6px 12px'
                        }}
                      >
                        Block
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Main App
export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<AlertsPage />} />
          <Route path="/incident/:id" element={<IncidentPage />} />
          <Route path="/live" element={<LivePage />} />
          <Route path="/copilot" element={<CopilotPage />} />
          <Route path="/threats" element={<ThreatsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
