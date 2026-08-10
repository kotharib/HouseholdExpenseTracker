export const investmentCategoryLabels: Record<string, string> = {
  ppf: 'PPF',
  nps: 'NPS',
  ssy: 'Sukanya Samriddhi',
  scss: 'SCSS',
  nsc: 'NSC',
  fd: 'Fixed Deposit',
  rd: 'Recurring Deposit',
  sgb: 'Gold (SGB)',
  elss: 'ELSS',
  equity_mf: 'Equity Fund',
  index_fund: 'Index Fund',
  debt_mf: 'Debt Fund',
  hybrid_mf: 'Hybrid Fund',
}

export const investmentCategoryLabelsFull: Record<string, string> = {
  ppf: 'Public Provident Fund (PPF)',
  nps: 'National Pension System (NPS)',
  ssy: 'Sukanya Samriddhi Yojana (SSY)',
  scss: 'Senior Citizens Savings Scheme (SCSS)',
  nsc: 'National Savings Certificate (NSC)',
  fd: 'Bank Fixed Deposit (FD)',
  rd: 'Recurring Deposit (RD)',
  sgb: 'Sovereign Gold Bond (SGB)',
  elss: 'ELSS Mutual Fund',
  equity_mf: 'Equity Mutual Fund',
  index_fund: 'Index Fund / ETF',
  debt_mf: 'Debt Mutual Fund',
  hybrid_mf: 'Hybrid / Balanced Fund',
}

export function investmentCategoryLabel(cat: string): string {
  return investmentCategoryLabels[cat] ?? cat
}
