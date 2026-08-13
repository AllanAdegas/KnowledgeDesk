import { NavLink, Route, Routes } from 'react-router-dom'
import { AgentPage } from './pages/AgentPage'
import { ChatPage } from './pages/ChatPage'
import { DocumentsPage } from './pages/DocumentsPage'

const NAV_ITEMS = [
  { to: '/', label: 'Chat' },
  { to: '/documents', label: 'Documentos' },
  { to: '/agent', label: 'Agente' },
]

function App() {
  return (
    <div className="flex h-screen flex-col">
      <nav className="flex gap-4 border-b border-gray-200 px-6 py-3">
        <span className="font-semibold">KnowledgeDesk</span>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              isActive ? 'font-medium text-blue-600' : 'text-gray-500'
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/agent" element={<AgentPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
