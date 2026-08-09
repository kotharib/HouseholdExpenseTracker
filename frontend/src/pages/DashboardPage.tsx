import { Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DashboardCharts from '../components/DashboardCharts'
import DataState from '../components/DataState'
import type { DashboardSummary } from '../types'

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<DashboardSummary>('/dashboard/summary')
      setSummary(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <DataState loading={loading} error={error} onRetry={load} />
      {summary && <DashboardCharts summary={summary} />}
    </div>
  )
}
