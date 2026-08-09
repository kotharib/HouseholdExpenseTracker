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
import { Delete as DeleteIcon, DeleteSweep as DeleteSweepIcon, Edit as EditIcon, FilterAltOff as FilterAltOffIcon } from '@mui/icons-material'
import { useState } from 'react'
import type { Servant } from '../types'
import { formatMoney } from '../utils/format'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  servants: Servant[]
  onEdit: (servant: Servant) => void
  onDelete: (servant: Servant) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function ServantList({ servants, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Servant>(servants)
  const allSelected = sortedAndFiltered.length > 0 && selected.length === sortedAndFiltered.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : sortedAndFiltered.map((s) => s.id))

  if (servants.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No servants registered yet.
      </Typography>
    )
  }

  if (sortedAndFiltered.length === 0) {
    return (
      <Stack alignItems="center" spacing={1} sx={{ py: 4 }}>
        <Typography color="text.secondary">No servants match the current filters.</Typography>
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
          {hasActiveFilter && ` (of ${servants.length})`}
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
              <SortableHeader active={sortColumn === 'name'} direction={sortDirection} onClick={() => handleSort('name')}>
                Name
              </SortableHeader>
              <SortableHeader active={sortColumn === 'role'} direction={sortDirection} onClick={() => handleSort('role')}>
                Role
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'monthly_salary'} direction={sortDirection} onClick={() => handleSort('monthly_salary')}>
                Monthly Salary
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'attendance_count'} direction={sortDirection} onClick={() => handleSort('attendance_count')}>
                Attendance
              </SortableHeader>
              <SortableHeader active={sortColumn === 'payment_status'} direction={sortDirection} onClick={() => handleSort('payment_status')}>
                Status
              </SortableHeader>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
            <TableRow>
              <TableCell padding="checkbox" />
              <FilterCell value={filters.name ?? ''} onChange={(v) => handleFilter('name', v)} placeholder="Name" />
              <FilterCell value={filters.role ?? ''} onChange={(v) => handleFilter('role', v)} placeholder="Role" />
              <FilterCell align="right" value={filters.monthly_salary ?? ''} onChange={(v) => handleFilter('monthly_salary', v)} placeholder="Salary" />
              <FilterCell align="right" value={filters.attendance_count ?? ''} onChange={(v) => handleFilter('attendance_count', v)} placeholder="Attendance" />
              <FilterCell value={filters.payment_status ?? ''} onChange={(v) => handleFilter('payment_status', v)} placeholder="Status" />
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((s) => (
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
