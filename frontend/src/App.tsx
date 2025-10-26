import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import SharedReportPage from './pages/SharedReportPage'
import HistoryPage from './pages/HistoryPage'
import WatchlistPage from './pages/WatchlistPage'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/shared/:shareToken" element={<SharedReportPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
