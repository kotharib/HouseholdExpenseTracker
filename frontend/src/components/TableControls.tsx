import { TableCell, TableSortLabel, TextField } from '@mui/material'
import type { ReactNode } from 'react'
import type { SortDirection } from '../utils/useTableControls'

interface SortableHeaderProps {
  active: boolean
  direction: SortDirection
  onClick: () => void
  align?: 'left' | 'right'
  children: ReactNode
}

export function SortableHeader({ active, direction, onClick, align = 'left', children }: SortableHeaderProps) {
  return (
    <TableCell align={align} sortDirection={active ? direction : false}>
      <TableSortLabel active={active} direction={active ? direction : 'asc'} onClick={onClick}>
        {children}
      </TableSortLabel>
    </TableCell>
  )
}

interface FilterCellProps {
  value: string
  onChange: (value: string) => void
  align?: 'left' | 'right'
  placeholder?: string
  width?: number
}

export function FilterCell({ value, onChange, align = 'left', placeholder = 'Filter', width }: FilterCellProps) {
  return (
    <TableCell align={align} sx={{ maxWidth: width ?? 220, minWidth: width ?? 96 }}>
      <TextField
        size="small"
        variant="standard"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        inputProps={{ 'aria-label': placeholder }}
        sx={{ width: '100%' }}
      />
    </TableCell>
  )
}
