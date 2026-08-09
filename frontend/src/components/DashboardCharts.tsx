import { Box, Card, CardContent, Grid, Typography, useTheme } from '@mui/material'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DashboardSummary } from '../types'
import { formatMoney } from '../utils/format'

const COLORS = ['#2563eb', '#7c3aed', '#f59e0b', '#16a34a', '#ef4444', '#06b6d4', '#f97316', '#8b5cf6', '#10b981']

function MetricCard({ title, value, sub, color }: { title: string; value: string; sub?: string; color?: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h5" fontWeight={700} sx={{ color: color ?? 'inherit' }}>
          {value}
        </Typography>
        {sub && (
          <Typography variant="caption" color="text.secondary">
            {sub}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

export default function DashboardCharts({ summary }: { summary: DashboardSummary }) {
  const theme = useTheme()
  const trend = summary.monthly_trend.map((t) => ({ name: t.month, Spending: t.total }))
  const cats = summary.category_totals.map((c) => ({ name: c.category, value: c.total }))

  const delta = summary.current_month_total - summary.previous_month_total

  return (
    <Box>
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Spent this month"
            value={formatMoney(summary.current_month_total)}
            sub={`${summary.expense_count} transactions`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="All-time expenses"
            value={formatMoney(summary.total_expenses)}
            sub={`${summary.current_month} month trending`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Vs last month"
            value={`${delta >= 0 ? '+' : ''}${formatMoney(delta)}`}
            sub={`last month: ${formatMoney(summary.previous_month_total)}`}
            color={delta > 0 ? theme.palette.error.main : theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Pending payments" value={formatMoney(summary.total_pending)} sub="servants / milk / newspaper" color={theme.palette.warning.main} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Spending Trend
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(v: number) => formatMoney(v)} />
                  <Bar dataKey="Spending" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Spending by Category (this month)
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={cats} dataKey="value" nameKey="name" outerRadius={90} label>
                    {cats.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => formatMoney(v)} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Pending Payments
          </Typography>
          {summary.pending_payments.length === 0 ? (
            <Typography color="text.secondary">All payments cleared. Nice!</Typography>
          ) : (
            summary.pending_payments.map((p) => (
              <Box key={`${p.type}-${p.name}`} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: `1px solid ${theme.palette.divider}` }}>
                <span>
                  [{p.type}] {p.name} {p.month && `(${p.month})`}
                </span>
                <strong>{formatMoney(p.amount)}</strong>
              </Box>
            ))
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
