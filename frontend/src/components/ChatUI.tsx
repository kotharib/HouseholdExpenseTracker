import { Box, Button, Card, CardContent, Paper, TextField, Typography, useTheme } from '@mui/material'
import { Send as SendIcon } from '@mui/icons-material'
import { useEffect, useRef, useState } from 'react'
import { getErrorMessage } from '../api/client'
import { useAuthStore } from '../store/authStore'
import type { ChatMessage } from '../types'

function parseSse(reader: ReadableStreamDefaultReader<Uint8Array>, onToken: (text: string) => void): Promise<void> {
  const decoder = new TextDecoder()
  let buffer = ''
  return reader.read().then(function process({ done, value }): Promise<void> {
    if (done) return Promise.resolve()
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const match = /^data: (.*)$/m.exec(line)
      if (!match) continue
      try {
        const data = JSON.parse(match[1])
        if (data.token !== undefined) onToken(data.token)
      } catch {
        // ignore malformed frames
      }
    }
    return reader.read().then(process)
  })
}

export default function ChatUI() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState('')
  const token = useAuthStore((s) => s.token)
  const theme = useTheme()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  const send = async () => {
    const text = input.trim()
    if (!text || streaming) return
    setError('')
    setInput('')
    const userMsg: ChatMessage = { role: 'user', content: text }
    const history = [...messages]
    setMessages([...messages, userMsg, { role: 'assistant', content: '' }])
    setStreaming(true)

    const placeholderId = history.length + 1
    const update = (content: string) =>
      setMessages((prev) => prev.map((m, i) => (i === placeholderId ? { ...m, content } : m)))

    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token ?? ''}` },
        body: JSON.stringify({ message: text, history }),
      })
      if (!res.ok || !res.body) {
        const body = await res.text().catch(() => '')
        throw new Error(body || `HTTP ${res.status}`)
      }
      await parseSse(res.body.getReader(), update)
    } catch (err) {
      update(getErrorMessage(err))
      setError(getErrorMessage(err))
    } finally {
      setStreaming(false)
    }
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          AI Finance Assistant
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={2}>
          Ask about spending, salaries, milk/newspaper bills, insights and monthly reports. Backed by
          LangChain + local Llama 3 (Ollama) when available.
        </Typography>

        <Box sx={{ height: 420, overflowY: 'auto', mb: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
          {messages.length === 0 && (
            <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 8 }}>
              Say hello and ask something like “Which servant salary is pending?”
            </Typography>
          )}
          {messages.map((m, i) => (
            <Box
              key={i}
              className="animate-fade-up"
              sx={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}
            >
              <Paper
                className="chat-bubble"
                sx={{
                  p: 1.5,
                  background:
                    m.role === 'user'
                      ? theme.palette.mode === 'light'
                        ? 'linear-gradient(135deg, #4f46e5, #7c3aed)'
                        : 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                      : theme.palette.background.default,
                  color: m.role === 'user' ? '#fff' : theme.palette.text.primary,
                  boxShadow: m.role === 'user' ? '0 6px 14px rgba(79,70,229,0.3)' : undefined,
                }}
              >
                {m.content}
                {m.role === 'assistant' && streaming && i === messages.length - 1 && (
                  <span className="typing-indicator" style={{ color: 'inherit' }}>
                    <span />
                    <span />
                    <span />
                  </span>
                )}
              </Paper>
            </Box>
          ))}
          <div ref={bottomRef} />
        </Box>

        {error && (
          <Typography color="error" variant="caption" display="block" mb={1}>
            {error}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Type a question about your household finances..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            disabled={streaming}
          />
          <Button variant="contained" onClick={send} disabled={!input.trim() || streaming} endIcon={<SendIcon />}>
            Send
          </Button>
        </Box>
      </CardContent>
    </Card>
  )
}
