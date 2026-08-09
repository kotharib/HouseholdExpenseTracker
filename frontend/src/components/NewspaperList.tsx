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
import type { Newspaper } from '../types'
import { formatMoney } from '../utils/format'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  papers: Newspaper[]
  onEdit: (paper: Newspaper) => void
  onDelete: (paper: Newspaper) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function NewspaperList({ papers, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Newspaper>(papers)
  const allSelected = sortedAndFiltered.length > 0 && selected.length === sortedAndFiltered.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : sortedAndFiltered.map((p) => p.id))

  if (papers.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No newspaper subscriptions recorded.
      </Typography>
    )
  }

  if (sortedAndFiltered.length === 0) {
    return (
      <Stack alignItems="center" spacing={1} sx={{ py: 4 }}>
        <Typography color="text.secondary">No newspaper subscriptions match the current filters.</Typography>
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
          {hasActiveFilter && ` (of ${papers.length})`}
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
            disabled={papers.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${papers.length} newspaper subscriptions? This cannot be undone.`)) {
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
              <SortableHeader active={sortColumn === 'month'} direction={sortDirection} onClick={() => handleSort('month')}>
                Month
              </SortableHeader>
              <SortableHeader align="right" active={sortColumn === 'monthly_cost'} direction={sortDirection} onClick={() => handleSort('monthly_cost')}>
                Monthly Cost
              </SortableHeader>
              <SortableHeader active={sortColumn === 'payment_status'} direction={sortDirection} onClick={() => handleSort('payment_status')}>
                Status
              </SortableHeader>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
            <TableRow>
              <TableCell padding="checkbox" />
              <FilterCell value={filters.name ?? ''} onChange={(v) => handleFilter('name', v)} placeholder="Name" />
              <FilterCell value={filters.month ?? ''} onChange={(v) => handleFilter('month', v)} placeholder="Month" />
              <FilterCell align="right" value={filters.monthly_cost ?? ''} onChange={(v) => handleFilter('monthly_cost', v)} placeholder="Cost" />
              <FilterCell value={filters.payment_status ?? ''} onChange={(v) => handleFilter('payment_status', v)} placeholder="Status" />
              <TableCell align="right" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((p) => (
              <TableRow key={p.id} hover selected={selected.includes(p.id)}>
                <TableCell padding="checkbox">
                  <Checkbox size="small" checked={selected.includes(p.id)} onChange={() => toggle(p.id)} inputProps={{ 'aria-label': 'select' }} />
                </TableCell>
                <TableCell>{p.name}</TableCell>
                <TableCell>{p.month}</TableCell>
                <TableCell align="right">{formatMoney(p.monthly_cost)}</TableCell>
                <TableCell>
                  <Chip label={p.payment_status} size="small" color={p.payment_status === 'paid' ? 'success' : 'warning'} />
                </TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => onEdit(p)} aria-label="edit">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={() => onDelete(p)} aria-label="delete">
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
