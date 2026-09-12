import { Box, Card, CardContent, Grid, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material'
import type { YearlyExpenseReport } from '../types'
import { formatMoney } from '../utils/format'
import CategoryBreakdownGraph from './CategoryBreakdownGraph'

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

export default function YearlyReportCard({ report }: { report: YearlyExpenseReport }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Yearly Expense Report
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Total yearly expenses" value={report.total_expenses} color="#d97706" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Yearly milk bill" value={report.milk_bill} color="#0d9488" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Yearly newspaper bill" value={report.newspaper_bill} color="#7c3aed" />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Metric label="Yearly servant salary total" value={report.servant_salary_total} color="#0891b2" />
        </Grid>
        <Grid item xs={12} sm={6} md={8}>
          <Metric label="Yearly grand total" value={report.grand_total} color="#4f46e5" />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={5}>
          <CategoryBreakdownGraph title="Category-wise yearly expenses" categories={report.category_totals} />
        </Grid>
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                Month-by-month breakdown
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Month</TableCell>
                      <TableCell align="right">Expenses</TableCell>
                      <TableCell align="right">Milk</TableCell>
                      <TableCell align="right">Newspaper</TableCell>
                      <TableCell align="right">Servants</TableCell>
                      <TableCell align="right">Grand total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {report.months.map((row) => (
                      <TableRow key={row.month} hover>
                        <TableCell>{row.month_abbrev}</TableCell>
                        <TableCell align="right">{formatMoney(row.expenses_total)}</TableCell>
                        <TableCell align="right">{formatMoney(row.milk_bill)}</TableCell>
                        <TableCell align="right">{formatMoney(row.newspaper_bill)}</TableCell>
                        <TableCell align="right">{formatMoney(row.servant_salary_total)}</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight={700}>{formatMoney(row.grand_total)}</Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
