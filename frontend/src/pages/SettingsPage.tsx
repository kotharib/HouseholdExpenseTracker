import { Card, CardContent, FormControlLabel, List, ListItem, ListItemText, Switch, Typography } from '@mui/material'
import { useThemeStore } from '../store/themeStore'

export default function SettingsPage() {
  const mode = useThemeStore((s) => s.mode)
  const toggle = useThemeStore((s) => s.toggle)

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Appearance
          </Typography>
          <FormControlLabel
            control={<Switch checked={mode === 'dark'} onChange={toggle} />}
            label={mode === 'dark' ? 'Dark mode enabled' : 'Light mode enabled'}
          />
        </CardContent>
      </Card>

      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI & Reports
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText
                primary="Local LLM"
                secondary="Powered by Ollama + llama3 via LangChain. If Ollama is not running, a deterministic fallback engine answers from the database."
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Auto-report"
                secondary="GET /reports/auto produces expense + pending summaries with AI insights."
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Monthly PDF"
                secondary="GET /reports/monthly/pdf renders a ReportLab PDF with charts, tables and AI text."
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </div>
  )
}
