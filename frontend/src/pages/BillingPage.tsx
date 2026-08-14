import { Alert, Box, Button, Card, CardContent, Chip, Grid, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material'
import {
  Article as ArticleIcon,
  Download as DownloadIcon,
  Groups as GroupsIcon,
  Receipt as ReceiptIcon,
  Savings as SavingsIcon,
  WaterDrop as WaterDropIcon,
} from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import type { MilkDailyResponse, MonthlyBill, NewspaperDailyResponse } from '../types'
import { formatMoney } from '../utils/format'

const today = () => new Date().toISOString().slice(0, 7)

function Metric({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 42,
              height: 42,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              background: `linear-gradient(135deg, ${color}, ${color}99)`,
              boxShadow: `0 6px 14px ${color}44`,
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={800} sx={{ color }}>
              {formatMoney(value)}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default function BillingPage() {
  const [month, setMonth] = useState(today())
  const [bill, setBill] = useState<MonthlyBill | null>(null)
  const [milkDaily, setMilkDaily] = useState<MilkDailyResponse | null>(null)
  const [paperDaily, setPaperDaily] = useState<NewspaperDailyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  const load = async (m: string) => {
    setLoading(true)
    setError('')
    try {
      const year = m.slice(0, 4)
      const monthNum = m.slice(5, 7)
      const [billRes, milkRes, paperRes] = await Promise.all([
        api.get<MonthlyBill>(`/billing/monthly/${year}/${monthNum}`),
        api.get<MilkDailyResponse>(`/milk/deliveries/${year}/${monthNum}`),
        api.get<NewspaperDailyResponse>(`/newspaper/deliveries/${year}/${monthNum}`),
      ])
      setBill(billRes.data)
      setMilkDaily(milkRes.data)
      setPaperDaily(paperRes.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(month)
  }, [month])

  const downloadPdf = async () => {
    setDownloading(true)
    setError('')
    try {
      const year = month.slice(0, 4)
      const monthNum = month.slice(5, 7)
      const res = await api.get<Blob>(`/billing/monthly/${year}/${monthNum}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `monthly-bill-${month}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Monthly Bill
      </Typography>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
            <Typography variant="h6">Bill for the selected month</Typography>
            <Stack direction="row" gap={1.5} alignItems="center" flexWrap="wrap">
              <TextField
                label="Month (YYYY-MM)"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                inputProps={{ maxLength: 7 }}
              />
              <Button variant="contained" onClick={() => load(month)} disabled={loading}>
                {loading ? 'Loading...' : 'Generate'}
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />} onClick={downloadPdf} disabled={loading || downloading}>
                {downloading ? 'Generating...' : 'Download Monthly PDF'}
              </Button>
            </Stack>
          </Stack>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      <DataState loading={loading} error={!bill && error ? error : ''} onRetry={() => load(month)} />
      {!loading && bill && (
        <>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Metric icon={<WaterDropIcon fontSize="small" />} label="Milk bill" value={bill.milk_bill} color="#0d9488" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Metric icon={<ArticleIcon fontSize="small" />} label="Newspaper bill" value={bill.newspaper_bill} color="#7c3aed" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Metric icon={<GroupsIcon fontSize="small" />} label="Servant salaries" value={bill.servant_salary_total} color="#0891b2" />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Metric icon={<ReceiptIcon fontSize="small" />} label="Expenses" value={bill.expenses_total} color="#d97706" />
            </Grid>
            <Grid item xs={12}>
              <Metric icon={<SavingsIcon fontSize="small" />} label="Grand total" value={bill.grand_total} color="#4f46e5" />
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                    <WaterDropIcon color="primary" fontSize="small" />
                    <Typography variant="h6">Daily Milk Deliveries</Typography>
                  </Stack>
                  {milkDaily && milkDaily.days.length === 0 ? (
                    <Typography color="text.secondary">No milk deliveries recorded.</Typography>
                  ) : (
                    <>
                      <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                        {milkDaily?.delivered_days} delivered · {milkDaily?.missed_days} missed
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Date</TableCell>
                              <TableCell>Supplier</TableCell>
                              <TableCell align="right">Qty</TableCell>
                              <TableCell align="right">Rate</TableCell>
                              <TableCell align="right">Amount</TableCell>
                              <TableCell>Status</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {milkDaily?.days.map((d) => (
                              <TableRow key={d.id ?? d.date} hover>
                                <TableCell>{d.date}</TableCell>
                                <TableCell>{d.supplier}</TableCell>
                                <TableCell align="right">{d.quantity}</TableCell>
                                <TableCell align="right">{formatMoney(d.rate)}</TableCell>
                                <TableCell align="right">{formatMoney(d.total)}</TableCell>
                                <TableCell>
                                  <Chip size="small" color={d.delivered ? 'success' : 'error'} label={d.delivered ? 'Delivered' : 'Missed'} />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                    <ArticleIcon color="primary" fontSize="small" />
                    <Typography variant="h6">Daily Newspaper Deliveries</Typography>
                  </Stack>
                  {paperDaily && paperDaily.newspapers.length === 0 ? (
                    <Typography color="text.secondary">No newspaper deliveries recorded.</Typography>
                  ) : (
                    <Stack spacing={2}>
                      {paperDaily?.newspapers.map((g) => (
                        <Box key={g.name}>
                          <Stack direction="row" justifyContent="space-between" mb={0.5}>
                            <Typography variant="subtitle2" fontWeight={700}>
                              {g.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {g.days_delivered}/{g.days_total} days · {formatMoney(g.total)}
                            </Typography>
                          </Stack>
                          <TableContainer>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Date</TableCell>
                                  <TableCell>Delivered</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {g.days.map((d) => (
                                  <TableRow key={d.id ?? d.date} hover>
                                    <TableCell>{d.date}</TableCell>
                                    <TableCell>
                                      <Chip size="small" color={d.delivered ? 'success' : 'error'} label={d.delivered ? 'Yes' : 'No'} />
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </Box>
                      ))}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Servant Salaries
                  </Typography>
                  {bill.servant_details.length === 0 ? (
                    <Typography color="text.secondary">No servants registered.</Typography>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Role</TableCell>
                            <TableCell align="right">Salary</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {bill.servant_details.map((s) => (
                            <TableRow key={s.name} hover>
                              <TableCell>{s.name}</TableCell>
                              <TableCell>{s.role}</TableCell>
                              <TableCell align="right">{formatMoney(s.monthly_salary)}</TableCell>
                            </TableRow>
                          ))}
                          <TableRow>
                            <TableCell colSpan={2} sx={{ fontWeight: 700 }}>
                              Total
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 700 }}>
                              {formatMoney(bill.servant_salary_total)}
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Expenses
                  </Typography>
                  {bill.expense_details.length === 0 ? (
                    <Typography color="text.secondary">No expenses recorded.</Typography>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Category</TableCell>
                            <TableCell align="right">Amount</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {bill.expense_details.map((e) => (
                            <TableRow key={e.id} hover>
                              <TableCell>{e.date}</TableCell>
                              <TableCell>{e.category}</TableCell>
                              <TableCell align="right">{formatMoney(e.amount)}</TableCell>
                            </TableRow>
                          ))}
                          <TableRow>
                            <TableCell colSpan={2} sx={{ fontWeight: 700 }}>
                              Total
                            </TableCell>
                            <TableCell align="right" sx={{ fontWeight: 700 }}>
                              {formatMoney(bill.expenses_total)}
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </div>
  )
}
