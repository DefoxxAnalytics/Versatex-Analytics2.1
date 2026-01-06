import type { ProcurementRecord } from '../hooks/useProcurementData';
import type { Filters } from '../hooks/useFilters';

/**
 * Analytics utilities for procurement data
 *
 * Note: Most analytics calculations are now handled by backend APIs.
 * This module contains only client-side filtering for drill-down functionality.
 *
 * Security: All inputs are validated, no unsafe operations
 * Performance: Optimized for large datasets with efficient algorithms
 */

/**
 * Apply filters to procurement data
 *
 * Filters data based on date range, categories, suppliers, and amount range.
 * All filters are applied with AND logic (all conditions must match).
 *
 * @param data - Array of procurement records to filter
 * @param filters - Filter criteria to apply
 * @returns Filtered array of procurement records
 *
 * Security:
 * - All inputs are validated
 * - No XSS vulnerabilities (React handles escaping)
 * - Safe string comparisons (case-sensitive)
 *
 * Performance:
 * - Single pass through data (O(n))
 * - Early returns for empty data
 * - Efficient Set lookups for categories/suppliers
 *
 * @example
 * ```ts
 * const filters = {
 *   dateRange: { start: '2024-01-01', end: '2024-12-31' },
 *   categories: ['IT Equipment'],
 *   suppliers: [],
 *   amountRange: { min: 1000, max: null }
 * };
 * const filtered = applyFilters(data, filters);
 * ```
 */
export function applyFilters(
  data: ProcurementRecord[],
  filters: Filters
): ProcurementRecord[] {
  // Validate inputs
  if (!data || data.length === 0) return [];
  if (!filters) return data;

  // Return all data if no filters are active
  const hasDateFilter = filters.dateRange.start !== null || filters.dateRange.end !== null;
  const hasCategoryFilter = filters.categories.length > 0;
  const hasSubcategoryFilter = filters.subcategories.length > 0;
  const hasSupplierFilter = filters.suppliers.length > 0;
  const hasLocationFilter = filters.locations.length > 0;
  const hasYearFilter = filters.years.length > 0;
  const hasAmountFilter = filters.amountRange.min !== null || filters.amountRange.max !== null;

  if (!hasDateFilter && !hasCategoryFilter && !hasSubcategoryFilter && !hasSupplierFilter && !hasLocationFilter && !hasYearFilter && !hasAmountFilter) {
    return data;
  }

  // Convert arrays to Sets for O(1) lookups
  const categorySet = new Set(filters.categories);
  const subcategorySet = new Set(filters.subcategories);
  const supplierSet = new Set(filters.suppliers);
  const locationSet = new Set(filters.locations);
  const yearSet = new Set(filters.years);

  // Filter data with a single pass
  return data.filter(record => {
    // Date range filter
    if (hasDateFilter) {
      const recordDate = record.date;

      if (filters.dateRange.start && recordDate < filters.dateRange.start) {
        return false;
      }

      if (filters.dateRange.end && recordDate > filters.dateRange.end) {
        return false;
      }
    }

    // Category filter
    if (hasCategoryFilter && !categorySet.has(record.category)) {
      return false;
    }

    // Subcategory filter
    if (hasSubcategoryFilter && !subcategorySet.has(record.subcategory)) {
      return false;
    }

    // Supplier filter
    if (hasSupplierFilter && !supplierSet.has(record.supplier)) {
      return false;
    }

    // Location filter
    if (hasLocationFilter && !locationSet.has(record.location)) {
      return false;
    }

    // Year filter - use year field if available, otherwise extract from date
    if (hasYearFilter) {
      const recordYear = record.year?.toString() || new Date(record.date).getFullYear().toString();
      if (!yearSet.has(recordYear)) {
        return false;
      }
    }

    // Amount range filter
    if (hasAmountFilter) {
      const amount = record.amount;

      if (filters.amountRange.min !== null && amount < filters.amountRange.min) {
        return false;
      }

      if (filters.amountRange.max !== null && amount > filters.amountRange.max) {
        return false;
      }
    }

    // All filters passed
    return true;
  });
}
