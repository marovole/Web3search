import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SharedReportPage from './pages/SharedReportPage'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/shared/:shareToken" element={<SharedReportPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
