import { Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import MilkForm from '../components/MilkForm'
import MilkList from '../components/MilkList'
import type { Milk, MilkInput } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function MilkPage() {
  const [month, setMonth] = useState(today())
  const [deliveries, setDeliveries] = useState<Milk[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Milk | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<Milk[]>('/milk', { params: { month: m } })
      setDeliveries(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
  }, [month])

  const submit = async (data: MilkInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/milk/${id}`, data)
      } else {
        await api.post('/milk', data)
      }
      setOpen(false)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const remove = async (delivery: Milk) => {
    if (!window.confirm(`Delete milk delivery from ${delivery.supplier}?`)) return
    try {
      await api.delete(`/milk/${delivery.id}`)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const bulkDelete = async (ids: number[]) => {
    try {
      await api.post('/milk/bulk-delete', { ids })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deleteAll = async () => {
    try {
      await api.post('/milk/bulk-delete', { all: true })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const toggleDelivered = async (delivery: Milk) => {
    try {
      await api.put(`/milk/${delivery.id}`, { is_delivered: !delivery.is_delivered })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Milk Deliveries
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
          onClick={() => {
            setEditing(null)
            setOpen(true)
          }}
        >
          Add Delivery
        </Button>
      </Stack>
      <DataState loading={loading} error={error} onRetry={() => load(month)} />
      {!loading && !error && (
        <Card>
          <CardContent>
            <MilkList
              deliveries={deliveries}
              onEdit={(d) => {
                setEditing(d)
                setOpen(true)
              }}
              onDelete={remove}
              onBulkDelete={bulkDelete}
              onDeleteAll={deleteAll}
              onToggleDelivered={toggleDelivered}
            />
          </CardContent>
        </Card>
      )}
      <MilkForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
