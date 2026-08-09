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
import { Savings as SavingsIcon } from '@mui/icons-material'
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
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        overflow: 'hidden',
        background: 'linear-gradient(120deg, #4f46e5 0%, #7c3aed 45%, #0891b2 100%)',
        backgroundSize: '200% 200%',
        animation: 'gradientShift 12s ease infinite',
      }}
    >
      <Box
        className="animate-float"
        sx={{
          position: 'absolute',
          top: '12%',
          left: '8%',
          width: 220,
          height: 220,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.08)',
          filter: 'blur(6px)',
        }}
      />
      <Box
        className="animate-float"
        sx={{
          position: 'absolute',
          bottom: '15%',
          right: '10%',
          width: 180,
          height: 180,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.1)',
          filter: 'blur(6px)',
          animationDelay: '1.2s',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: '55%',
          left: '55%',
          width: 120,
          height: 120,
          borderRadius: 4,
          background: 'rgba(255,255,255,0.06)',
          transform: 'rotate(20deg)',
        }}
      />
      <Card className="animate-fade-up" sx={{ width: '100%', maxWidth: 420, position: 'relative', zIndex: 1 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Box
              sx={{
                width: 42,
                height: 42,
                borderRadius: 3,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                boxShadow: '0 6px 16px rgba(79,70,229,0.35)',
              }}
            >
              <SavingsIcon fontSize="small" />
            </Box>
            <Typography variant="h5" fontWeight={800}>
              Household Finance
            </Typography>
          </Box>
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
