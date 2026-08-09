import { useMemo, useState } from 'react'

export type SortDirection = 'asc' | 'desc'

interface Filters {
  [column: string]: string
}

interface TableControls<T> {
  sortColumn: keyof T | null
  sortDirection: SortDirection
  filters: Filters
  sortedAndFiltered: T[]
  handleSort: (column: keyof T) => void
  handleFilter: (column: string, value: string) => void
  clearFilters: () => void
  hasActiveFilter: boolean
}

function compareValues(a: unknown, b: unknown): number {
  if (a == null && b == null) return 0
  if (a == null) return -1
  if (b == null) return 1
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b))
}

export function useTableControls<T>(rows: T[]): TableControls<T> {
  const [sortColumn, setSortColumn] = useState<keyof T | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [filters, setFilters] = useState<Filters>({})

  const handleSort = (column: keyof T) => {
    if (sortColumn === column) {
      setSortDirection((dir) => (dir === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const handleFilter = (column: string, value: string) => {
    setFilters((prev) => {
      const next = { ...prev }
      if (value === '') delete next[column]
      else next[column] = value.toLowerCase()
      return next
    })
  }

  const clearFilters = () => setFilters({})

  const activeColumns = Object.keys(filters)

  const sortedAndFiltered = useMemo(() => {
    let list = rows
    if (activeColumns.length > 0) {
      list = rows.filter((row) =>
        activeColumns.every((column) => {
          const cell = (row as unknown as Record<string, unknown>)[column]
          const text = cell == null ? '' : String(cell).toLowerCase()
          return text.includes(filters[column])
        }),
      )
    }
    if (sortColumn) {
      const column = sortColumn as string
      list = [...list].sort((a, b) => {
        const av = (a as unknown as Record<string, unknown>)[column]
        const bv = (b as unknown as Record<string, unknown>)[column]
        const cmp = compareValues(av, bv)
        return sortDirection === 'asc' ? cmp : -cmp
      })
    }
    return list
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, filters, sortColumn, sortDirection])

  return {
    sortColumn,
    sortDirection,
    filters,
    sortedAndFiltered,
    handleSort,
    handleFilter,
    clearFilters,
    hasActiveFilter: activeColumns.length > 0,
  }
}
