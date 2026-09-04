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
import type { DeliveryFrequency, DeliverySubscription, DeliverySubscriptionInput, DeliveryType } from '../types'

interface Props {
  open: boolean
  initial?: DeliverySubscription | null
  onClose: () => void
  onSubmit: (data: DeliverySubscriptionInput, id?: number) => void
  submitting?: boolean
}

const WEEKDAYS = [
  { value: 'mon', label: 'Mon' },
  { value: 'tue', label: 'Tue' },
  { value: 'wed', label: 'Wed' },
  { value: 'thu', label: 'Thu' },
  { value: 'fri', label: 'Fri' },
  { value: 'sat', label: 'Sat' },
  { value: 'sun', label: 'Sun' },
]

const today = () => new Date().toISOString().slice(0, 10)

export default function SubscriptionForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [deliveryType, setDeliveryType] = useState<DeliveryType>('milk')
  const [name, setName] = useState('')
  const [startDate, setStartDate] = useState(today())
  const [endDate, setEndDate] = useState('')
  const [frequency, setFrequency] = useState<DeliveryFrequency>('daily')
  const [pattern, setPattern] = useState<string[]>(['mon', 'wed', 'fri'])
  const [rate, setRate] = useState('28')
  const [quantity, setQuantity] = useState('1.5')
  const [monthlyCost, setMonthlyCost] = useState('250')
  const [autoGenerate, setAutoGenerate] = useState(true)
  const [active, setActive] = useState(true)

  useEffect(() => {
    if (!open) return
    setDeliveryType(initial?.delivery_type ?? 'milk')
    setName(initial?.name ?? '')
    setStartDate(initial?.start_date ?? today())
    setEndDate(initial?.end_date ?? '')
    setFrequency(initial?.delivery_frequency ?? 'daily')
    setPattern(initial?.custom_pattern ?? ['mon', 'wed', 'fri'])
    setRate(initial?.rate_per_unit != null ? String(initial.rate_per_unit) : '28')
    setQuantity(initial?.default_quantity != null ? String(initial.default_quantity) : '1.5')
    setMonthlyCost(initial?.monthly_cost != null ? String(initial.monthly_cost) : '250')
    setAutoGenerate(initial?.auto_generate ?? true)
    setActive(initial?.active ?? true)
  }, [open, initial])

  const toggleDay = (day: string) => {
    setPattern((prev) => (prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]))
  }

  const submit = () => {
    if (!name || !startDate) return
    const payload: DeliverySubscriptionInput = {
      delivery_type: deliveryType,
      name,
      start_date: startDate,
      end_date: endDate || null,
      active,
      delivery_frequency: frequency,
      custom_pattern: frequency === 'custom' ? pattern : null,
      auto_generate: autoGenerate,
      rate_per_unit: deliveryType === 'milk' ? Number(rate) : null,
      default_quantity: deliveryType === 'milk' ? Number(quantity) : null,
      monthly_cost: deliveryType === 'newspaper' ? Number(monthlyCost) : null,
    }
    onSubmit(payload, initial?.id)
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Subscription' : 'New Delivery Subscription'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <FormControl>
            <InputLabel>Delivery type</InputLabel>
            <Select
              value={deliveryType}
              label="Delivery type"
              onChange={(e) => setDeliveryType(e.target.value as DeliveryType)}
            >
              <MenuItem value="milk">Milk</MenuItem>
              <MenuItem value="newspaper">Newspaper</MenuItem>
              <MenuItem value="custom">Custom</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label={deliveryType === 'newspaper' ? 'Newspaper name' : 'Supplier / name'}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Start date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="End date (optional)"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
          <FormControl>
            <InputLabel>Frequency</InputLabel>
            <Select
              value={frequency}
              label="Frequency"
              onChange={(e) => setFrequency(e.target.value as DeliveryFrequency)}
            >
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="alternate">Alternate days</MenuItem>
              <MenuItem value="custom">Custom pattern</MenuItem>
            </Select>
          </FormControl>
          {frequency === 'custom' && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {WEEKDAYS.map((day) => (
                <FormControlLabel
                  key={day.value}
                  control={<Checkbox checked={pattern.includes(day.value)} onChange={() => toggleDay(day.value)} />}
                  label={day.label}
                />
              ))}
            </Box>
          )}
          {deliveryType === 'milk' && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Default quantity (L)"
                type="number"
                inputProps={{ step: '0.5', min: 0 }}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
              <TextField
                label="Rate per unit"
                type="number"
                inputProps={{ step: '0.01', min: 0 }}
                value={rate}
                onChange={(e) => setRate(e.target.value)}
                required
              />
            </Box>
          )}
          {deliveryType === 'newspaper' && (
            <TextField
              label="Monthly cost"
              type="number"
              inputProps={{ step: '0.01', min: 0 }}
              value={monthlyCost}
              onChange={(e) => setMonthlyCost(e.target.value)}
              required
            />
          )}
          <FormControlLabel
            control={<Checkbox checked={autoGenerate} onChange={(e) => setAutoGenerate(e.target.checked)} />}
            label="Auto-generate daily delivery rows"
          />
          <FormControlLabel
            control={<Checkbox checked={active} onChange={(e) => setActive(e.target.checked)} />}
            label="Active"
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
