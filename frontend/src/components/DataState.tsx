import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
} from '@mui/material'

interface StateProps {
  loading?: boolean
  error?: string
  empty?: string
  onRetry?: () => void
}

export default function DataState({ loading, error, empty, onRetry }: StateProps) {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    )
  }
  if (error) {
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Alert severity="error">{error}</Alert>
          {onRetry && (
            <Button onClick={onRetry} sx={{ mt: 1 }}>
              Retry
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }
  if (empty) {
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography color="text.secondary">{empty}</Typography>
        </CardContent>
      </Card>
    )
  }
  return null
}
