import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material'
import { useEffect, useState } from 'react'
import type { Milk, MilkInput } from '../types'
import { formatMoneyFixed } from '../utils/format'

interface Props {
  open: boolean
  initial?: Milk | null
  onClose: () => void
  onSubmit: (data: MilkInput, id?: number) => void
  submitting?: boolean
}

const today = () => new Date().toISOString().slice(0, 10)
const currentMonth = () => today().slice(0, 7)

export default function MilkForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [supplier, setSupplier] = useState('')
  const [quantity, setQuantity] = useState('')
  const [rate, setRate] = useState('')
  const [date, setDate] = useState(today())
  const [month, setMonth] = useState(currentMonth())
  const [delivered, setDelivered] = useState(true)
  const [status, setStatus] = useState<'pending' | 'paid'>('pending')

  useEffect(() => {
    if (open) {
      setSupplier(initial?.supplier ?? '')
      setQuantity(initial ? String(initial.quantity) : '')
      setRate(initial ? String(initial.rate) : '')
      setDate(initial?.date ?? today())
      setMonth(initial?.month ?? currentMonth())
      setDelivered(initial?.is_delivered ?? true)
      setStatus(initial?.payment_status ?? 'pending')
    }
  }, [open, initial])

  const submit = () => {
    if (!supplier || !quantity || !rate || !date || !month) return
    onSubmit(
      {
        supplier,
        quantity: Number(quantity),
        rate: Number(rate),
        date,
        month,
        is_delivered: delivered,
        payment_status: status,
      },
      initial?.id,
    )
  }

  const total = Number(quantity || 0) * Number(rate || 0)

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Milk Delivery' : 'Add Milk Delivery'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Supplier" value={supplier} onChange={(e) => setSupplier(e.target.value)} required />
          <TextField
            label="Quantity (litres)"
            type="number"
            inputProps={{ step: '0.5', min: 0 }}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
          />
          <TextField
            label="Rate (per litre)"
            type="number"
            inputProps={{ step: '0.01', min: 0 }}
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            required
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <TextField label="Month (YYYY-MM)" value={month} onChange={(e) => setMonth(e.target.value)} required inputProps={{ maxLength: 7 }} />
          </Box>
          <FormControl>
            <InputLabel>Payment Status</InputLabel>
            <Select value={status} onChange={(e) => setStatus(e.target.value as 'pending' | 'paid')} label="Payment Status">
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="paid">Paid</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={<Checkbox checked={delivered} onChange={(e) => setDelivered(e.target.checked)} />}
            label="Delivered"
          />
          <Box>
            Total: <strong>{formatMoneyFixed(total)}</strong>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={submit} disabled={submitting}>
          {submitting ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
