import { Alert, Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import NewspaperForm from '../components/NewspaperForm'
import NewspaperList from '../components/NewspaperList'
import type { NewspaperDailyResponse, NewspaperDay, NewspaperGroup, NewspaperInput } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function NewspaperPage() {
  const [month, setMonth] = useState(today())
  const [daily, setDaily] = useState<NewspaperDailyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

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

  const submit = async (data: NewspaperInput, _id?: number) => {
    setSubmitting(true)
    try {
      await api.post('/newspaper', data)
      setOpen(false)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const toggleDelivered = async (day: NewspaperDay, _group: NewspaperGroup) => {
    if (day.id == null) return
    try {
      await api.put(`/newspaper/${day.id}`, { delivery_status: !day.delivered })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const remove = async (day: NewspaperDay) => {
    if (day.id == null) return
    if (!window.confirm(`Delete newspaper delivery on ${day.date}?`)) return
    try {
      await api.delete(`/newspaper/${day.id}`)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const bulkDelete = async (ids: number[]) => {
    try {
      await api.post('/newspaper/bulk-delete', { ids })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deleteAll = async () => {
    try {
      await api.post('/newspaper/bulk-delete', { all: true })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Newspaper Deliveries
      </Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: 'center' }}>
        <TextField
          label="Month (YYYY-MM)"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          inputProps={{ maxLength: 7 }}
        />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          Add Newspaper
        </Button>
      </Stack>
      <DataState loading={loading} error={error} onRetry={() => load(month)} />
      {error && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {error}
        </Alert>
      )}
      {!loading && !error && daily && (
        <Card>
          <CardContent>
            <NewspaperList
              daily={daily}
              onToggleDelivered={toggleDelivered}
              onDelete={remove}
              onBulkDelete={bulkDelete}
              onDeleteAll={deleteAll}
            />
          </CardContent>
        </Card>
      )}
      <NewspaperForm
        open={open}
        initial={null}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
