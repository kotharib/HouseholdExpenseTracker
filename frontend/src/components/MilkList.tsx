import {
  Button,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { FilterAltOff as FilterAltOffIcon } from '@mui/icons-material'
import { useMemo } from 'react'
import type { Milk } from '../types'
import { formatMoney } from '../utils/format'
import { usePermissions } from '../utils/roles'
import { useTableControls } from '../utils/useTableControls'
import { FilterCell, SortableHeader } from './TableControls'

interface Props {
  deliveries: Milk[]
  onMarkStatus: (delivery: Milk, delivered: boolean) => void
}

function statusLabel(value: boolean | null) {
  if (value === true) return 'Delivered'
  if (value === false) return 'Not delivered'
  return 'Unmarked'
}

export default function MilkList({ deliveries, onMarkStatus }: Props) {
  const { canWrite } = usePermissions()
  const { sortColumn, sortDirection, filters, sortedAndFiltered, handleSort, handleFilter, clearFilters, hasActiveFilter } =
    useTableControls<Milk>(deliveries)

  const total = useMemo(
    () => sortedAndFiltered.reduce((sum, d) => sum + (d.is_delivered ? d.total : 0), 0),
    [sortedAndFiltered],
  )

  if (deliveries.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No milk deliveries generated for this month. Add a milk subscription first.
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
          {sortedAndFiltered.length} scheduled days
          {hasActiveFilter && ` (of ${deliveries.length})`}
        </Typography>
        {hasActiveFilter && (
          <Button size="small" startIcon={<FilterAltOffIcon />} onClick={clearFilters}>
            Clear
          </Button>
        )}
      </Stack>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
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
              <SortableHeader active={sortColumn === 'is_delivered'} direction={sortDirection} onClick={() => handleSort('is_delivered')}>
                Status
              </SortableHeader>
            </TableRow>
            <TableRow>
              <FilterCell value={filters.date ?? ''} onChange={(v) => handleFilter('date', v)} placeholder="Date" />
              <FilterCell value={filters.supplier ?? ''} onChange={(v) => handleFilter('supplier', v)} placeholder="Supplier" />
              <FilterCell align="right" value={filters.quantity ?? ''} onChange={(v) => handleFilter('quantity', v)} placeholder="Qty" />
              <FilterCell align="right" value={filters.rate ?? ''} onChange={(v) => handleFilter('rate', v)} placeholder="Rate" />
              <FilterCell align="right" value={filters.total ?? ''} onChange={(v) => handleFilter('total', v)} placeholder="Total" />
              <FilterCell value={filters.is_delivered ?? ''} onChange={(v) => handleFilter('is_delivered', v)} placeholder="Status" />
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAndFiltered.map((d) => (
              <TableRow key={d.id} hover>
                <TableCell>{d.date}</TableCell>
                <TableCell>{d.supplier}</TableCell>
                <TableCell align="right">{d.quantity}</TableCell>
                <TableCell align="right">{formatMoney(d.rate)}</TableCell>
                <TableCell align="right">{formatMoney(d.total)}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip
                      size="small"
                      color={d.is_delivered === true ? 'success' : d.is_delivered === false ? 'error' : 'default'}
                      label={statusLabel(d.is_delivered)}
                    />
                    <ToggleButtonGroup
                      exclusive
                      size="small"
                      value={d.is_delivered}
                      disabled={!canWrite}
                      onChange={(_, value) => {
                        if (value === true || value === false) onMarkStatus(d, value)
                      }}
                    >
                      <ToggleButton value={true}>Delivered</ToggleButton>
                      <ToggleButton value={false}>Not delivered</ToggleButton>
                    </ToggleButtonGroup>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={4} />
              <TableCell align="right" sx={{ fontWeight: 700 }}>
                {formatMoney(total)}
              </TableCell>
              <TableCell />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
