import { Typography } from '@mui/material'
import ReportViewer from '../components/ReportViewer'

export default function ReportsPage() {
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>
      <ReportViewer />
    </div>
  )
}
