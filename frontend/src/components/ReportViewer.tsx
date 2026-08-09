import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  TextField,
  Typography,
} from '@mui/material'
import { Download as DownloadIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import type { AiMonthlyReport, AutoReport } from '../types'
import { formatMoney } from '../utils/format'

const today = () => new Date().toISOString().slice(0, 7)

export default function ReportViewer() {
  const [month, setMonth] = useState(today())
  const [auto, setAuto] = useState<AutoReport | null>(null)
  const [aiReport, setAiReport] = useState<AiMonthlyReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Monthly Reports
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap' }}>
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
          </Box>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {auto && (
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6">{auto.title}</Typography>
                <Divider sx={{ my: 1 }} />
                {auto.sections.map((s, i) => (
                  <Typography key={i} variant="body2" paragraph>
                    {s}
                  </Typography>
                ))}
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2">
                  Totals: expenses <strong>{formatMoney(auto.totals.total_expenses)}</strong> · pending{' '}
                  <strong>{formatMoney(auto.totals.pending)}</strong>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6">AI Monthly Summary</Typography>
                <Divider sx={{ my: 1 }} />
                <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
                  {aiReport?.report}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  LLM available: {aiReport?.llm_available ? 'yes (Ollama llama3)' : 'no (fallback engine)'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}
