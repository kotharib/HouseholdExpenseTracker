import {
  Button,
  Checkbox,
  Chip,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { Delete as DeleteIcon, DeleteSweep as DeleteSweepIcon, Edit as EditIcon } from '@mui/icons-material'
import { useState } from 'react'
import type { Servant } from '../types'
import { formatMoney } from '../utils/format'

interface Props {
  servants: Servant[]
  onEdit: (servant: Servant) => void
  onDelete: (servant: Servant) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function ServantList({ servants, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const allSelected = servants.length > 0 && selected.length === servants.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : servants.map((s) => s.id))

  if (servants.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No servants registered yet.
      </Typography>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${servants.length} records`}
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            size="small"
            color="error"
            variant="outlined"
            startIcon={<DeleteSweepIcon />}
            disabled={selected.length === 0}
            onClick={() => {
              onBulkDelete(selected)
              setSelected([])
            }}
          >
            Delete selected ({selected.length})
          </Button>
          <Button
            size="small"
            color="error"
            variant="outlined"
            disabled={servants.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${servants.length} servants? This cannot be undone.`)) {
                onDeleteAll()
                setSelected([])
              }
            }}
          >
            Delete all
          </Button>
        </Stack>
      </Stack>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox size="small" checked={allSelected} onChange={toggleAll} inputProps={{ 'aria-label': 'select all' }} />
              </TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Role</TableCell>
              <TableCell align="right">Monthly Salary</TableCell>
              <TableCell align="right">Attendance</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {servants.map((s) => (
              <TableRow key={s.id} hover selected={selected.includes(s.id)}>
                <TableCell padding="checkbox">
                  <Checkbox size="small" checked={selected.includes(s.id)} onChange={() => toggle(s.id)} inputProps={{ 'aria-label': 'select' }} />
                </TableCell>
                <TableCell>{s.name}</TableCell>
                <TableCell>{s.role}</TableCell>
                <TableCell align="right">{formatMoney(s.monthly_salary)}</TableCell>
                <TableCell align="right">{s.attendance_count}</TableCell>
                <TableCell>
                  <Chip label={s.payment_status} size="small" color={s.payment_status === 'paid' ? 'success' : 'warning'} />
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => onEdit(s)} aria-label="edit">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => onDelete(s)} aria-label="delete">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
