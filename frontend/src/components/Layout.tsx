import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import { styled } from '@mui/material/styles'
import { Article as ArticleIcon } from '@mui/icons-material'
import { Chat as ChatIcon } from '@mui/icons-material'
import { Dashboard as DashboardIcon } from '@mui/icons-material'
import { Description as DescriptionIcon } from '@mui/icons-material'
import { People as PeopleIcon } from '@mui/icons-material'
import { Receipt as ReceiptIcon } from '@mui/icons-material'
import { Settings as SettingsIcon } from '@mui/icons-material'
import { WaterDrop as WaterDropIcon } from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import type { ComponentType } from 'react'

interface NavItem {
  label: string
  path: string
  icon: ComponentType<{ fontSize?: 'small' | 'inherit' | 'medium' | 'large' }>
}

const drawerWidth = 240

const Main = styled('main')(({ theme }) => ({
  flexGrow: 1,
  minHeight: '100vh',
  backgroundColor: theme.palette.background.default,
  padding: theme.spacing(3),
  marginLeft: drawerWidth,
  [theme.breakpoints.down('md')]: {
    marginLeft: 0,
  },
}))

const Sidebar = styled('nav')(({ theme }) => ({
  width: drawerWidth,
  position: 'fixed',
  top: 0,
  bottom: 0,
  left: 0,
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.paper,
  borderRight: `1px solid ${theme.palette.divider}`,
  paddingTop: theme.spacing(2),
  overflowY: 'auto',
  [theme.breakpoints.down('md')]: {
    display: 'none',
  },
}))

const Brand = styled('div')(({ theme }) => ({
  padding: theme.spacing(2, 3),
  fontWeight: 700,
  fontSize: 18,
  color: theme.palette.primary.main,
}))

const StyledLink = styled(NavLink)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.5),
  padding: theme.spacing(1.2, 3),
  color: theme.palette.text.secondary,
  textDecoration: 'none',
  fontSize: 14,
  '&.active': {
    color: theme.palette.primary.main,
    backgroundColor: theme.palette.mode === 'light' ? 'rgba(37,99,235,0.08)' : 'rgba(144,202,249,0.12)',
    fontWeight: 600,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}))

const TopBar = styled('header')(({ theme }) => ({
  position: 'sticky',
  top: 0,
  zIndex: 10,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(1.5, 3),
  marginBottom: theme.spacing(3),
  backgroundColor: theme.palette.background.paper,
  borderBottom: `1px solid ${theme.palette.divider}`,
}))

export default function Layout() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const mode = useThemeStore((s) => s.mode)
  const toggle = useThemeStore((s) => s.toggle)
  const navigate = useNavigate()

  const items: NavItem[] = [
    { label: 'Dashboard', path: '/', icon: DashboardIcon },
    { label: 'Expenses', path: '/expenses', icon: ReceiptIcon },
    { label: 'Servants', path: '/servants', icon: PeopleIcon },
    { label: 'Milk', path: '/milk', icon: WaterDropIcon },
    { label: 'Newspaper', path: '/newspaper', icon: ArticleIcon },
    { label: 'AI Chat', path: '/chat', icon: ChatIcon },
    { label: 'Reports', path: '/reports', icon: DescriptionIcon },
    { label: 'Settings', path: '/settings', icon: SettingsIcon },
  ]

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar>
        <Brand>Household Finance</Brand>
        {items.map((item) => {
          const Icon = item.icon
          return (
            <StyledLink key={item.path} to={item.path} end={item.path === '/'}>
              <Icon fontSize="small" />
              <span>{item.label}</span>
            </StyledLink>
          )
        })}
      </Sidebar>
      <Main>
        <TopBar>
          <div style={{ fontSize: 14, color: 'text.secondary' }}>
            Welcome, <strong>{user?.username}</strong> ({user?.role})
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              onClick={toggle}
              style={{ border: '1px solid', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', background: 'transparent' }}
            >
              {mode === 'light' ? 'Dark' : 'Light'}
            </button>
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              style={{ border: '1px solid', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', background: 'transparent' }}
            >
              Logout
            </button>
          </div>
        </TopBar>
        <Outlet />
      </Main>
    </div>
  )
}
