import { Card, CardContent, Grid, Typography, useTheme } from '@mui/material'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { YearlyGraphData } from '../types'
import { formatMoney } from '../utils/format'
import CategoryBreakdownGraph from './CategoryBreakdownGraph'
import TrendGraph from './TrendGraph'

function toRows(data: YearlyGraphData) {
  return data.months.map((name, i) => ({
    name,
    Expenses: data.monthly_expenses[i],
    Milk: data.milk_cost[i],
    Newspaper: data.newspaper_cost[i],
    Servants: data.servant_salary[i],
    'Grand total': data.grand_total[i],
  }))
}

export default function GraphVisuals({ data }: { data: YearlyGraphData }) {
  const theme = useTheme()
  const rows = toRows(data)

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <TrendGraph
          title="Monthly Expense Trend"
          months={data.months}
          series={[{ key: 'monthly_expenses', label: 'Expenses', color: '#4f46e5' }]}
          values={{ monthly_expenses: data.monthly_expenses }}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <CategoryBreakdownGraph title="Category-wise Yearly Breakdown" categories={data.category_totals} />
      </Grid>
      <Grid item xs={12} md={6}>
        <TrendGraph
          title="Milk Delivery Cost Trend"
          months={data.months}
          series={[{ key: 'milk_cost', label: 'Milk', color: '#0d9488' }]}
          values={{ milk_cost: data.milk_cost }}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <TrendGraph
          title="Newspaper Delivery Cost Trend"
          months={data.months}
          series={[{ key: 'newspaper_cost', label: 'Newspaper', color: '#7c3aed' }]}
          values={{ newspaper_cost: data.newspaper_cost }}
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Servant Salary Trend
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v: number) => formatMoney(v)} />
                <Bar dataKey="Servants" fill="#0891b2" radius={[8, 8, 0, 0]} maxBarSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Grand Total Trend
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v: number) => formatMoney(v)} />
                <Legend />
                <Line type="monotone" dataKey="Expenses" stroke="#d97706" strokeWidth={2} />
                <Line type="monotone" dataKey="Milk" stroke="#0d9488" strokeWidth={2} />
                <Line type="monotone" dataKey="Newspaper" stroke="#7c3aed" strokeWidth={2} />
                <Line type="monotone" dataKey="Servants" stroke="#0891b2" strokeWidth={2} />
                <Line type="monotone" dataKey="Grand total" stroke="#4f46e5" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}
