import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  useTheme,
} from '@mui/material'
import {
  AccountBalanceWallet as WalletIcon,
  Download as DownloadIcon,
  Insights as InsightsIcon,
  Psychology as PsychologyIcon,
  Receipt as ReceiptIcon,
  TrendingDown as TrendingDownIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import type { AiMonthlyReport, AutoReport } from '../types'
import { formatMoney } from '../utils/format'
import { useCountUp } from '../utils/useCountUp'

const today = () => new Date().toISOString().slice(0, 7)

const STATUS_COLOR: Record<string, 'success' | 'warning'> = { paid: 'success', pending: 'warning' }

function MiniMetric({
  icon,
  label,
  value,
  color,
  delay,
}: {
  icon: React.ReactNode
  label: string
  value: number
  color?: string
  delay?: number
}) {
  const animated = useCountUp(value)
  return (
    <Card className="animate-fade-up" sx={{ height: '100%', animationDelay: `${delay ?? 0}ms` }}>
      <CardContent>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 42,
              height: 42,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              background: `linear-gradient(135deg, ${color ?? '#4f46e5'}, ${color ?? '#4f46e5'}99)`,
              boxShadow: `0 6px 14px ${color ?? '#4f46e5'}44`,
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={800} sx={{ color: color ?? 'inherit' }}>
              {formatMoney(animated)}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default function ReportViewer() {
  const [month, setMonth] = useState(today())
  const [auto, setAuto] = useState<AutoReport | null>(null)
  const [aiReport, setAiReport] = useState<AiMonthlyReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const theme = useTheme()

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [autoRes, aiRes] = await Promise.all([
        api.get<AutoReport>('/reports/auto', { params: { month } }),
        api.get<AiMonthlyReport>('/ai/report/monthly', { params: { month } }),
      ])
      setAuto(autoRes.data)
      setAiReport(aiRes.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const downloadPdf = async () => {
    try {
      const res = await api.get<Blob>('/reports/monthly/pdf', {
        params: { month },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `household-report-${month}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const deltaColor = auto ? (auto.delta > 0 ? theme.palette.error.main : theme.palette.success.main) : undefined

  return (
    <Box>
      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
            <Typography variant="h6">Monthly Reports</Typography>
            <Stack direction="row" gap={1.5} alignItems="center" flexWrap="wrap">
              <TextField
                label="Month (YYYY-MM)"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                inputProps={{ maxLength: 7 }}
              />
              <Button variant="contained" onClick={load} disabled={loading}>
                {loading ? 'Loading...' : 'Generate'}
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />} onClick={downloadPdf} disabled={loading}>
                Download PDF
              </Button>
            </Stack>
          </Stack>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {auto && (
        <>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={6} md={3}>
              <MiniMetric icon={<WalletIcon fontSize="small" />} label="Total expenses" value={auto.totals.total_expenses} color="#4f46e5" delay={0} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MiniMetric icon={<ReceiptIcon fontSize="small" />} label="Transactions" value={auto.expense_count} color="#0891b2" delay={70} />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MiniMetric
                icon={auto.delta > 0 ? <TrendingUpIcon fontSize="small" /> : <TrendingDownIcon fontSize="small" />}
                label="Vs last month"
                value={auto.delta}
                color={deltaColor}
                delay={140}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <MiniMetric icon={<InsightsIcon fontSize="small" />} label="Pending payments" value={auto.totals.pending} color="#d97706" delay={210} />
            </Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} md={7}>
              <Card className="animate-fade-up" sx={{ height: '100%', animationDelay: '140ms' }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={0.5}>
                    <ReceiptIcon color="primary" fontSize="small" />
                    <Typography variant="h6">{auto.title}</Typography>
                  </Stack>
                  <Typography variant="caption" color="text.secondary" display="block" mb={1.5}>
                    Generated on {auto.generated_at}
                  </Typography>
                  <Divider sx={{ mb: 1.5 }} />
                  <Stack spacing={1.25}>
                    {auto.sections.map((s, i) => (
                      <Box
                        key={i}
                        className="animate-slide-in"
                        sx={{
                          display: 'flex',
                          gap: 1,
                          p: 1,
                          borderRadius: 2,
                          backgroundColor: theme.palette.mode === 'light' ? 'rgba(79,70,229,0.05)' : 'rgba(129,140,248,0.08)',
                          animationDelay: `${160 + i * 60}ms`,
                        }}
                      >
                        <Typography variant="body2">{s}</Typography>
                      </Box>
                    ))}
                  </Stack>

                  {auto.category_totals.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                        Category breakdown
                      </Typography>
                      <Stack spacing={1}>
                        {auto.category_totals.map((c, i) => {
                          const pct = (c.total / auto.totals.total_expenses) * 100
                          return (
                            <Box key={c.category}>
                              <Stack direction="row" justifyContent="space-between" mb={0.25}>
                                <Typography variant="caption">{c.category}</Typography>
                                <Typography variant="caption" fontWeight={700}>
                                  {formatMoney(c.total)} · {pct.toFixed(0)}%
                                </Typography>
                              </Stack>
                              <Box
                                sx={{
                                  height: 8,
                                  borderRadius: 4,
                                  backgroundColor: theme.palette.divider,
                                  overflow: 'hidden',
                                }}
                              >
                                <Box
                                  className="animate-fade-in"
                                  sx={{
                                    height: '100%',
                                    width: `${Math.min(pct, 100)}%`,
                                    borderRadius: 4,
                                    background: `linear-gradient(90deg, ${['#4f46e5', '#7c3aed', '#0891b2', '#d97706', '#059669', '#dc2626'][i % 6]}, transparent)`,
                                  }}
                                />
                              </Box>
                            </Box>
                          )
                        })}
                      </Stack>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={5}>
              <Stack spacing={2}>
                <Card className="animate-fade-up" sx={{ animationDelay: '200ms' }}>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                      <PsychologyIcon color="secondary" fontSize="small" />
                      <Typography variant="h6">AI Monthly Summary</Typography>
                    </Stack>
                    <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: 13, fontFamily: 'inherit' }}>
                      {aiReport?.report}
                    </Box>
                    <Chip
                      size="small"
                      label={aiReport?.llm_available ? 'Ollama llama3' : 'Fallback engine'}
                      color={aiReport?.llm_available ? 'success' : 'warning'}
                    />
                  </CardContent>
                </Card>

                <Card className="animate-fade-up" sx={{ animationDelay: '260ms' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Pending Payments
                    </Typography>
                    {auto.pending.length === 0 ? (
                      <Typography color="text.secondary">All payments cleared. Nice!</Typography>
                    ) : (
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Type</TableCell>
                              <TableCell>Name</TableCell>
                              <TableCell align="right">Amount</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {auto.pending.map((p) => (
                              <TableRow key={`${p.type}-${p.name}`} hover>
                                <TableCell>
                                  <Chip label={p.type} size="small" color={STATUS_COLOR[p.type] ?? 'default'} variant="outlined" />
                                </TableCell>
                                <TableCell>
                                  {p.name} {p.month && `(${p.month})`}
                                </TableCell>
                                <TableCell align="right">
                                  <Typography fontWeight={700}>{formatMoney(p.amount)}</Typography>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </CardContent>
                </Card>
              </Stack>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  )
}
