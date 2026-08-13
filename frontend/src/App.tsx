import { NavLink, Route, Routes } from 'react-router-dom'
import { AgentPage } from './pages/AgentPage'
import { ChatPage } from './pages/ChatPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { AgentIcon, ChatIcon, DocsIcon } from './components/icons'

const NAV_ITEMS = [
  { to: '/', label: 'Chat', icon: ChatIcon },
  { to: '/documents', label: 'Documentos', icon: DocsIcon },
  { to: '/agent', label: 'Agente', icon: AgentIcon },
]

function App() {
  return (
    <div className="flex h-screen flex-col bg-[#05060a]">
      <nav className="flex shrink-0 items-center gap-1 border-b border-white/10 bg-white/[0.03] px-4 py-2.5 backdrop-blur-xl sm:px-6">
        <div className="mr-4 flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-400 via-violet-500 to-fuchsia-500 text-xs font-bold text-white shadow-[0_0_18px_rgba(129,140,248,0.45)]">
            K
          </span>
          <span className="font-semibold tracking-tight text-slate-100">KnowledgeDesk</span>
        </div>

        <div className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </div>
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
