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
import { Delete as DeleteIcon, DeleteSweep as DeleteSweepIcon, Edit as EditIcon, FilterAltOff as FilterAltOffIcon } from '@mui/icons-material'
import { useMemo, useState } from 'react'
import type { Expense } from '../types'
import { formatMoney } from '../utils/format'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  expenses: Expense[]
  onEdit: (expense: Expense) => void
  onDelete: (expense: Expense) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function ExpenseList({ expenses, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Expense>(expenses)
  const allSelected = sortedAndFiltered.length > 0 && selected.length === sortedAndFiltered.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  const toggleAll = () => setSelected(allSelected ? [] : sortedAndFiltered.map((e) => e.id))

  const total = useMemo(() => sortedAndFiltered.reduce((sum, e) => sum + e.amount, 0), [sortedAndFiltered])

  if (expenses.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No expenses recorded for this month.
      </Typography>
    )
  }

  if (sortedAndFiltered.length === 0) {
    return (
      <Stack alignItems="center" spacing={1} sx={{ py: 4 }}>
        <Typography color="text.secondary">No expenses match the current filters.</Typography>
        <Button size="small" startIcon={<FilterAltOffIcon />} onClick={clearFilters}>
          Clear filters
        </Button>
      </Stack>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${sortedAndFiltered.length} records`}
          {hasActiveFilter && ` (of ${expenses.length})`}
        </Typography>
        <Stack direction="row" spacing={1}>
          {hasActiveFilter && (
            <Button size="small" startIcon={<FilterAltOffIcon />} onClick={clearFilters}>
              Clear
            </Button>
          )}
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
              <SortableHeader active={sortColumn === 'date'} direction={sortDirection} onClick={() => handleSort('date')}>
                Date
              </SortableHeader>
              <SortableHeader active={sortColumn === 'category'} direction={sortDirection} onClick={() => handleSort('category')}>
                Category
              </SortableHeader>
              <SortableHeader active={sortColumn === 'notes'} direction={sortDirection} onClick={() => handleSort('notes')}>
                Notes
              </SortableHeader>
              <SortableHeader active={sortColumn === 'payment_mode'} direction={sortDirection} onClick={() => handleSort('payment_mode')}>
                Payment
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'amount'} direction={sortDirection} onClick={() => handleSort('amount')}>
                Amount
              </SortableHeader>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
            <TableRow>
              <TableCell padding="checkbox" />
              <FilterCell value={filters.date ?? ''} onChange={(v) => handleFilter('date', v)} placeholder="Date" />
              <FilterCell value={filters.category ?? ''} onChange={(v) => handleFilter('category', v)} placeholder="Category" />
              <FilterCell value={filters.notes ?? ''} onChange={(v) => handleFilter('notes', v)} placeholder="Notes" />
              <FilterCell value={filters.payment_mode ?? ''} onChange={(v) => handleFilter('payment_mode', v)} placeholder="Payment" />
              <FilterCell align="right" value={filters.amount ?? ''} onChange={(v) => handleFilter('amount', v)} placeholder="Amount" />
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((e) => (
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
