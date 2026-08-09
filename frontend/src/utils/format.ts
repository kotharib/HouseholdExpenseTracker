const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })

export function formatMoney(value: number): string {
  return inr.format(value)
}

export function formatMoneyFixed(value: number): string {
  return `₹${value.toFixed(2)}`
}
