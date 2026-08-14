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
import type { Newspaper, NewspaperInput } from '../types'

interface Props {
  open: boolean
  initial?: Newspaper | null
  onClose: () => void
  onSubmit: (data: NewspaperInput, id?: number) => void
  submitting?: boolean
}

const today = () => new Date().toISOString().slice(0, 10)
const currentMonth = () => today().slice(0, 7)

export default function NewspaperForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [name, setName] = useState('')
  const [cost, setCost] = useState('')
  const [month, setMonth] = useState(currentMonth())
  const [date, setDate] = useState('')
  const [delivered, setDelivered] = useState(true)
  const [status, setStatus] = useState<'pending' | 'paid'>('pending')

  useEffect(() => {
    if (open) {
      setName(initial?.name ?? '')
      setCost(initial ? String(initial.monthly_cost) : '')
      setMonth(initial?.month ?? currentMonth())
      setDate(initial?.date ?? '')
      setDelivered(initial?.delivery_status ?? true)
      setStatus(initial?.payment_status ?? 'pending')
    }
  }, [open, initial])

  const submit = () => {
    if (!name || !cost || !month) return
    onSubmit(
      {
        name,
        monthly_cost: Number(cost),
        month,
        date: date || undefined,
        delivery_status: delivered,
        payment_status: status,
      },
      initial?.id,
    )
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Newspaper Delivery' : 'Add Newspaper Subscription'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <TextField
            label="Monthly Cost"
            type="number"
            inputProps={{ step: '0.01', min: 0 }}
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            required
          />
          <TextField label="Month (YYYY-MM)" value={month} onChange={(e) => setMonth(e.target.value)} required inputProps={{ maxLength: 7 }} />
          <TextField
            label="Date (optional - blank adds the whole month)"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
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
