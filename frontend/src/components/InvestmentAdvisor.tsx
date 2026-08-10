import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { AutoAwesome as AutoAwesomeIcon } from '@mui/icons-material'
import { useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import type { AdvisorResponse, InvestmentOption, RiskProfile } from '../types'
import { formatMoney } from '../utils/format'

const ASSET_COLORS: Record<string, string> = {
  government: '#4f46e5',
  bank: '#0891b2',
  debt: '#7c3aed',
  gold: '#d97706',
  equity: '#16a34a',
}

const RISK_CHIP_COLOR: Record<string, 'success' | 'warning' | 'error'> = {
  low: 'success',
  medium: 'warning',
  high: 'error',
}

export default function InvestmentAdvisor() {
  const [amount, setAmount] = useState('100000')
  const [profile, setProfile] = useState('moderate')
  const [result, setResult] = useState<AdvisorResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const advise = async () => {
    const parsed = Number(amount)
    if (!parsed || parsed <= 0) {
      setError('Please enter a valid amount greater than zero.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.post<AdvisorResponse>('/investments/advisor', {
        amount: parsed,
        profile,
      })
      setResult(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const profiles: RiskProfile[] = result?.profiles ?? [
    { key: 'conservative', label: 'Conservative' },
    { key: 'moderate', label: 'Moderate' },
    { key: 'aggressive', label: 'Aggressive' },
  ]

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
          <AutoAwesomeIcon color="primary" />
          <Typography variant="h6">Investment Advisor</Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Get a suggested asset allocation for a lump-sum investment based on your risk profile.
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 1 }}>
          <TextField
            label="Amount to invest (₹)"
            type="number"
            inputProps={{ step: '0.01', min: 1 }}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            sx={{ flex: 1 }}
          />
          <FormControl sx={{ flex: 1 }}>
            <InputLabel>Risk Profile</InputLabel>
            <Select value={profile} onChange={(e) => setProfile(e.target.value)} label="Risk Profile">
              {profiles.map((p) => (
                <MenuItem key={p.key} value={p.key}>
                  {p.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button variant="contained" onClick={advise} disabled={loading} sx={{ alignSelf: { xs: 'stretch', sm: 'center' } }}>
            {loading ? 'Computing...' : 'Get Allocation'}
          </Button>
        </Stack>
        {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}

        {result && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
              Suggested allocation for {formatMoney(result.allocation.total)}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {result.allocation.description}
            </Typography>
            <Stack spacing={1.5}>
              {result.allocation.items.map((item) => (
                <Box key={item.asset_class}>
                  <Stack direction="row" justifyContent="space-between">
                    <Typography variant="body2">{item.label}</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {item.percent}% · {formatMoney(item.amount)}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={item.percent}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: `${ASSET_COLORS[item.asset_class] ?? '#64748b'}33`,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: ASSET_COLORS[item.asset_class] ?? '#64748b',
                        borderRadius: 4,
                      },
                    }}
                  />
                </Box>
              ))}
            </Stack>

            <Typography variant="subtitle1" sx={{ fontWeight: 700, mt: 3, mb: 1 }}>
              Representative schemes
            </Typography>
            <Stack spacing={1}>
              {result.schemes.map((scheme: InvestmentOption) => (
                <Box key={scheme.key} sx={{ p: 1.5, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
                    <Typography variant="body2" fontWeight={600}>
                      {scheme.name}
                    </Typography>
                    <Chip label={`~${scheme.expected_return}%`} size="small" color={RISK_CHIP_COLOR[scheme.risk] ?? 'default'} />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    {scheme.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Lock-in: {scheme.lock_in} · {scheme.tax_benefit}
                  </Typography>
                </Box>
              ))}
            </Stack>

            <Alert severity="info" sx={{ mt: 2 }}>
              {result.disclaimer}
            </Alert>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
