import { Button, Card, CardContent, Stack, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import ServantForm from '../components/ServantForm'
import ServantList from '../components/ServantList'
import type { Servant, ServantInput } from '../types'

export default function ServantsPage() {
  const [servants, setServants] = useState<Servant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Servant | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<Servant[]>('/servants')
      setServants(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async (data: ServantInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/servants/${id}`, data)
      } else {
        await api.post('/servants', data)
      }
      setOpen(false)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const remove = async (servant: Servant) => {
    if (!window.confirm(`Delete servant ${servant.name}?`)) return
    try {
      await api.delete(`/servants/${servant.id}`)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const bulkDelete = async (ids: number[]) => {
    try {
      await api.post('/servants/bulk-delete', { ids })
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deleteAll = async () => {
    try {
      await api.post('/servants/bulk-delete', { all: true })
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Servants
      </Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditing(null)
            setOpen(true)
          }}
        >
          Add Servant
        </Button>
      </Stack>
      <DataState loading={loading} error={error} onRetry={load} />
      {!loading && !error && (
        <Card>
          <CardContent>
            <ServantList
              servants={servants}
              onEdit={(s) => {
                setEditing(s)
                setOpen(true)
              }}
              onDelete={remove}
              onBulkDelete={bulkDelete}
              onDeleteAll={deleteAll}
            />
          </CardContent>
        </Card>
      )}
      <ServantForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
