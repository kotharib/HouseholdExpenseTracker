import { Alert, Box, Card, CardContent, Chip, Grid, Stack, Typography, useTheme } from '@mui/material'
import {
  Article as ArticleIcon,
  Groups as GroupsIcon,
  LocalShipping as LocalShippingIcon,
  Receipt as ReceiptIcon,
  Savings as SavingsIcon,
  WaterDrop as WaterDropIcon,
} from '@mui/icons-material'
import type { MonthlyExpenseReport } from '../types'
import { formatMoney } from '../utils/format'

function Metric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary" fontWeight={600}>
          {label}
        </Typography>
        <Typography variant="h6" fontWeight={800} sx={{ color }}>
          {formatMoney(value)}
        </Typography>
      </CardContent>
    </Card>
  )
}

export default function MonthlyReportCard({ report }: { report: MonthlyExpenseReport }) {
  const theme = useTheme()
  const savingsColor = report.savings.saved ? theme.palette.success.main : theme.palette.error.main

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Monthly Expense Overview
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Total monthly expenses" value={report.total_expenses} color="#d97706" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Monthly milk bill" value={report.milk_bill} color="#0d9488" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Monthly newspaper bill" value={report.newspaper_bill} color="#7c3aed" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Monthly servant salary total" value={report.servant_salary_total} color="#0891b2" />
        </Grid>
        <Grid item xs={12} sm={6} md={8}>
          <Metric label="Monthly grand total" value={report.grand_total} color="#4f46e5" />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Category-wise monthly expenses
              </Typography>
              <Stack spacing={1}>
                {report.category_totals.map((c) => {
                  const pct = report.total_expenses > 0 ? (c.total / report.total_expenses) * 100 : 0
                  return (
                    <Box key={c.category}>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography variant="caption">{c.category}</Typography>
                        <Typography variant="caption" fontWeight={700}>
                          {formatMoney(c.total)}
                        </Typography>
                      </Stack>
                      <Box sx={{ height: 8, borderRadius: 4, backgroundColor: theme.palette.divider, overflow: 'hidden' }}>
                        <Box sx={{ height: '100%', width: `${Math.min(pct, 100)}%`, backgroundColor: '#4f46e5' }} />
                      </Box>
                    </Box>
                  )
                })}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={5}>
          <Stack spacing={2}>
            <Card>
              <CardContent>
                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                  <LocalShippingIcon color="primary" fontSize="small" />
                  <Typography variant="subtitle1" fontWeight={700}>
                    Monthly delivery summary
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  <Chip icon={<WaterDropIcon />} label={`Milk ${report.delivery_summary.milk_delivered_days}/${report.delivery_summary.milk_total_days}`} />
                  <Chip icon={<ArticleIcon />} label={`Newspaper ${report.delivery_summary.newspaper_delivered_days}`} />
                  <Chip icon={<GroupsIcon />} label={`Missed ${report.delivery_summary.total_missed_deliveries}`} color={report.delivery_summary.total_missed_deliveries > 0 ? 'warning' : 'default'} />
                </Stack>
              </CardContent>
            </Card>
            <Alert severity={report.savings.saved ? 'success' : 'info'} icon={report.savings.saved ? <SavingsIcon /> : <ReceiptIcon />}>
              <Typography fontWeight={700} sx={{ color: savingsColor }}>
                {report.savings.message}
              </Typography>
            </Alert>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  )
}
