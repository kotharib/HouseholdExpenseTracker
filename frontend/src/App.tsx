import { CssBaseline, ThemeProvider } from '@mui/material'
import { useMemo } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AccessDeniedPage from './pages/AccessDeniedPage'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AuthPage from './pages/AuthPage'
import BillingPage from './pages/BillingPage'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import ExpensesPage from './pages/ExpensesPage'
import InvestmentsPage from './pages/InvestmentsPage'
import MilkPage from './pages/MilkPage'
import NewspaperPage from './pages/NewspaperPage'
import ReportsPage from './pages/ReportsPage'
import SubscriptionsPage from './pages/SubscriptionsPage'
import ServantsPage from './pages/ServantsPage'
import SettingsPage from './pages/SettingsPage'
import { useThemeStore } from './store/themeStore'
import { buildTheme } from './theme'
import type { Role } from './types'

const MANAGER_ROLES: Role[] = ['admin', 'user']

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
            <Route
              path="/expenses"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <ExpensesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/investments"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <InvestmentsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/servants"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <ServantsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/milk"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <MilkPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/newspaper"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <NewspaperPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/subscriptions"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <SubscriptionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/billing"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <BillingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <ChatPage />
                </ProtectedRoute>
              }
            />
            <Route path="/reports" element={<ReportsPage />} />
            <Route
              path="/settings"
              element={
                <ProtectedRoute roles={MANAGER_ROLES}>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route path="/access-denied" element={<AccessDeniedPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
