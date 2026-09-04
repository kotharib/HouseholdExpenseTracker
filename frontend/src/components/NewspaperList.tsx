import {
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
import type { NewspaperDailyResponse, NewspaperDay, NewspaperGroup } from '../types'
import { formatMoney } from '../utils/format'
import { usePermissions } from '../utils/roles'

interface Props {
  daily: NewspaperDailyResponse
  onMarkStatus: (day: NewspaperDay, delivered: boolean, group: NewspaperGroup) => void
}

function statusLabel(value: boolean | null) {
  if (value === true) return 'Delivered'
  if (value === false) return 'Not delivered'
  return 'Unmarked'
}

export default function NewspaperList({ daily, onMarkStatus }: Props) {
  const { canWrite } = usePermissions()
  const groups = daily.newspapers

  if (groups.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
        No newspaper deliveries generated for this month. Add a newspaper subscription first.
      </Typography>
    )
  }

  return (
    <>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Newspaper</TableCell>
              <TableCell>Date</TableCell>
              <TableCell align="right">Monthly Cost</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((g) => {
              const dayRows = g.days.filter((d) => d.id != null)
              const deliveredCount = dayRows.filter((d) => d.delivered === true).length
              return [
                <TableRow key={`header-${g.name}`} sx={{ backgroundColor: (theme) => (theme.palette.mode === 'light' ? 'rgba(79,70,229,0.06)' : 'rgba(129,140,248,0.08)') }}>
                  <TableCell colSpan={2} sx={{ fontWeight: 700 }}>
                    {g.name}
                  </TableCell>
                  <TableCell align="right">{formatMoney(g.monthly_cost)}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      color={deliveredCount === dayRows.length && dayRows.length > 0 ? 'success' : 'warning'}
                      label={`${deliveredCount}/${dayRows.length} delivered`}
                    />
                  </TableCell>
                </TableRow>,
                ...dayRows.map((d) => (
                  <TableRow key={d.id} hover>
                    <TableCell />
                    <TableCell>{d.date}</TableCell>
                    <TableCell align="right" />
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip
                          size="small"
                          color={d.delivered === true ? 'success' : d.delivered === false ? 'error' : 'default'}
                          label={statusLabel(d.delivered)}
                        />
                        <ToggleButtonGroup
                          exclusive
                          size="small"
                          value={d.delivered}
                          disabled={!canWrite}
                          onChange={(_, value) => {
                            if (value === true || value === false) onMarkStatus(d, value, g)
                          }}
                        >
                          <ToggleButton value={true}>Delivered</ToggleButton>
                          <ToggleButton value={false}>Not delivered</ToggleButton>
                        </ToggleButtonGroup>
                      </Stack>
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
