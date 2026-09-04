import { Alert, Card, CardContent, Snackbar, Stack, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import MilkList from '../components/MilkList'
import type { Milk } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function MilkPage() {
  const [month, setMonth] = useState(today())
  const [deliveries, setDeliveries] = useState<Milk[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const year = m.slice(0, 4)
      const monthNum = m.slice(5, 7)
      const res = await api.get(`/milk/deliveries/${year}/${monthNum}`)
      const days = (res.data?.days ?? []) as Array<Milk & { delivered?: boolean | null; supplier: string }>
      setDeliveries(
        days.map((d) => ({
          id: d.id as number,
          supplier: d.supplier,
          quantity: d.quantity,
          rate: d.rate,
          date: d.date,
          month: m,
          is_delivered: d.delivered ?? d.is_delivered ?? null,
          payment_status: d.payment_status,
          total: d.total,
          subscription_id: d.subscription_id,
        })),
      )
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
  }, [month])

  const markStatus = async (delivery: Milk, delivered: boolean) => {
    try {
      await api.patch(`/deliveries/${delivery.id}/status`, { delivered, delivery_type: 'milk' })
      setDeliveries((prev) => prev.map((row) => (row.id === delivery.id ? { ...row, is_delivered: delivered } : row)))
      setToast(delivered ? 'Marked as delivered.' : 'Marked as not delivered.')
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Milk Deliveries
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Rows are generated from your milk subscriptions. Mark each day as delivered or not delivered.
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
      {!loading && !error && (
        <Card>
          <CardContent>
            <MilkList deliveries={deliveries} onMarkStatus={markStatus} />
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
