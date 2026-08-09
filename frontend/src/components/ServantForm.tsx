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
import type { Servant, ServantInput } from '../types'

interface Props {
  open: boolean
  initial?: Servant | null
  onClose: () => void
  onSubmit: (data: ServantInput, id?: number) => void
  submitting?: boolean
}

const roles = ['home cleaning', 'utensil cleaning', 'car cleaning', 'cook', 'gardener', 'driver', 'other']

export default function ServantForm({ open, initial, onClose, onSubmit, submitting }: Props) {
  const [name, setName] = useState('')
  const [role, setRole] = useState('home cleaning')
  const [salary, setSalary] = useState('')
  const [status, setStatus] = useState<'pending' | 'paid'>('pending')
  const [attendance, setAttendance] = useState('0')

  useEffect(() => {
    if (open) {
      setName(initial?.name ?? '')
      setRole(initial?.role ?? 'home cleaning')
      setSalary(initial ? String(initial.monthly_salary) : '')
      setStatus(initial?.payment_status ?? 'pending')
      setAttendance(initial ? String(initial.attendance_count) : '0')
    }
  }, [open, initial])

  const submit = () => {
    if (!name || !salary) return
    onSubmit(
      {
        name,
        role,
        monthly_salary: Number(salary),
        payment_status: status,
        attendance_count: Number(attendance || 0),
      },
      initial?.id,
    )
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{initial ? 'Edit Servant' : 'Add Servant'}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Autocomplete
            freeSolo
            options={roles}
            inputValue={role}
            onInputChange={(_, v) => setRole(v)}
            renderInput={(params) => <TextField {...params} label="Role" />}
          />
          <TextField
            label="Monthly Salary"
            type="number"
            inputProps={{ step: '0.01', min: 0 }}
            value={salary}
            onChange={(e) => setSalary(e.target.value)}
            required
          />
          <TextField
            label="Attendance (days)"
            type="number"
            inputProps={{ min: 0 }}
            value={attendance}
            onChange={(e) => setAttendance(e.target.value)}
          />
          <FormControl>
            <InputLabel>Payment Status</InputLabel>
            <Select value={status} onChange={(e) => setStatus(e.target.value as 'pending' | 'paid')} label="Payment Status">
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="paid">Paid</MenuItem>
            </Select>
          </FormControl>
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
