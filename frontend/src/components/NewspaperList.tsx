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
import { Delete as DeleteIcon, DeleteSweep as DeleteSweepIcon } from '@mui/icons-material'
import { useState } from 'react'
import type { NewspaperDailyResponse, NewspaperDay, NewspaperGroup } from '../types'
import { formatMoney } from '../utils/format'

interface Props {
  daily: NewspaperDailyResponse
  onToggleDelivered: (day: NewspaperDay, group: NewspaperGroup) => void
  onDelete: (day: NewspaperDay, group: NewspaperGroup) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function NewspaperList({ daily, onToggleDelivered, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const groups = daily.newspapers

  const allRows = groups.flatMap((g) =>
    g.days.filter((d) => d.id != null).map((d) => ({ id: d.id as number, date: d.date, name: g.name })),
  )
  const allSelected = allRows.length > 0 && selected.length === allRows.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : allRows.map((r) => r.id))

  if (groups.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No newspaper deliveries recorded for this month.
      </Typography>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${allRows.length} daily records`}
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
            disabled={allRows.length === 0}
            onClick={() => {
              if (window.confirm(`Delete ALL ${allRows.length} newspaper delivery records? This cannot be undone.`)) {
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
              <TableCell>Newspaper</TableCell>
              <TableCell>Date</TableCell>
              <TableCell align="right">Monthly Cost</TableCell>
              <TableCell>Delivered</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((g) => {
              const dayRows = g.days.filter((d) => d.id != null)
              return [
                <TableRow key={`header-${g.name}`} sx={{ backgroundColor: (theme) => (theme.palette.mode === 'light' ? 'rgba(79,70,229,0.06)' : 'rgba(129,140,248,0.08)') }}>
                  <TableCell padding="checkbox" />
                  <TableCell colSpan={2} sx={{ fontWeight: 700 }}>
                    {g.name}
                  </TableCell>
                  <TableCell align="right">{formatMoney(g.monthly_cost)}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      color={g.days_delivered === g.days_total ? 'success' : 'warning'}
                      label={`${g.days_delivered}/${g.days_total} days`}
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700 }}>
                    {formatMoney(g.total)}
                  </TableCell>
                </TableRow>,
                ...dayRows.map((d) => (
                  <TableRow key={d.id} hover selected={selected.includes(d.id as number)}>
                    <TableCell padding="checkbox">
                      <Checkbox size="small" checked={selected.includes(d.id as number)} onChange={() => toggle(d.id as number)} inputProps={{ 'aria-label': 'select' }} />
                    </TableCell>
                    <TableCell />
                    <TableCell>{d.date}</TableCell>
                    <TableCell align="right" />
                    <TableCell>
                      <Checkbox size="small" checked={d.delivered} onChange={() => onToggleDelivered(d, g)} title="Toggle delivered" />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => onDelete(d, g)} aria-label="delete">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                )),
              ]
            })}
          </TableBody>
        </Table>
      </TableContainer>
      {daily.missed_days > 0 && (
        <Typography variant="caption" color="error" sx={{ display: 'block', mt: 1 }}>
          {daily.missed_days} missed delivery day{daily.missed_days === 1 ? '' : 's'} this month.
        </Typography>
      )}
    </>
  )
}
