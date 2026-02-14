import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import AlertsPage from './pages/AlertsPage'
import IncidentPage from './pages/IncidentPage'
import LivePage from './pages/LivePage'
import CopilotPage from './pages/CopilotPage'
import ThreatsPage from './pages/ThreatsPage'

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
  )
}
