import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Investment, InvestmentInput, InvestmentOption } from '../types'
import { formatMoneyFixed } from '../utils/format'

interface Props {
  open: boolean
  initial?: Investment | null
  onClose: () => void
  onSubmit: (data: InvestmentInput, id?: number) => void
  submitting?: boolean
}

const today = () => new Date().toISOString().slice(0, 10)
const currentMonth = () => today().slice(0, 7)

const RISK_LABELS: Record<string, string> = {
  low: 'Low risk',
  medium: 'Medium risk',
  high: 'High risk',
}

export default function InvestmentForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [schemeName, setSchemeName] = useState('')
  const [category, setCategory] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(today())
  const [month, setMonth] = useState(currentMonth())
  const [expectedReturn, setExpectedReturn] = useState('')
  const [notes, setNotes] = useState('')
  const [options, setOptions] = useState<InvestmentOption[]>([])

  useEffect(() => {
    if (open) {
      setSchemeName(initial?.scheme_name ?? '')
      setCategory(initial?.category ?? '')
      setAmount(initial ? String(initial.amount) : '')
      setDate(initial?.date ?? today())
      setMonth(initial?.month ?? currentMonth())
      setExpectedReturn(initial?.expected_return != null ? String(initial.expected_return) : '')
      setNotes(initial?.notes ?? '')
    }
  }, [open, initial])

  useEffect(() => {
    if (!open) return
    api
      .get<InvestmentOption[]>('/investments/options')
      .then((res) => setOptions(res.data))
      .catch(() => setOptions([]))
  }, [open])

  const submit = () => {
    if (!schemeName || !category || !amount || !date || !month) return
    onSubmit(
      {
        scheme_name: schemeName,
        category,
        amount: Number(amount),
        date,
        month,
        expected_return: expectedReturn ? Number(expectedReturn) : undefined,
        notes: notes || undefined,
      },
      initial?.id,
    )
  }

  const selected = options.find((o) => o.key === category)

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Investment' : 'Add Investment'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Scheme Name"
            value={schemeName}
            onChange={(e) => setSchemeName(e.target.value)}
            placeholder="e.g. HDFC Flexi Cap Fund, PPF Account"
            required
          />
          <FormControl>
            <InputLabel>Category</InputLabel>
            <Select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              label="Category"
              required
            >
              {options.map((opt) => (
                <MenuItem key={opt.key} value={opt.key}>
                  {opt.name} ({RISK_LABELS[opt.risk] ?? opt.risk})
                </MenuItem>
              ))}
            </Select>
            {selected && (
              <FormHelperText>
                ~{selected.expected_return}% expected return · {selected.lock_in}
              </FormHelperText>
            )}
          </FormControl>
          <TextField
            label="Amount (₹)"
            type="number"
            inputProps={{ step: '0.01', min: 0 }}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required InputLabelProps={{ shrink: true }} />
            <TextField label="Month (YYYY-MM)" value={month} onChange={(e) => setMonth(e.target.value)} required inputProps={{ maxLength: 7 }} />
          </Box>
          <TextField
            label="Expected Return (% p.a.)"
            type="number"
            inputProps={{ step: '0.1', min: 0, max: 100 }}
            value={expectedReturn}
            onChange={(e) => setExpectedReturn(e.target.value)}
          />
          <TextField
            label="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            multiline
            minRows={2}
            placeholder="SIP, tax-saver, emergency fund, etc."
          />
          <Box>
            Amount: <strong>{formatMoneyFixed(Number(amount || 0))}</strong>
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
