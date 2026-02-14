# ThreatLens AI Frontend

React + Vite frontend for the ThreatLens AI SOC dashboard.

## Features

- 🚨 **Real-time Alert Feed** - Live incident monitoring with WebSocket updates
- 📊 **Incident Details** - Timeline, attack graph, evidence, and XAI explanations
- 📹 **Live Monitoring** - Real-time metrics from all data sources
- 🤖 **SOC Copilot** - Natural language queries powered by Mistral-7B
- 🧬 **Threat Intelligence** - MITRE ATT&CK heatmap, IOCs, and threat origins

## Tech Stack

- React 18
- React Router v6
- Vite (build tool)
- Axios (API client)
- WebSocket (real-time updates)
- CSS Modules (styling)

## Quick Start

### 1. Install Dependencies

```powershell
cd frontend/threat_lens_frontend
npm install
```

### 2. Start Development Server

```powershell
npm run dev
```

Frontend will be available at: http://localhost:3000

### 3. Ensure Backend is Running

The frontend expects the backend API at `http://localhost:8000`

Make sure you've started the backend server first!

## Project Structure

```
src/
├── components/
│   ├── layout/         # Sidebar, TopBar, Layout
│   └── alerts/         # AlertCard component
│
├── pages/
│   ├── AlertsPage.jsx       # Main alert feed (homepage)
│   ├── IncidentPage.jsx     # Incident detail view
│   ├── LivePage.jsx         # Live monitoring dashboard
│   ├── CopilotPage.jsx      # SOC Copilot chat interface
│   └── ThreatsPage.jsx      # Threat intelligence page
│
├── services/
│   ├── api.js          # Axios API client
│   └── websocket.js    # WebSocket client
│
├── App.jsx             # Router setup
├── main.jsx           # Entry point
└── index.css          # Global styles (dark theme)
```

## Pages

### 1. Alerts Feed (`/`)
- Displays all security incidents
- Filters by severity (Critical/High/Medium/Low)
- Filters by source (camera/network/logs/rf/file)
- Real-time updates via WebSocket
- Click any incident to view details

### 2. Incident Detail (`/incident/:id`)
- **Overview Tab**: Sources, MITRE TTPs, status
- **Timeline Tab**: Chronological event sequence
- **Evidence Tab**: Files, videos, logs (placeholder)
- **XAI Tab**: Explainable AI analysis

### 3. Live Monitoring (`/live`)
- Network traffic metrics
- Login attempt monitoring
- Camera zone status
- RF device detection
- File modification feed
- Anomaly score meters

### 4. SOC Copilot (`/copilot`)
- Chat interface with AI assistant
- Powered by Mistral-7B (via Ollama)
- Natural language queries about incidents
- Shows related incident references

### 5. Threat Intelligence (`/threats`)
- MITRE ATT&CK tactic heatmap
- Active IOC feed with actions
- Attack intent distribution
- Geographic threat origins

## API Integration

All API calls go through `src/services/api.js`:

```javascript
import { incidentsAPI, copilotAPI, liveAPI } from './services/api'

// Get incidents
const data = await incidentsAPI.getAll({ severity: 'CRITICAL' })

// Query copilot
const response = await copilotAPI.query('What are the critical incidents?')

// Get system health
const health = await liveAPI.getHealth()
```

## WebSocket Integration

Real-time updates via WebSocket:

```javascript
import { alertsWebSocket } from './services/websocket'

// Connect
alertsWebSocket.connect()

// Subscribe to messages
const unsubscribe = alertsWebSocket.subscribe((message) => {
  if (message.type === 'new_incident') {
    console.log('New incident:', message.data)
  }
})

// Cleanup
unsubscribe()
```

## Dark Theme

The UI uses a dark theme optimized for SOC environments:

Color palette:
- Primary BG: `#0a0e1a`
- Secondary BG: `#111827`
- Card BG: `#1a2233`
- Border: `#1e2d45`

Severity colors:
- Critical: `#ef4444` (red)
- High: `#f97316` (orange)
- Medium: `#eab308` (yellow)
- Low: `#22c55e` (green)

## Build for Production

```powershell
npm run build
```

Production files will be in `dist/`

To preview production build:
```powershell
npm run preview
```

## Development Tips

### Hot Module Replacement (HMR)
Vite provides instant HMR - your changes will appear immediately without full page reload.

### API Proxy
The dev server proxies `/api` and `/ws` requests to `localhost:8000` (configured in `vite.config.js`).

### Adding New Pages
1. Create component in `src/pages/`
2. Add route in `src/App.jsx`
3. Add menu item in `src/components/layout/Sidebar.jsx`

### Styling
Use CSS Modules for component styles (`.module.css` files). Global styles go in `src/index.css`.

## Mock Data

Currently, the frontend works with:
- Live backend API data (when available)
- Mock/placeholder data for visualization components
- Empty states when no data is present

To populate with real data, you need to:
1. Have the backend running
2. Ensure database has incident data
3. Start Kafka producers (for real-time updates)

## Troubleshooting

**WebSocket not connecting?**
- Check if backend is running on port 8000
- Open browser console to see connection errors
- WebSocket auto-reconnects after 3 seconds

**API calls failing?**
- Verify backend is running: `http://localhost:8000/health`
- Check browser Network tab for request details
- CORS is configured in backend to allow localhost:3000

**Blank page?**
- Check browser console for errors
- Ensure all dependencies installed: `npm install`
- Try clearing cache: `npm run dev -- --force`

## Browser Support

Tested on:
- Chrome/Edge (recommended)
- Firefox
- Safari

Requires modern browser with ES6+ and WebSocket support.
