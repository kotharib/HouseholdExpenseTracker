import { Box, Typography } from '@mui/material'
import type { YearlyGraphData } from '../types'
import GraphVisuals from './GraphVisuals'

export default function GraphSection({ data }: { data: YearlyGraphData }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Graphs & Trends
      </Typography>
      <GraphVisuals data={data} />
    </Box>
  )
}
