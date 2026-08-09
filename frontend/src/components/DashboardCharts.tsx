import { Box, Card, CardContent, Grid, Stack, Typography, useTheme } from '@mui/material'
import { AccountBalanceWallet as WalletIcon, ArrowDownward as ArrowDownIcon, ArrowUpward as ArrowUpIcon, PendingActions as PendingIcon, Savings as SavingsIcon } from '@mui/icons-material'
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
import type { ComponentType } from 'react'
import type { DashboardSummary } from '../types'
import { formatMoney } from '../utils/format'
import { useCountUp } from '../utils/useCountUp'

const COLORS = ['#4f46e5', '#7c3aed', '#f59e0b', '#10b981', '#ef4444', '#06b6d4', '#f97316', '#8b5cf6', '#0d9488', '#e11d48']

interface MetricCardProps {
  title: string
  value: number
  sub?: string
  color?: string
  icon: ComponentType<{ fontSize?: 'small' | 'inherit' | 'medium' | 'large' }>
  delay?: number
}

function MetricCard({ title, value, sub, color, icon: Icon, delay = 0 }: MetricCardProps) {
  const animated = useCountUp(value)
  return (
    <Card
      className="animate-fade-up"
      sx={{
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        animationDelay: `${delay}ms`,
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: `linear-gradient(90deg, ${color ?? '#4f46e5'}, transparent)`,
        },
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              {title}
            </Typography>
            <Typography variant="h5" fontWeight={800} sx={{ color: color ?? 'inherit', mt: 0.5 }}>
              {formatMoney(animated)}
            </Typography>
            {sub && (
              <Typography variant="caption" color="text.secondary">
                {sub}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              background: `linear-gradient(135deg, ${color ?? '#4f46e5'}, ${color ?? '#4f46e5'}99)`,
              boxShadow: `0 6px 14px ${color ?? '#4f46e5'}44`,
            }}
          >
            <Icon fontSize="small" />
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default function DashboardCharts({ summary }: { summary: DashboardSummary }) {
  const theme = useTheme()
  const trend = summary.monthly_trend.map((t) => ({ name: t.month, Spending: t.total }))
  const cats = summary.category_totals.map((c) => ({ name: c.category, value: c.total }))

  const delta = summary.current_month_total - summary.previous_month_total
  const deltaColor = delta > 0 ? theme.palette.error.main : theme.palette.success.main

  return (
    <Box>
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Spent this month"
            value={summary.current_month_total}
            sub={`${summary.expense_count} transactions`}
            color="#4f46e5"
            icon={SavingsIcon}
            delay={0}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="All-time expenses"
            value={summary.total_expenses}
            sub={`${summary.current_month} month trending`}
            color="#0891b2"
            icon={WalletIcon}
            delay={80}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Vs last month"
            value={delta}
            sub={`last month: ${formatMoney(summary.previous_month_total)}`}
            color={deltaColor}
            icon={delta >= 0 ? ArrowUpIcon : ArrowDownIcon}
            delay={160}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Pending payments"
            value={summary.total_pending}
            sub="servants / milk / newspaper"
            color="#d97706"
            icon={PendingIcon}
            delay={240}
          />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Card className="animate-fade-up" sx={{ animationDelay: '120ms' }}>
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
                  <Bar dataKey="Spending" fill="#4f46e5" radius={[8, 8, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={5}>
          <Card className="animate-fade-up" sx={{ animationDelay: '200ms' }}>
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

      <Card className="animate-fade-up" sx={{ mt: 2, animationDelay: '280ms' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Pending Payments
          </Typography>
          {summary.pending_payments.length === 0 ? (
            <Typography color="text.secondary">All payments cleared. Nice!</Typography>
          ) : (
            summary.pending_payments.map((p, i) => (
              <Box
                key={`${p.type}-${p.name}`}
                className="animate-slide-in"
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  py: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  animationDelay: `${280 + i * 60}ms`,
                  transition: 'background-color 0.15s ease',
                  borderRadius: 1,
                  px: 1,
                  '&:hover': { backgroundColor: theme.palette.action.hover },
                }}
              >
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
