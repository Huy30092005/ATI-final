import { useState } from 'react'
import { Library, Menu } from 'lucide-react'
import * as api from './api/research'
import { USE_MOCK } from './api/client'
import { useChat } from './hooks/useChat'
import { useDocuments } from './hooks/useDocuments'
import { downloadBlob } from './lib/utils'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'
import EvidencePanel from './components/EvidencePanel'
import ExportMenu from './components/ExportMenu'

export default function App() {
  const docs = useDocuments()
  const chat = useChat()

  const [sources, setSources] = useState({ documents: true, web: true, academic: true })
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [activeId, setActiveId] = useState(null) // câu trả lời đang xem bằng chứng
  const [highlight, setHighlight] = useState(null) // { messageId, n, t }

  // Tài liệu sẽ được gửi làm ngữ cảnh: đã xử lý xong + còn được tick
  const contextDocs = docs.documents.filter((d) => d.status === 'ready' && docs.isIncluded(d.id))

  // Câu trả lời "đang hoạt động": cái người dùng chọn, hoặc câu mới nhất
  const answers = chat.messages.filter((m) => m.role === 'assistant' && !m.isError)
  const activeMessage = answers.find((m) => m.id === activeId) ?? answers[answers.length - 1] ?? null
  const activeIndex = activeMessage ? chat.messages.indexOf(activeMessage) : -1
  const activeQuestion = activeIndex > 0 ? chat.messages[activeIndex - 1].content : 'Research brief'

  const handleSend = (text) => {
    setActiveId(null) // quay về câu trả lời mới nhất
    chat.send(text, {
      documentIds: sources.documents ? contextDocs.map((d) => d.id) : [],
      sources,
    })
  }

  const handleNewChat = () => {
    chat.reset()
    setActiveId(null)
    setHighlight(null)
  }

  const handleShowEvidence = (messageId) => {
    setActiveId(messageId)
    setEvidenceOpen(true)
  }

  const handleCite = (messageId, n) => {
    setActiveId(messageId)
    setHighlight({ messageId, n, t: Date.now() }) // t để bấm lại cùng 1 nguồn vẫn kích hoạt
    setEvidenceOpen(true)
  }

  const handleExport = async (format) => {
    const { blob, filename } = await api.exportAnswer({
      format,
      title: activeQuestion,
      content: activeMessage.content,
      evidence: activeMessage.evidence,
    })
    downloadBlob(blob, filename)
  }

  const toggleSource = (key) => setSources((s) => ({ ...s, [key]: !s[key] }))

  return (
    <div className="flex h-full bg-white text-slate-800">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        docs={docs}
      />

      <main className="flex min-w-0 flex-1 flex-col bg-slate-50">
        <header className="flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Open documents"
          >
            <Menu className="h-5 w-5" />
          </button>

          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold text-slate-900">AI Research Assistant</h1>
            <p className="text-xs text-slate-500">
              {USE_MOCK ? 'Demo mode · mock data' : 'Connected to backend'}
            </p>
          </div>

          <ExportMenu disabled={!activeMessage} onExport={handleExport} />

          <button
            type="button"
            onClick={() => setEvidenceOpen(true)}
            className="relative rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 xl:hidden"
            aria-label="Open evidence"
          >
            <Library className="h-5 w-5" />
            {activeMessage?.evidence?.length > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-bold text-white">
                {activeMessage.evidence.length}
              </span>
            )}
          </button>
        </header>

        <div className="min-h-0 flex-1">
          <ChatWindow
            messages={chat.messages}
            isLoading={chat.isLoading}
            activeId={activeMessage?.id}
            onSuggest={handleSend}
            onCite={handleCite}
            onShowEvidence={handleShowEvidence}
          />
        </div>

        <ChatInput
          onSend={handleSend}
          disabled={chat.isLoading}
          sources={sources}
          onToggleSource={toggleSource}
          contextDocCount={contextDocs.length}
        />
      </main>

      <EvidencePanel
        open={evidenceOpen}
        onClose={() => setEvidenceOpen(false)}
        message={activeMessage}
        highlight={highlight}
      />
    </div>
  )
}
