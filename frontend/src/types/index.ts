export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Expense {
  id: number
  category: string
  amount: number
  date: string
  notes?: string
  payment_mode?: string
  tags?: string
  month: string
}

export interface ExpenseInput {
  category: string
  amount: number
  date: string
  notes?: string
  payment_mode?: string
  tags?: string
}

export interface Servant {
  id: number
  name: string
  role: string
  monthly_salary: number
  payment_status: 'pending' | 'paid'
  attendance_count: number
}

export interface ServantInput {
  name: string
  role: string
  monthly_salary: number
  payment_status: 'pending' | 'paid'
  attendance_count: number
}

export interface Milk {
  id: number
  supplier: string
  quantity: number
  rate: number
  date: string
  month: string
  payment_status: 'pending' | 'paid'
  total: number
}

export interface MilkInput {
  supplier: string
  quantity: number
  rate: number
  date: string
  month: string
  payment_status: 'pending' | 'paid'
}

export interface Newspaper {
  id: number
  name: string
  monthly_cost: number
  month: string
  payment_status: 'pending' | 'paid'
}

export interface NewspaperInput {
  name: string
  monthly_cost: number
  month: string
  payment_status: 'pending' | 'paid'
}

export interface CategoryTotal {
  category: string
  total: number
}

export interface MonthlyTotal {
  month: string
  total: number
}

export interface PendingPayment {
  type: 'servant' | 'milk' | 'newspaper'
  name: string
  amount: number
  month: string
}

export interface DashboardSummary {
  current_month: string
  current_month_total: number
  previous_month_total: number
  total_expenses: number
  expense_count: number
  servant_pending: number
  milk_pending: number
  newspaper_pending: number
  total_pending: number
  category_totals: CategoryTotal[]
  monthly_trend: MonthlyTotal[]
  pending_payments: PendingPayment[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AiInsights {
  insights: string
  llm_available: boolean
  data: Record<string, unknown>
}

export interface AiMonthlyReport {
  month: string
  report: string
  llm_available: boolean
}

export interface AutoReport {
  month: string
  title: string
  sections: string[]
  ai_summary: string
  pending: PendingPayment[]
  totals: {
    total_expenses: number
    pending: number
  }
  expense_count: number
  previous_month_total: number
  delta: number
  category_totals: CategoryTotal[]
  generated_at: string
}

export interface Page<T> {
  data: T[]
}

export const expenseCategories = [
  'groceries',
  'utilities',
  'transport',
  'entertainment',
  'health',
  'education',
  'household',
  'dining',
  'shopping',
  'travel',
  'insurance',
  'internet',
  'subscriptions',
  'ott',
  'other',
]
