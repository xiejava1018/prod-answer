/**
 * Date utility functions
 */
import dayjs from 'dayjs'

/**
 * Format date to 'YYYY-MM-DD HH:mm:ss' format
 * @param date - Date string or Date object
 * @returns Formatted date string or '-' if date is falsy
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * Format date to 'YYYY-MM-DD' format
 * @param date - Date string or Date object
 * @returns Formatted date string or '-' if date is falsy
 */
export function formatDateShort(date: string | Date | null | undefined): string {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

/**
 * Format date to relative time (e.g., '5 minutes ago')
 * @param date - Date string or Date object
 * @returns Relative time string or '-' if date is falsy
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '-'
  return dayjs(date).fromNow()
}

/**
 * Get current date in 'YYYY-MM-DD HH:mm:ss' format
 * @returns Current date string
 */
export function getCurrentDateTime(): string {
  return dayjs().format('YYYY-MM-DD HH:mm:ss')
}
