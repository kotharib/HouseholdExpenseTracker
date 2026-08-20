import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import { TrendingUp as TrendingUpIcon } from '@mui/icons-material'
import { useCallback, useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import type { MarketSuggestions, MutualFundSuggestion } from '../types'

function returnLabel(value: number | null): string {
  return value === null ? 'n/a' : `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function returnColor(value: number | null): 'success' | 'error' | 'default' {
  if (value === null) return 'default'
  return value >= 0 ? 'success' : 'error'
}

export default function MarketSuggestions() {
  const [data, setData] = useState<MarketSuggestions | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<MarketSuggestions>('/investments/market/suggest', {
        params: { limit: 6 },
      })
      setData(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
          <TrendingUpIcon color="success" />
          <Typography variant="h6">Top Mutual Funds (Live Market)</Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Best-performing funds based on the current market value (live NAV).
        </Typography>

        {loading && <LinearProgress sx={{ mt: 2 }} />}
        {error && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="error">{error}</Alert>
            <Button variant="outlined" size="small" onClick={load} sx={{ mt: 1 }}>
              Retry
            </Button>
          </Box>
        )}

        {data && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1.5 }}>
              NAV as of {data.as_of} · source: {data.source}
            </Typography>
            <Stack spacing={1}>
              {data.funds.map((fund: MutualFundSuggestion, idx: number) => (
                <Box
                  key={fund.code}
                  sx={{ p: 1.5, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
                    <Typography variant="body2" fontWeight={600}>
                      {idx + 1}. {fund.name}
                    </Typography>
                    <Chip label={fund.category} size="small" variant="outlined" />
                  </Stack>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 0.5 }} flexWrap="wrap" gap={1}>
                    <Typography variant="caption" color="text.secondary">
                      NAV ₹{fund.nav.toFixed(4)} ({fund.nav_date})
                    </Typography>
                    <Stack direction="row" spacing={0.75}>
                      <Chip label={`1M ${returnLabel(fund.returns['1m'])}`} size="small" color={returnColor(fund.returns['1m'])} variant="outlined" />
                      <Chip label={`3M ${returnLabel(fund.returns['3m'])}`} size="small" color={returnColor(fund.returns['3m'])} variant="outlined" />
                      <Chip label={`6M ${returnLabel(fund.returns['6m'])}`} size="small" color={returnColor(fund.returns['6m'])} variant="outlined" />
                      <Chip label={`1Y ${returnLabel(fund.returns['1y'])}`} size="small" color={returnColor(fund.returns['1y'])} variant="outlined" />
                    </Stack>
                  </Stack>
                </Box>
              ))}
            </Stack>
            <Alert severity="info" sx={{ mt: 2 }}>
              {data.disclaimer}
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
