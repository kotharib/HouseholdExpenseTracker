import { Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import ExpenseForm from '../components/ExpenseForm'
import ExpenseList from '../components/ExpenseList'
import type { Expense, ExpenseInput } from '../types'

const today = () => new Date().toISOString().slice(0, 7)

export default function ExpensesPage() {
  const [month, setMonth] = useState(today())
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Expense | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<Expense[]>('/expenses', { params: { month: m } })
      setExpenses(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month])

  const submit = async (data: ExpenseInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/expenses/${id}`, data)
      } else {
        await api.post('/expenses', data)
      }
      setOpen(false)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const remove = async (expense: Expense) => {
    if (!window.confirm(`Delete expense of ${expense.category}?`)) return
    try {
      await api.delete(`/expenses/${expense.id}`)
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const bulkDelete = async (ids: number[]) => {
    try {
      await api.post('/expenses/bulk-delete', { ids })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deleteAll = async () => {
    try {
      await api.post('/expenses/bulk-delete', { all: true })
      load(month)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Expenses
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
          Add Expense
        </Button>
      </Stack>
      <DataState loading={loading} error={error} onRetry={() => load(month)} />
      {!loading && !error && (
        <Card>
          <CardContent>
            <ExpenseList
              expenses={expenses}
              onEdit={(e) => {
                setEditing(e)
                setOpen(true)
              }}
              onDelete={remove}
              onBulkDelete={bulkDelete}
              onDeleteAll={deleteAll}
            />
          </CardContent>
        </Card>
      )}
      <ExpenseForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
