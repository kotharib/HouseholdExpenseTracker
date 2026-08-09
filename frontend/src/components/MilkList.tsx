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
import { useMemo, useState } from 'react'
import type { Milk } from '../types'
import { formatMoney } from '../utils/format'

interface Props {
  deliveries: Milk[]
  onEdit: (delivery: Milk) => void
  onDelete: (delivery: Milk) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function MilkList({ deliveries, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const allSelected = deliveries.length > 0 && selected.length === deliveries.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : deliveries.map((d) => d.id))

  const total = useMemo(() => deliveries.reduce((sum, d) => sum + d.total, 0), [deliveries])

  if (deliveries.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No milk deliveries recorded.
      </Typography>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${deliveries.length} records`}
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
              <TableCell>Date</TableCell>
              <TableCell>Supplier</TableCell>
              <TableCell align="right">Qty (L)</TableCell>
              <TableCell align="right">Rate</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {deliveries.map((d) => (
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
