import { Button, Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import InvestmentAdvisor from '../components/InvestmentAdvisor'
import InvestmentForm from '../components/InvestmentForm'
import InvestmentList from '../components/InvestmentList'
import MarketSuggestions from '../components/MarketSuggestions'
import type { Investment, InvestmentInput, InvestmentSummary } from '../types'
import { formatMoney } from '../utils/format'
import { investmentCategoryLabelsFull } from '../utils/investmentCategories'

export default function InvestmentsPage() {
  const [investments, setInvestments] = useState<Investment[]>([])
  const [summary, setSummary] = useState<InvestmentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Investment | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [listRes, summaryRes] = await Promise.all([
        api.get<Investment[]>('/investments'),
        api.get<InvestmentSummary>('/investments/summary'),
      ])
      setInvestments(listRes.data)
      setSummary(summaryRes.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async (data: InvestmentInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/investments/${id}`, data)
      } else {
        await api.post('/investments', data)
      }
      setOpen(false)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const remove = async (investment: Investment) => {
    if (!window.confirm(`Delete ${investment.scheme_name}?`)) return
    try {
      await api.delete(`/investments/${investment.id}`)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const bulkDelete = async (ids: number[]) => {
    try {
      await api.post('/investments/bulk-delete', { ids })
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deleteAll = async () => {
    try {
      await api.post('/investments/bulk-delete', { all: true })
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Investments
      </Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 2, alignItems: 'center' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditing(null)
            setOpen(true)
          }}
        >
          Add Investment
        </Button>
        {summary && summary.count > 0 && (
          <Typography variant="body2" color="text.secondary">
            Total invested: <strong>{formatMoney(summary.total)}</strong> ({summary.count} records)
          </Typography>
        )}
      </Stack>

      {summary && summary.count > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
          {Object.entries(summary.by_category).slice(0, 8).map(([cat, val]) => (
            <Chip
              key={cat}
              label={`${investmentCategoryLabelsFull[cat] ?? cat}: ${formatMoney(val)}`}
              variant="outlined"
              size="small"
            />
          ))}
        </Stack>
      )}

      <DataState loading={loading} error={error} onRetry={load} />
      {!loading && !error && (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card>
              <CardContent>
                <InvestmentList
                  investments={investments}
                  onEdit={(inv) => {
                    setEditing(inv)
                    setOpen(true)
                  }}
                  onDelete={remove}
                  onBulkDelete={bulkDelete}
                  onDeleteAll={deleteAll}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} lg={4}>
            <Stack spacing={3}>
              <InvestmentAdvisor />
              <MarketSuggestions />
            </Stack>
          </Grid>
        </Grid>
      )}
      <InvestmentForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
    </div>
  )
}
