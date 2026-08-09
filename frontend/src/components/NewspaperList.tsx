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
import type { Newspaper } from '../types'
import { formatMoney } from '../utils/format'

interface Props {
  papers: Newspaper[]
  onEdit: (paper: Newspaper) => void
  onDelete: (paper: Newspaper) => void
  onBulkDelete: (ids: number[]) => void
  onDeleteAll: () => void
}

export default function NewspaperList({ papers, onEdit, onDelete, onBulkDelete, onDeleteAll }: Props) {
  const [selected, setSelected] = useState<number[]>([])
  const allSelected = papers.length > 0 && selected.length === papers.length

  const toggle = (id: number) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  const toggleAll = () => setSelected(allSelected ? [] : papers.map((p) => p.id))

  if (papers.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No newspaper subscriptions recorded.
      </Typography>
    )
  }

  return (
    <>
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} justifyContent="space-between">
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
          {selected.length > 0 ? `${selected.length} selected` : `${papers.length} records`}
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
              <TableCell>Name</TableCell>
              <TableCell>Month</TableCell>
              <TableCell align="right">Monthly Cost</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {papers.map((p) => (
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
