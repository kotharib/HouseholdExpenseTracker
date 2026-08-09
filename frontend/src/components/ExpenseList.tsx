import {
  Box,
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
import { useMemo, useState } from 'react'
import type { Expense } from '../types'
import { formatMoney } from '../utils/format'

interface Props {
  expenses: Expense[]
  onEdit: (expense: Expense) => void
  onDelete: (expense: Expense) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function ExpenseList({ expenses, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const allSelected = expenses.length > 0 && selected.length === expenses.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  const toggleAll = () => setSelected(allSelected ? [] : expenses.map((e) => e.id))

  const total = useMemo(() => expenses.reduce((sum, e) => sum + e.amount, 0), [expenses])

  if (expenses.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No expenses recorded for this month.
      </Typography>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${expenses.length} records`}
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
            disabled={expenses.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${expenses.length} expenses? This cannot be undone.`)) {
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
              <TableCell>Date</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell>Payment</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {expenses.map((e) => (
              <TableRow key={e.id} hover selected={selected.includes(e.id)}>
                <TableCell padding="checkbox">
                  <Checkbox size="small" checked={selected.includes(e.id)} onChange={() => toggle(e.id)} inputProps={{ 'aria-label': 'select' }} />
                </TableCell>
                <TableCell>{e.date}</TableCell>
                <TableCell>
                  <Chip label={e.category} size="small" />
                </TableCell>
                <TableCell>{e.notes || '—'}</TableCell>
                <TableCell>{e.payment_mode}</TableCell>
                <TableCell align="right">{formatMoney(e.amount)}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => onEdit(e)} aria-label="edit">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => onDelete(e)} aria-label="delete">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={5} />
              <TableCell align="right">
                <Box fontWeight={700}>{formatMoney(total)}</Box>
              </TableCell>
              <TableCell />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
