import { Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material'
import {
  Article as ArticleIcon,
  Groups as GroupsIcon,
  Receipt as ReceiptIcon,
  Savings as SavingsIcon,
  WaterDrop as WaterDropIcon,
} from '@mui/icons-material'
import type { ComponentType } from 'react'
import type { YearlyBillSummary as YearlyBillSummaryData } from '../types'
import { formatMoney } from '../utils/format'
import { useCountUp } from '../utils/useCountUp'

function Item({
  label,
  value,
  color,
  icon: Icon,
}: {
  label: string
  value: number
  color: string
  icon: ComponentType<{ fontSize?: 'small' | 'inherit' | 'medium' | 'large' }>
}) {
  const animated = useCountUp(value)
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              background: `linear-gradient(135deg, ${color}, ${color}99)`,
            }}
          >
            <Icon fontSize="small" />
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={800} sx={{ color }}>
              {formatMoney(animated)}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default function YearlyBillSummary({ data }: { data: YearlyBillSummaryData }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Yearly Bill Summary
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={4}>
          <Item label="Total milk cost" value={data.milk_cost} color="#0d9488" icon={WaterDropIcon} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Item label="Total newspaper cost" value={data.newspaper_cost} color="#7c3aed" icon={ArticleIcon} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Item label="Total servant salary" value={data.servant_salary} color="#0891b2" icon={GroupsIcon} />
        </Grid>
        <Grid item xs={12} sm={6} md={6}>
          <Item label="Total expenses" value={data.expenses_total} color="#d97706" icon={ReceiptIcon} />
        </Grid>
        <Grid item xs={12} sm={6} md={6}>
          <Item label="Total household cost" value={data.household_cost} color="#4f46e5" icon={SavingsIcon} />
        </Grid>
      </Grid>
    </Box>
  )
}
