import { Alert, Card, CardContent, Snackbar, Stack, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import NewspaperList from '../components/NewspaperList'
import type { NewspaperDailyResponse, NewspaperDay } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function NewspaperPage() {
  const [month, setMonth] = useState(today())
  const [daily, setDaily] = useState<NewspaperDailyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const year = m.slice(0, 4)
      const monthNum = m.slice(5, 7)
      const res = await api.get<NewspaperDailyResponse>(`/newspaper/deliveries/${year}/${monthNum}`)
      setDaily(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
  }, [month])

  const markStatus = async (day: NewspaperDay, delivered: boolean) => {
    if (day.id == null) return
    try {
      await api.patch(`/deliveries/${day.id}/status`, { delivered, delivery_type: 'newspaper' })
      setDaily((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          newspapers: prev.newspapers.map((group) => ({
            ...group,
            days: group.days.map((item) => (item.id === day.id ? { ...item, delivered } : item)),
          })),
        }
      })
      setToast(delivered ? 'Marked as delivered.' : 'Marked as not delivered.')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Newspaper Deliveries
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Rows are generated from your newspaper subscriptions. Mark each scheduled day as delivered or not delivered.
      </Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: 'center' }}>
        <TextField
          label="Month (YYYY-MM)"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          inputProps={{ maxLength: 7 }}
        />
      </Stack>
      <DataState loading={loading} error={error} onRetry={() => load(month)} />
      {!loading && !error && daily && (
        <Card>
          <CardContent>
            <NewspaperList daily={daily} onMarkStatus={markStatus} />
          </CardContent>
        </Card>
      )}
      <Snackbar open={Boolean(toast)} autoHideDuration={2500} onClose={() => setToast('')}>
        <Alert severity="success" onClose={() => setToast('')} variant="filled">
          {toast}
        </Alert>
      </Snackbar>
    </div>
  )
}
