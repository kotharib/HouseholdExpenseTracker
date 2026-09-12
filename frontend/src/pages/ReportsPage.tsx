import { Alert, Box, Button, Card, CardContent, Stack, Tab, Tabs, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import GraphSection from '../components/GraphSection'
import MonthlyReportCard from '../components/MonthlyReportCard'
import ReportViewer from '../components/ReportViewer'
import YearlyBillSummary from '../components/YearlyBillSummary'
import YearlyReportCard from '../components/YearlyReportCard'
import type { MonthlyExpenseReport, YearlyBillSummary as YearlyBillSummaryData, YearlyExpenseReport, YearlyGraphData } from '../types'

const todayMonth = () => new Date().toISOString().slice(0, 7)
const todayYear = () => String(new Date().getFullYear())

export default function ReportsPage() {
  const [tab, setTab] = useState(0)
  const [month, setMonth] = useState(todayMonth())
  const [year, setYear] = useState(todayYear())
  const [monthly, setMonthly] = useState<MonthlyExpenseReport | null>(null)
  const [yearly, setYearly] = useState<YearlyExpenseReport | null>(null)
  const [bills, setBills] = useState<YearlyBillSummaryData | null>(null)
  const [graphs, setGraphs] = useState<YearlyGraphData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const loadMonthly = async (value: string) => {
    const [y, m] = value.split('-')
    const res = await api.get<MonthlyExpenseReport>(`/reports/monthly/${y}/${m}`)
    setMonthly(res.data)
  }

  const loadYearly = async (value: string) => {
    const [yearRes, billRes, graphRes] = await Promise.all([
      api.get<YearlyExpenseReport>(`/reports/yearly/${value}`),
      api.get<YearlyBillSummaryData>(`/billing/yearly/${value}`),
      api.get<YearlyGraphData>(`/reports/graphs/yearly/${value}`),
    ])
    setYearly(yearRes.data)
    setBills(billRes.data)
    setGraphs(graphRes.data)
  }

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      if (tab === 0) {
        await loadMonthly(month)
      } else {
        await loadYearly(year)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Tabs value={tab} onChange={(_, value) => setTab(value)} sx={{ mb: 2 }}>
            <Tab label="Monthly Report" />
            <Tab label="Yearly Report" />
            <Tab label="Graphs & Trends" />
          </Tabs>
          <Stack direction="row" gap={1.5} alignItems="center" flexWrap="wrap">
            {tab === 0 ? (
              <TextField
                label="Month (YYYY-MM)"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                inputProps={{ maxLength: 7 }}
              />
            ) : (
              <TextField
                label="Year (YYYY)"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                inputProps={{ maxLength: 4 }}
              />
            )}
            <Button variant="contained" onClick={load} disabled={loading}>
              {loading ? 'Loading...' : 'Generate'}
            </Button>
          </Stack>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      <DataState loading={loading} error="" />
      {!loading && tab === 0 && monthly && <MonthlyReportCard report={monthly} />}
      {!loading && tab === 1 && yearly && (
        <Box>
          <YearlyReportCard report={yearly} />
          {bills && (
            <Box sx={{ mt: 3 }}>
              <YearlyBillSummary data={bills} />
            </Box>
          )}
        </Box>
      )}
      {!loading && tab === 2 && graphs && <GraphSection data={graphs} />}

      {tab === 0 && (
        <Box sx={{ mt: 3 }}>
          <ReportViewer />
        </Box>
      )}
    </div>
  )
}
