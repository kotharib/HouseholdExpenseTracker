import { CssBaseline, ThemeProvider } from '@mui/material'
import { useMemo } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AuthPage from './pages/AuthPage'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import ExpensesPage from './pages/ExpensesPage'
import InvestmentsPage from './pages/InvestmentsPage'
import MilkPage from './pages/MilkPage'
import NewspaperPage from './pages/NewspaperPage'
import ReportsPage from './pages/ReportsPage'
import ServantsPage from './pages/ServantsPage'
import SettingsPage from './pages/SettingsPage'
import { useThemeStore } from './store/themeStore'
import { buildTheme } from './theme'

export default function App() {
  const mode = useThemeStore((s) => s.mode)
  const theme = useMemo(() => buildTheme(mode), [mode])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/investments" element={<InvestmentsPage />} />
            <Route path="/servants" element={<ServantsPage />} />
            <Route path="/milk" element={<MilkPage />} />
            <Route path="/newspaper" element={<NewspaperPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
