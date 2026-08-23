import { useAuthStore } from '../store/authStore'
import type { Role } from '../types'

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Admin',
  user: 'User',
  viewer: 'Viewer',
}

export interface RolePermissions {
  role: Role
  isAdmin: boolean
  isUser: boolean
  isViewer: boolean
  /** Can create/update records in the household modules. */
  canWrite: boolean
  /** Can delete records (bulk and single). */
  canDelete: boolean
  /** Can manage servant salaries (create/update/delete). */
  canManageServants: boolean
  /** Can use the AI chat assistant. */
  canChat: boolean
}

export function usePermissions(): RolePermissions {
  const role = useAuthStore((s) => s.user?.role ?? 'viewer')
  return {
    role,
    isAdmin: role === 'admin',
    isUser: role === 'user',
    isViewer: role === 'viewer',
    canWrite: role === 'admin' || role === 'user',
    canDelete: role === 'admin',
    canManageServants: role === 'admin',
    canChat: role === 'admin' || role === 'user',
  }
}
