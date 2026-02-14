class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.listeners = []
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectDelay = 3000
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}${this.url}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log(`✅ WebSocket connected: ${this.url}`)
      this.reconnectAttempts = 0
      
      // Send ping every 30 seconds to keep connection alive
      this.pingInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send('ping')
        }
      }, 30000)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.listeners.forEach(listener => listener(data))
      } catch (error) {
        console.error('WebSocket parse error:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error(`❌ WebSocket error: ${this.url}`, error)
    }

    this.ws.onclose = () => {
      console.log(`🔌 WebSocket disconnected: ${this.url}`)
      clearInterval(this.pingInterval)
      this.attemptReconnect()
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      setTimeout(() => this.connect(), this.reconnectDelay)
    } else {
      console.error('❌ Max reconnection attempts reached')
    }
  }

  subscribe(listener) {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener)
    }
  }

  disconnect() {
    clearInterval(this.pingInterval)
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

export const alertsWebSocket = new WebSocketClient('/ws/alerts')
export const liveNetworkWebSocket = new WebSocketClient('/ws/live/network')
export const liveCameraWebSocket = new WebSocketClient('/ws/live/camera')
export const liveRFWebSocket = new WebSocketClient('/ws/live/rf')
export const liveLogsWebSocket = new WebSocketClient('/ws/live/logs')
export const liveFilesWebSocket = new WebSocketClient('/ws/live/files')

export default WebSocketClient
