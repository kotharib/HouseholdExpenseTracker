import { Button, Card, CardContent, Typography } from '@mui/material'
import { Lock as LockIcon } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { usePermissions } from '../utils/roles'

export default function AccessDeniedPage() {
  const navigate = useNavigate()
  const { role } = usePermissions()

  return (
    <div>
      <Card sx={{ maxWidth: 520, mx: 'auto', mt: 6 }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <LockIcon sx={{ fontSize: 56, color: 'error.main', mb: 2 }} />
          <Typography variant="h4" fontWeight={800} gutterBottom>
            Access Denied
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            You do not have permission to view this page. Your current role is{' '}
            <strong>{role}</strong>, which does not grant access to this area.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/')}>
            Go to Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
