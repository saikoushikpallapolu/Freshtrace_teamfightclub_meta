import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import BatchWorkspace from './pages/BatchWorkspace.jsx'

const showDeviceDashboard = new URLSearchParams(window.location.search).get('view') === 'device'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {showDeviceDashboard ? <App /> : <BatchWorkspace />}
  </StrictMode>,
)
