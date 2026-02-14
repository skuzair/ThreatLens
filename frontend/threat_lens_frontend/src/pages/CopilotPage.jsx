import { useState } from 'react'
import { copilotAPI } from '../services/api'
import styles from './CopilotPage.module.css'

export default function CopilotPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your SOC Copilot powered by Mistral-7B. Ask me about security incidents, threat intelligence, or system status.'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await copilotAPI.query(input)
      console.log('Copilot response:', response)
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        references: response.incident_references
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Copilot error:', error)
      console.error('Error details:', error.response?.data || error.message)
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please check browser console for details.`
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🤖 SOC Copilot</h1>
        <div className={styles.powered}>Powered by Mistral-7B (Local)</div>
      </div>

      <div className={styles.chatContainer}>
        <div className={styles.messages}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={msg.role === 'user' ? styles.userMessage : styles.assistantMessage}
            >
              <div className={styles.messageHeader}>
                <strong>{msg.role === 'user' ? '👤 You' : '🤖 ThreatLens AI'}</strong>
              </div>
              <div className={styles.messageContent}>
                {msg.content}
              </div>
              {msg.references && msg.references.length > 0 && (
                <div className={styles.references}>
                  <strong>Related Incidents:</strong> {msg.references.join(', ')}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className={styles.assistantMessage}>
              <div className={styles.messageHeader}>
                <strong>🤖 ThreatLens AI</strong>
              </div>
              <div className={styles.messageContent}>
                <div className="spinner"></div> Thinking...
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about security incidents, threats, or system status..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()} className="primary">
            Send ↵
          </button>
        </form>

        <div className={styles.suggestions}>
          <strong>Suggested Questions:</strong>
          {[
            'What are the critical incidents today?',
            'Show me all data exfiltration attempts',
            'Which hosts should be isolated right now?'
          ].map(suggestion => (
            <button
              key={suggestion}
              onClick={() => setInput(suggestion)}
              disabled={loading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
