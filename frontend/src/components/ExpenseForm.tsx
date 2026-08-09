import {
  Autocomplete,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { expenseCategories } from '../types'
import type { Expense, ExpenseInput } from '../types'

interface Props {
  open: boolean
  initial?: Expense | null
  onClose: () => void
  onSubmit: (data: ExpenseInput, id?: number) => void
  submitting?: boolean
}

const today = () => new Date().toISOString().slice(0, 10)

export default function ExpenseForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [category, setCategory] = useState('groceries')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(today())
  const [paymentMode, setPaymentMode] = useState('cash')
  const [notes, setNotes] = useState('')
  const [tags, setTags] = useState('')

  useEffect(() => {
    if (open) {
      setCategory(initial?.category ?? 'groceries')
      setAmount(initial ? String(initial.amount) : '')
      setDate(initial?.date ?? today())
      setPaymentMode(initial?.payment_mode ?? 'cash')
      setNotes(initial?.notes ?? '')
      setTags(initial?.tags ?? '')
    }
  }, [open, initial])

  const submit = () => {
    if (!category || !amount || !date) return
    onSubmit(
      {
        category,
        amount: Number(amount),
        date,
        payment_mode: paymentMode,
        notes,
        tags,
      },
      initial?.id,
    )
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Expense' : 'Add Expense'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <Autocomplete
            freeSolo
            options={expenseCategories}
            inputValue={category}
            onInputChange={(_, v) => setCategory(v)}
            renderInput={(params) => <TextField {...params} label="Category" required />}
          />
          <TextField
            label="Amount"
            type="number"
            inputProps={{ step: '0.01', min: 0 }}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <TextField label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required InputLabelProps={{ shrink: true }} />
          <FormControl>
            <InputLabel>Payment Mode</InputLabel>
            <Select value={paymentMode} onChange={(e) => setPaymentMode(e.target.value)} label="Payment Mode">
              <MenuItem value="cash">Cash</MenuItem>
              <MenuItem value="card">Card</MenuItem>
              <MenuItem value="upi">UPI</MenuItem>
              <MenuItem value="bank">Bank Transfer</MenuItem>
            </Select>
          </FormControl>
          <TextField label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} multiline rows={2} />
          <TextField label="Tags (comma separated)" value={tags} onChange={(e) => setTags(e.target.value)} />
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
