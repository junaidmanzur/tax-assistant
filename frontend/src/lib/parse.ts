/** Parse income strings like "85,000", "85k" -> 85000 */
export function parseIncome(value: string): number | null {
  if (!value) return null;
  const cleaned = value.toLowerCase().replace(/[,\s]/g, '').replace(/k$/, '000');
  const n = Number(cleaned);
  if (!Number.isFinite(n) || n <= 0) return null;
  return Math.round(n);
}