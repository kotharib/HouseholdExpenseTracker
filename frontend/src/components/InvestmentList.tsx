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
import { useMemo, useState } from 'react'
import type { Investment } from '../types'
import { formatMoney } from '../utils/format'
import { investmentCategoryLabel } from '../utils/investmentCategories'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  investments: Investment[]
  onEdit: (investment: Investment) => void
  onDelete: (investment: Investment) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function InvestmentList({ investments, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Investment>(investments)
  const allSelected = sortedAndFiltered.length > 0 && selected.length === sortedAndFiltered.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : sortedAndFiltered.map((d) => d.id))

  const total = useMemo(() => sortedAndFiltered.reduce((sum, d) => sum + d.amount, 0), [sortedAndFiltered])

  if (investments.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No investments recorded yet. Add your first mutual fund or PPF contribution above.
      </Typography>
    )
  }

  if (sortedAndFiltered.length === 0) {
    return (
      <Stack alignItems="center" spacing={1} sx={{ py: 4 }}>
        <Typography color="text.secondary">No investments match the current filters.</Typography>
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
          {hasActiveFilter && ` (of ${investments.length})`}
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
            disabled={investments.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${investments.length} investments? This cannot be undone.`)) {
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
              <SortableHeader active={sortColumn === 'scheme_name'} direction={sortDirection} onClick={() => handleSort('scheme_name')}>
                Scheme
              </SortableHeader>
              <SortableHeader active={sortColumn === 'category'} direction={sortDirection} onClick={() => handleSort('category')}>
                Category
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'amount'} direction={sortDirection} onClick={() => handleSort('amount')}>
                Amount
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'expected_return'} direction={sortDirection} onClick={() => handleSort('expected_return')}>
                Exp. Ret
              </SortableHeader>
              <TableCell>Notes</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
            <TableRow>
              <TableCell padding="checkbox" />
              <FilterCell value={filters.date ?? ''} onChange={(v) => handleFilter('date', v)} placeholder="Date" />
              <FilterCell value={filters.scheme_name ?? ''} onChange={(v) => handleFilter('scheme_name', v)} placeholder="Scheme" />
              <FilterCell value={filters.category ?? ''} onChange={(v) => handleFilter('category', v)} placeholder="Category" />
              <FilterCell align="right" value={filters.amount ?? ''} onChange={(v) => handleFilter('amount', v)} placeholder="Amount" />
              <FilterCell align="right" value={filters.expected_return ?? ''} onChange={(v) => handleFilter('expected_return', v)} placeholder="%" />
              <TableCell />
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((inv) => (
              <TableRow key={inv.id} hover selected={selected.includes(inv.id)}>
                <TableCell padding="checkbox">
                  <Checkbox size="small" checked={selected.includes(inv.id)} onChange={() => toggle(inv.id)} inputProps={{ 'aria-label': 'select' }} />
                </TableCell>
                <TableCell>{inv.date}</TableCell>
                <TableCell>{inv.scheme_name}</TableCell>
                <TableCell>
                  <Chip label={investmentCategoryLabel(inv.category)} size="small" variant="outlined" />
                </TableCell>
                <TableCell align="right">{formatMoney(inv.amount)}</TableCell>
                <TableCell align="right">
                  {inv.expected_return != null ? `${inv.expected_return}%` : '—'}
                </TableCell>
                <TableCell sx={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {inv.notes || '—'}
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => onEdit(inv)} aria-label="edit">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => onDelete(inv)} aria-label="delete">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={4} />
              <TableCell align="right" sx={{ fontWeight: 700 }}>
                {formatMoney(total)}
              </TableCell>
              <TableCell colSpan={3} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
