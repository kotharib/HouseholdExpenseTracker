import { Box, Card, CardContent, Grid, Stack, TextField, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DashboardCharts from '../components/DashboardCharts'
import DataState from '../components/DataState'
import GraphVisuals from '../components/GraphVisuals'
import TrendGraph from '../components/TrendGraph'
import YearlyBillSummary from '../components/YearlyBillSummary'
import YearlyReportCard from '../components/YearlyReportCard'
import type { DashboardSummary, YearlyBillSummary as YearlyBillSummaryData, YearlyExpenseReport, YearlyGraphData } from '../types'

const currentYear = () => String(new Date().getFullYear())

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [yearly, setYearly] = useState<YearlyExpenseReport | null>(null)
  const [bills, setBills] = useState<YearlyBillSummaryData | null>(null)
  const [graphs, setGraphs] = useState<YearlyGraphData | null>(null)
  const [year, setYear] = useState(currentYear())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [summaryRes, yearlyRes, billRes, graphRes] = await Promise.all([
        api.get<DashboardSummary>('/dashboard/summary'),
        api.get<YearlyExpenseReport>(`/reports/yearly/${year}`),
        api.get<YearlyBillSummaryData>(`/billing/yearly/${year}`),
        api.get<YearlyGraphData>(`/reports/graphs/yearly/${year}`),
      ])
      setSummary(summaryRes.data)
      setYearly(yearlyRes.data)
      setBills(billRes.data)
      setGraphs(graphRes.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year])

  return (
    <div>
      <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1} mb={1}>
        <Typography variant="h4">Dashboard</Typography>
        <TextField
          label="Year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          inputProps={{ maxLength: 4 }}
          size="small"
          sx={{ width: 120 }}
        />
      </Stack>
      <DataState loading={loading} error={error} onRetry={load} />
      {summary && <DashboardCharts summary={summary} />}
      {!loading && yearly && graphs && bills && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Yearly Overview
          </Typography>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={6}>
              <TrendGraph
                title="Monthly Trend Graph"
                months={graphs.months}
                series={[{ key: 'monthly_expenses', label: 'Expenses', color: '#4f46e5' }]}
                values={{ monthly_expenses: graphs.monthly_expenses }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TrendGraph
                title="Yearly Trend Graph"
                months={graphs.months}
                series={[
                  { key: 'monthly_expenses', label: 'Expenses', color: '#d97706' },
                  { key: 'milk_cost', label: 'Milk', color: '#0d9488' },
                  { key: 'newspaper_cost', label: 'Newspaper', color: '#7c3aed' },
                  { key: 'grand_total', label: 'Grand total', color: '#4f46e5' },
                ]}
                values={{
                  monthly_expenses: graphs.monthly_expenses,
                  milk_cost: graphs.milk_cost,
                  newspaper_cost: graphs.newspaper_cost,
                  grand_total: graphs.grand_total,
                }}
              />
            </Grid>
          </Grid>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <YearlyBillSummary data={bills} />
            </CardContent>
          </Card>
          <YearlyReportCard report={yearly} />
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Graphs & Trends
            </Typography>
            <GraphVisuals data={graphs} />
          </Box>
        </Box>
      )}
    </div>
  )
}
