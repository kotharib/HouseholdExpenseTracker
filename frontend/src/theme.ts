import { createTheme } from '@mui/material/styles'
import type { ThemeMode } from './store/themeStore'

export function buildTheme(mode: ThemeMode) {
  const dark = mode === 'dark'
  return createTheme({
    palette: {
      mode,
      primary: { main: dark ? '#818cf8' : '#4f46e5', light: dark ? '#a5b4fc' : '#6366f1', dark: dark ? '#6366f1' : '#4338ca' },
      secondary: { main: dark ? '#22d3ee' : '#0891b2', light: dark ? '#67e8f9' : '#06b6d4', dark: dark ? '#06b6d4' : '#155e75' },
      success: { main: dark ? '#34d399' : '#059669' },
      warning: { main: dark ? '#fbbf24' : '#d97706' },
      error: { main: dark ? '#f87171' : '#dc2626' },
      background: dark
        ? { default: '#0b1220', paper: '#111a2e' }
        : { default: '#f3f4fb', paper: '#ffffff' },
      divider: dark ? 'rgba(148,163,184,0.16)' : 'rgba(100,116,139,0.16)',
      text: dark ? { primary: '#e2e8f0', secondary: '#94a3b8' } : { primary: '#0f172a', secondary: '#64748b' },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: { fontWeight: 800, letterSpacing: '-0.02em' },
      h5: { fontWeight: 700 },
      h6: { fontWeight: 700 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 14,
            overflow: 'hidden',
            transition: 'transform 0.2s ease, box-shadow 0.25s ease, border-color 0.25s ease',
            '&:hover': {
              transform: 'translateY(-3px)',
              boxShadow: dark
                ? '0 12px 32px rgba(0,0,0,0.45)'
                : '0 12px 32px rgba(79,70,229,0.14)',
            },
          },
        },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
          root: {
            transition: 'transform 0.15s ease, box-shadow 0.2s ease, background-color 0.2s ease',
            '&:active': { transform: 'scale(0.97)' },
          },
          containedPrimary: {
            backgroundImage: dark
              ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
              : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
          },
          containedSecondary: {
            backgroundImage: 'linear-gradient(135deg, #0891b2, #0d9488)',
          },
        },
      },
      MuiChip: { styleOverrides: { root: { borderRadius: 8 } } },
      MuiTableHead: {
        styleOverrides: {
          root: {
            backgroundColor: dark ? 'rgba(148,163,184,0.08)' : 'rgba(100,116,139,0.08)',
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: { fontWeight: 700 },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: dark
              ? 'linear-gradient(180deg, rgba(148,163,184,0.06), transparent)'
              : 'none',
          },
        },
      },
      MuiTextField: {
        defaultProps: { size: 'small' },
      },
      MuiTable: { defaultProps: { size: 'small' } },
    },
  })
}
