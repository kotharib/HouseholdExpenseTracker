import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Paper,
} from '@mui/material'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getErrorMessage } from '../api/client'
import { useAuthStore } from '../store/authStore'
import type { AuthResponse } from '../types'

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post<AuthResponse>(
        mode === 'login' ? '/auth/login' : '/auth/register',
        { username, password },
      )
      setAuth(res.data.access_token, res.data.user)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" fontWeight={700} gutterBottom>
            Household Finance Manager
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Expense tracking, salaries, deliveries and an AI assistant.
          </Typography>

          <Paper sx={{ display: 'flex', mb: 3 }}>
            <Button
              fullWidth
              variant={mode === 'login' ? 'contained' : 'text'}
              onClick={() => setMode('login')}
            >
              Login
            </Button>
            <Button
              fullWidth
              variant={mode === 'register' ? 'contained' : 'text'}
              onClick={() => setMode('register')}
            >
              Register
            </Button>
          </Paper>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={submit}>
            <TextField
              label="Username"
              fullWidth
              margin="normal"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              sx={{ mt: 3 }}
              disabled={loading}
            >
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <Typography variant="caption" color="text.secondary" display="block" mt={2}>
            Demo: admin / admin123 (or demo / demo123)
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
