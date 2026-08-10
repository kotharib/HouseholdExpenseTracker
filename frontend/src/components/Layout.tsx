import { NavLink, useLocation, useNavigate, Outlet } from 'react-router-dom'
import { styled } from '@mui/material/styles'
import { Article as ArticleIcon, Chat as ChatIcon, Dashboard as DashboardIcon, DarkMode as DarkModeIcon, Description as DescriptionIcon, LightMode as LightModeIcon, Logout as LogoutIcon, People as PeopleIcon, Receipt as ReceiptIcon, Settings as SettingsIcon, Savings as SavingsIcon, ShowChart as ShowChartIcon, WaterDrop as WaterDropIcon } from '@mui/icons-material'
import { IconButton, Stack, Tooltip } from '@mui/material'
import { useAuthStore } from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import type { ComponentType } from 'react'

interface NavItem {
  label: string
  path: string
  icon: ComponentType<{ fontSize?: 'small' | 'inherit' | 'medium' | 'large' }>
}

const drawerWidth = 248

const Main = styled('main')(({ theme }) => ({
  flexGrow: 1,
  minHeight: '100vh',
  backgroundColor: theme.palette.background.default,
  backgroundImage: `radial-gradient(circle at 15% 0%, ${theme.palette.primary.main}14, transparent 40%), radial-gradient(circle at 95% 10%, ${theme.palette.secondary.main}14, transparent 35%)`,
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
  zIndex: 20,
  [theme.breakpoints.down('md')]: {
    display: 'none',
  },
}))

const Brand = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.5),
  padding: theme.spacing(1.5, 3),
  marginBottom: theme.spacing(2),
}))

const BrandBadge = styled('div')(({ theme }) => ({
  width: 40,
  height: 40,
  borderRadius: 12,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: '#fff',
  background: theme.palette.mode === 'light'
    ? 'linear-gradient(135deg, #4f46e5, #7c3aed)'
    : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
  boxShadow: theme.palette.mode === 'light'
    ? '0 6px 16px rgba(79,70,229,0.35)'
    : '0 6px 16px rgba(99,102,241,0.4)',
  animation: 'floaty 5s ease-in-out infinite',
}))

const BrandText = styled('div')(({ theme }) => ({
  fontWeight: 800,
  fontSize: 17,
  letterSpacing: '-0.01em',
  background: theme.palette.mode === 'light'
    ? 'linear-gradient(90deg, #4f46e5, #7c3aed)'
    : 'linear-gradient(90deg, #a5b4fc, #67e8f9)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
}))

const StyledLink = styled(NavLink)(({ theme }) => ({
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.5),
  margin: theme.spacing(0.4, 1.5),
  padding: theme.spacing(1.1, 1.5),
  borderRadius: 10,
  color: theme.palette.text.secondary,
  textDecoration: 'none',
  fontSize: 14,
  transition: 'all 0.18s ease',
  '&::before': {
    content: '""',
    position: 'absolute',
    left: 0,
    top: '50%',
    transform: 'translateY(-50%) scaleY(0)',
    width: 3,
    height: '60%',
    borderRadius: 4,
    background: theme.palette.primary.main,
    transition: 'transform 0.2s ease',
  },
  '&:hover': {
    backgroundColor: theme.palette.mode === 'light' ? 'rgba(79,70,229,0.06)' : 'rgba(148,163,184,0.08)',
    color: theme.palette.text.primary,
    transform: 'translateX(3px)',
  },
  '&.active': {
    color: theme.palette.primary.main,
    backgroundColor: theme.palette.mode === 'light' ? 'rgba(79,70,229,0.1)' : 'rgba(129,140,248,0.14)',
    fontWeight: 600,
    '&::before': { transform: 'translateY(-50%) scaleY(1)' },
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
  borderRadius: 12,
  backgroundColor: theme.palette.background.paper,
  border: `1px solid ${theme.palette.divider}`,
  boxShadow: theme.palette.mode === 'light' ? '0 4px 16px rgba(15,23,42,0.06)' : '0 4px 16px rgba(0,0,0,0.4)',
}))

export default function Layout() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const mode = useThemeStore((s) => s.mode)
  const toggle = useThemeStore((s) => s.toggle)
  const navigate = useNavigate()
  const location = useLocation()

  const items: NavItem[] = [
    { label: 'Dashboard', path: '/', icon: DashboardIcon },
    { label: 'Expenses', path: '/expenses', icon: ReceiptIcon },
    { label: 'Investments', path: '/investments', icon: ShowChartIcon },
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
        <Brand>
          <BrandBadge>
            <SavingsIcon fontSize="small" />
          </BrandBadge>
          <BrandText>Household Finance</BrandText>
        </Brand>
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
          <Stack direction="row" spacing={0.5}>
            <Tooltip title={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
              <IconButton onClick={toggle} size="small">
                {mode === 'light' ? <DarkModeIcon fontSize="small" /> : <LightModeIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Logout">
              <IconButton
                onClick={() => {
                  logout()
                  navigate('/login')
                }}
                size="small"
              >
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </TopBar>
        <div className="page-enter" key={location.pathname}>
          <Outlet />
        </div>
      </Main>
    </div>
  )
}
