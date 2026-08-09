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
import type { Milk } from '../types'
import { formatMoney } from '../utils/format'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  deliveries: Milk[]
  onEdit: (delivery: Milk) => void
  onDelete: (delivery: Milk) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function MilkList({ deliveries, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Milk>(deliveries)
  const allSelected = sortedAndFiltered.length > 0 && selected.length === sortedAndFiltered.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : sortedAndFiltered.map((d) => d.id))

  const total = useMemo(() => sortedAndFiltered.reduce((sum, d) => sum + d.total, 0), [sortedAndFiltered])

  if (deliveries.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No milk deliveries recorded.
      </Typography>
    )
  }

  if (sortedAndFiltered.length === 0) {
    return (
      <Stack alignItems="center" spacing={1} sx={{ py: 4 }}>
        <Typography color="text.secondary">No milk deliveries match the current filters.</Typography>
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
          {hasActiveFilter && ` (of ${deliveries.length})`}
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
            disabled={deliveries.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${deliveries.length} milk deliveries? This cannot be undone.`)) {
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
              <SortableHeader active={sortColumn === 'supplier'} direction={sortDirection} onClick={() => handleSort('supplier')}>
                Supplier
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'quantity'} direction={sortDirection} onClick={() => handleSort('quantity')}>
                Qty (L)
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'rate'} direction={sortDirection} onClick={() => handleSort('rate')}>
                Rate
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'total'} direction={sortDirection} onClick={() => handleSort('total')}>
                Total
              </SortableHeader>
              <SortableHeader active={sortColumn === 'payment_status'} direction={sortDirection} onClick={() => handleSort('payment_status')}>
                Status
              </SortableHeader>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
            <TableRow>
              <TableCell padding="checkbox" />
              <FilterCell value={filters.date ?? ''} onChange={(v) => handleFilter('date', v)} placeholder="Date" />
              <FilterCell value={filters.supplier ?? ''} onChange={(v) => handleFilter('supplier', v)} placeholder="Supplier" />
              <FilterCell align="right" value={filters.quantity ?? ''} onChange={(v) => handleFilter('quantity', v)} placeholder="Qty" />
              <FilterCell align="right" value={filters.rate ?? ''} onChange={(v) => handleFilter('rate', v)} placeholder="Rate" />
              <FilterCell align="right" value={filters.total ?? ''} onChange={(v) => handleFilter('total', v)} placeholder="Total" />
              <FilterCell value={filters.payment_status ?? ''} onChange={(v) => handleFilter('payment_status', v)} placeholder="Status" />
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((d) => (
              <TableRow key={d.id} hover selected={selected.includes(d.id)}>
                <TableCell padding="checkbox">
                  <Checkbox size="small" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} inputProps={{ 'aria-label': 'select' }} />
                </TableCell>
                <TableCell>{d.date}</TableCell>
                <TableCell>{d.supplier}</TableCell>
                <TableCell align="right">{d.quantity}</TableCell>
                <TableCell align="right">{formatMoney(d.rate)}</TableCell>
                <TableCell align="right">{formatMoney(d.total)}</TableCell>
                <TableCell>
                  <Chip label={d.payment_status} size="small" color={d.payment_status === 'paid' ? 'success' : 'warning'} />
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => onEdit(d)} aria-label="edit">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => onDelete(d)} aria-label="delete">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={5} />
              <TableCell align="right" sx={{ fontWeight: 700 }}>
                {formatMoney(total)}
              </TableCell>
              <TableCell colSpan={2} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
