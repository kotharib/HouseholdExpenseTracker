import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { api, getErrorMessage } from '../api/client'
import DataState from '../components/DataState'
import SubscriptionForm from '../components/SubscriptionForm'
import type { DeliverySubscription, DeliverySubscriptionInput } from '../types'
import { formatMoney } from '../utils/format'
import { usePermissions } from '../utils/roles'

export default function SubscriptionsPage() {
  const { canWrite } = usePermissions()
  const [items, setItems] = useState<DeliverySubscription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<DeliverySubscription | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<DeliverySubscription[]>('/subscriptions')
      setItems(res.data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async (data: DeliverySubscriptionInput, id?: number) => {
    setSubmitting(true)
    try {
      if (id) {
        await api.put(`/subscriptions/${id}`, data)
        setToast('Subscription updated. Daily deliveries regenerated for affected months.')
      } else {
        await api.post('/subscriptions', data)
        setToast('Daily deliveries generated automatically.')
      }
      setOpen(false)
      load()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Delivery Subscriptions
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Create milk, newspaper, or custom subscriptions. Daily rows are generated automatically; mark delivered or missed on the Milk and Newspaper pages.
      </Typography>
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        {canWrite && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditing(null)
              setOpen(true)
            }}
          >
            Add Subscription
          </Button>
        )}
      </Stack>
      <DataState loading={loading} error={error} onRetry={load} />
      {!loading && !error && (
        <Card>
          <CardContent>
            {items.length === 0 ? (
              <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                No subscriptions yet. Add one to auto-generate daily delivery rows.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Frequency</TableCell>
                      <TableCell>Start</TableCell>
                      <TableCell>End</TableCell>
                      <TableCell>Rate / Cost</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Rows</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item) => (
                      <TableRow key={item.id} hover>
                        <TableCell>{item.name}</TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>{item.delivery_type}</TableCell>
                        <TableCell sx={{ textTransform: 'capitalize' }}>{item.delivery_frequency}</TableCell>
                        <TableCell>{item.start_date}</TableCell>
                        <TableCell>{item.end_date || 'Ongoing'}</TableCell>
                        <TableCell>
                          {item.delivery_type === 'milk'
                            ? `${item.default_quantity}L @ ${formatMoney(item.rate_per_unit || 0)}`
                            : item.delivery_type === 'newspaper'
                              ? formatMoney(item.monthly_cost || 0)
                              : '-'}
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            color={item.active ? 'success' : 'default'}
                            label={item.active ? 'Active' : 'Paused'}
                          />
                        </TableCell>
                        <TableCell align="right">{item.generated_count ?? 0}</TableCell>
                        <TableCell align="right">
                          {canWrite && (
                            <IconButton
                              size="small"
                              onClick={() => {
                                setEditing(item)
                                setOpen(true)
                              }}
                              aria-label="edit"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}
      <SubscriptionForm
        open={open}
        initial={editing}
        onClose={() => setOpen(false)}
        onSubmit={submit}
        submitting={submitting}
      />
      <Snackbar open={Boolean(toast)} autoHideDuration={4000} onClose={() => setToast('')}>
        <Alert severity="success" onClose={() => setToast('')} variant="filled">
          {toast}
        </Alert>
      </Snackbar>
    </div>
  )
}
