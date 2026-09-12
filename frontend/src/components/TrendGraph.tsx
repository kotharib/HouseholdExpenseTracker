import { Card, CardContent, Typography, useTheme } from '@mui/material'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatMoney } from '../utils/format'

export interface TrendSeries {
  key: string
  label: string
  color: string
}

export default function TrendGraph({
  title,
  months,
  series,
  values,
}: {
  title: string
  months: string[]
  series: TrendSeries[]
  values: Record<string, number[]>
}) {
  const theme = useTheme()
  const data = months.map((name, i) => {
    const row: Record<string, string | number> = { name }
    for (const item of series) {
      row[item.label] = values[item.key]?.[i] ?? 0
    }
    return row
  })

  return (
    <Card className="animate-fade-up" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip formatter={(v: number) => formatMoney(v)} />
            <Legend />
            {series.map((item) => (
              <Line key={item.key} type="monotone" dataKey={item.label} stroke={item.color} strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
