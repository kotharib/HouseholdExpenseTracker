import { Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import NewspaperForm from '../components/NewspaperForm'
import NewspaperList from '../components/NewspaperList'
import type { Newspaper, NewspaperInput } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function NewspaperPage() {
  const [month, setMonth] = useState(today())
  const [papers, setPapers] = useState<Newspaper[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Newspaper | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<Newspaper[]>('/newspaper', { params: { month: m } })
      setPapers(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
  }, [month])

  const submit = async (data: NewspaperInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/newspaper/${id}`, data)
      } else {
        await api.post('/newspaper', data)
      }
      setOpen(false)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const remove = async (paper: Newspaper) => {
    if (!window.confirm(`Delete subscription ${paper.name}?`)) return
    try {
      await api.delete(`/newspaper/${paper.id}`)
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
          onClick={() => {
            setEditing(null)
            setOpen(true)
          }}
        >
          Add Newspaper
        </Button>
      </Stack>
      <DataState loading={loading} error={error} onRetry={() => load(month)} />
      {!loading && !error && (
        <Card>
          <CardContent>
            <NewspaperList
              papers={papers}
              onEdit={(p) => {
                setEditing(p)
                setOpen(true)
              }}
              onDelete={remove}
              onBulkDelete={bulkDelete}
              onDeleteAll={deleteAll}
            />
          </CardContent>
        </Card>
      )}
      <NewspaperForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
