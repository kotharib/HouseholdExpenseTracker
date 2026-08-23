import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import type { Role } from '../types'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  /** Roles allowed to view this route. When omitted, any authenticated role may access. */
  roles?: Role[]
}

export default function ProtectedRoute({ children, roles }: Props) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (roles && (!role || !roles.includes(role))) {
    return <Navigate to="/access-denied" replace />
  }

  return <>{children}</>
}
