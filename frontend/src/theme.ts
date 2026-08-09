import { createTheme } from '@mui/material/styles'
import type { ThemeMode } from './store/themeStore'

export function buildTheme(mode: ThemeMode) {
  return createTheme({
    palette: {
      mode,
      primary: { main: mode === 'light' ? '#2563eb' : '#90caf9' },
      secondary: { main: '#7c3aed' },
      background: mode === 'light' ? { default: '#f4f6fa', paper: '#ffffff' } : { default: '#0b1120', paper: '#111a2e' },
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: { fontWeight: 700 },
      h6: { fontWeight: 600 },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: mode === 'light' ? '0 1px 3px rgba(0,0,0,0.08)' : '0 1px 3px rgba(0,0,0,0.4)',
          },
        },
      },
      MuiButton: { defaultProps: { disableElevation: true } },
    },
  })
}
