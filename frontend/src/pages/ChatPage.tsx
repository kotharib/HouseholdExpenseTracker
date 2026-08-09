import { Typography } from '@mui/material'
import ChatUI from '../components/ChatUI'

export default function ChatPage() {
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        AI Chat
      </Typography>
      <ChatUI />
    </div>
  )
}
