import { Card, CardContent, Typography, useTheme } from '@mui/material'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { CategoryTotal } from '../types'
import { formatMoney } from '../utils/format'

const COLORS = ['#4f46e5', '#7c3aed', '#f59e0b', '#10b981', '#ef4444', '#06b6d4', '#f97316', '#8b5cf6', '#0d9488', '#e11d48']

export default function CategoryBreakdownGraph({
  title,
  categories,
}: {
  title: string
  categories: CategoryTotal[]
}) {
  const theme = useTheme()
  const data = categories.filter((c) => c.total > 0).map((c) => ({ name: c.category, total: c.total }))

  return (
    <Card className="animate-fade-up" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={110} />
            <Tooltip formatter={(v: number) => formatMoney(v)} />
            <Bar dataKey="total" radius={[0, 8, 8, 0]} maxBarSize={22}>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
