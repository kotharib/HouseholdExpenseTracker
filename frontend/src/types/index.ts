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
  is_delivered: boolean
  payment_status: 'pending' | 'paid'
  total: number
}

export interface MilkInput {
  supplier: string
  quantity: number
  rate: number
  date: string
  month: string
  is_delivered: boolean
  payment_status: 'pending' | 'paid'
}

export interface Newspaper {
  id: number
  name: string
  monthly_cost: number
  date: string
  month: string
  delivery_status: boolean
  payment_status: 'pending' | 'paid'
}

export interface NewspaperInput {
  name: string
  monthly_cost: number
  date?: string
  month: string
  delivery_status?: boolean
  payment_status: 'pending' | 'paid'
}

export interface MilkDay {
  id: number | null
  date: string
  supplier: string
  quantity: number
  rate: number
  total: number
  delivered: boolean
  payment_status: 'pending' | 'paid'
}

export interface MilkDailyResponse {
  year: number
  month: string
  month_label: string
  days: MilkDay[]
  delivered_days: number
  missed_days: number
}

export interface NewspaperDay {
  id: number | null
  date: string
  delivered: boolean
}

export interface NewspaperGroup {
  name: string
  monthly_cost: number
  days_delivered: number
  days_total: number
  total: number
  days: NewspaperDay[]
}

export interface NewspaperDailyResponse {
  year: number
  month: string
  month_label: string
  newspapers: NewspaperGroup[]
  total_delivered: number
  missed_days: number
}

export interface MilkBillDetail {
  date: string
  supplier: string
  quantity: number
  rate: number
  total: number
  delivered: boolean
  payment_status: 'pending' | 'paid'
}

export interface NewspaperBillDetail {
  name: string
  monthly_cost: number
  days_delivered: number
  total: number
}

export interface ServantBillDetail {
  name: string
  role: string
  monthly_salary: number
}

export interface ExpenseBillDetail {
  id: number
  category: string
  amount: number
  date: string
  notes?: string
  payment_mode?: string
}

export interface MonthlyBill {
  month: string
  month_label: string
  milk_bill: number
  newspaper_bill: number
  servant_salary_total: number
  expenses_total: number
  grand_total: number
  milk_details: MilkBillDetail[]
  newspaper_details: NewspaperBillDetail[]
  servant_details: ServantBillDetail[]
  expense_details: ExpenseBillDetail[]
}

export interface DeliverySummary {
  milk_total_days: number
  milk_delivered_days: number
  milk_missed_days: number
  newspaper_delivered_days: number
  newspaper_missed_days: number
  total_missed_deliveries: number
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
  delivery_summary?: DeliverySummary | null
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

export interface Investment {
  id: number
  scheme_name: string
  category: string
  amount: number
  date: string
  month: string
  expected_return?: number
  notes?: string
}

export interface InvestmentInput {
  scheme_name: string
  category: string
  amount: number
  date: string
  month: string
  expected_return?: number
  notes?: string
}

export interface InvestmentOption {
  key: string
  name: string
  category: string
  asset_class: string
  risk: 'low' | 'medium' | 'high'
  expected_return: number
  lock_in: string
  tax_benefit: string
  description: string
}

export interface RiskProfile {
  key: string
  label: string
}

export interface AllocationItem {
  asset_class: string
  label: string
  percent: number
  amount: number
}

export interface AllocationResponse {
  profile: string
  description: string
  total: number
  items: AllocationItem[]
}

export interface AdvisorResponse {
  allocation: AllocationResponse
  schemes: InvestmentOption[]
  profiles: RiskProfile[]
  disclaimer: string
}

export interface InvestmentSummary {
  count: number
  total: number
  by_category: Record<string, number>
}

export interface InvestmentAdvisorRequest {
  amount: number
  profile: string
  months?: number
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
