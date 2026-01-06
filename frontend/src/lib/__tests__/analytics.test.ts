import { describe, it, expect } from 'vitest';
import { applyFilters } from '../analytics';
import type { ProcurementRecord } from '../../hooks/useProcurementData';
import type { Filters } from '../../hooks/useFilters';

/**
 * Helper to create a full Filters object with default empty values
 */
function createFilters(partial: Partial<Filters> = {}): Filters {
  return {
    dateRange: { start: null, end: null },
    categories: [],
    subcategories: [],
    suppliers: [],
    locations: [],
    years: [],
    amountRange: { min: null, max: null },
    ...partial,
  };
}

/**
 * Test suite for applyFilters utility
 *
 * Note: Other analytics calculations (totals, averages, aggregations)
 * are now handled by backend APIs and tested via API integration tests.
 */

const mockData: ProcurementRecord[] = [
  {
    date: '2024-01-15',
    supplier: 'Acme Corp',
    category: 'Office Supplies',
    amount: 1500,
    description: 'Pens and paper',
  },
  {
    date: '2024-01-20',
    supplier: 'Tech Solutions',
    category: 'IT Equipment',
    amount: 5000,
    description: 'Laptops',
  },
  {
    date: '2024-02-10',
    supplier: 'Acme Corp',
    category: 'Office Supplies',
    amount: 800,
    description: 'Staplers',
  },
  {
    date: '2024-02-15',
    supplier: 'Office Depot',
    category: 'Office Supplies',
    amount: 1200,
    description: 'Chairs',
  },
  {
    date: '2024-03-01',
    supplier: 'Tech Solutions',
    category: 'IT Equipment',
    amount: 3000,
    description: 'Monitors',
  },
];

describe('applyFilters', () => {

  describe('Date Range Filtering', () => {
    it('should filter by start date only', () => {
      const filters = createFilters({
        dateRange: { start: '2024-02-01', end: null },
      });

      const filtered = applyFilters(mockData, filters);

      // Should include records from Feb 10, Feb 15, Mar 01
      expect(filtered.length).toBe(3);
      expect(filtered.every(r => r.date >= '2024-02-01')).toBe(true);
    });

    it('should filter by end date only', () => {
      const filters = createFilters({
        dateRange: { start: null, end: '2024-02-01' },
      });

      const filtered = applyFilters(mockData, filters);

      // Should include records from Jan 15, Jan 20
      expect(filtered.length).toBe(2);
      expect(filtered.every(r => r.date <= '2024-02-01')).toBe(true);
    });

    it('should filter by date range', () => {
      const filters = createFilters({
        dateRange: { start: '2024-02-01', end: '2024-02-28' },
      });

      const filtered = applyFilters(mockData, filters);

      // Should include only Feb records
      expect(filtered.length).toBe(2);
      expect(filtered.every(r => r.date >= '2024-02-01' && r.date <= '2024-02-28')).toBe(true);
    });
  });

  describe('Category Filtering', () => {
    it('should filter by single category', () => {
      const filters = createFilters({
        categories: ['IT Equipment'],
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r => r.category === 'IT Equipment')).toBe(true);
      expect(filtered.length).toBe(2);
    });

    it('should filter by multiple categories', () => {
      const filters = createFilters({
        categories: ['IT Equipment', 'Office Supplies'],
      });

      const filtered = applyFilters(mockData, filters);

      // All records match these categories
      expect(filtered.length).toBe(mockData.length);
    });

    it('should return empty array for non-matching category', () => {
      const filters = createFilters({
        categories: ['Non-existent Category'],
      });

      const filtered = applyFilters(mockData, filters);
      expect(filtered.length).toBe(0);
    });
  });

  describe('Supplier Filtering', () => {
    it('should filter by single supplier', () => {
      const filters = createFilters({
        suppliers: ['Acme Corp'],
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r => r.supplier === 'Acme Corp')).toBe(true);
      expect(filtered.length).toBe(2);
    });

    it('should filter by multiple suppliers', () => {
      const filters = createFilters({
        suppliers: ['Acme Corp', 'Tech Solutions'],
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r =>
        r.supplier === 'Acme Corp' || r.supplier === 'Tech Solutions'
      )).toBe(true);
      expect(filtered.length).toBe(4);
    });
  });

  describe('Amount Range Filtering', () => {
    it('should filter by minimum amount only', () => {
      const filters = createFilters({
        amountRange: { min: 2000, max: null },
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r => r.amount >= 2000)).toBe(true);
      expect(filtered.length).toBe(2); // 5000 and 3000
    });

    it('should filter by maximum amount only', () => {
      const filters = createFilters({
        amountRange: { min: null, max: 1500 },
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r => r.amount <= 1500)).toBe(true);
      expect(filtered.length).toBe(3); // 1500, 800, 1200
    });

    it('should filter by amount range', () => {
      const filters = createFilters({
        amountRange: { min: 1000, max: 2000 },
      });

      const filtered = applyFilters(mockData, filters);

      expect(filtered.every(r => r.amount >= 1000 && r.amount <= 2000)).toBe(true);
      expect(filtered.length).toBe(2); // 1500, 1200
    });
  });

  describe('Combined Filters', () => {
    it('should apply multiple filters together', () => {
      const filters = createFilters({
        dateRange: { start: '2024-01-01', end: '2024-02-28' },
        categories: ['Office Supplies'],
        suppliers: ['Acme Corp'],
        amountRange: { min: 500, max: 2000 },
      });

      const filtered = applyFilters(mockData, filters);

      // Should match: Acme Corp, Office Supplies, Jan-Feb, 500-2000
      expect(filtered.length).toBe(2); // Jan 15 (1500) and Feb 10 (800)
      expect(filtered.every(r =>
        r.supplier === 'Acme Corp' &&
        r.category === 'Office Supplies' &&
        r.date >= '2024-01-01' &&
        r.date <= '2024-02-28' &&
        r.amount >= 500 &&
        r.amount <= 2000
      )).toBe(true);
    });

    it('should return all data when no filters applied', () => {
      const filters = createFilters();

      const filtered = applyFilters(mockData, filters);
      expect(filtered.length).toBe(mockData.length);
    });

    it('should handle empty data array', () => {
      const filters = createFilters({
        dateRange: { start: '2024-01-01', end: '2024-12-31' },
        categories: ['Office Supplies'],
      });

      const filtered = applyFilters([], filters);
      expect(filtered.length).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle invalid date formats gracefully', () => {
      const filters = createFilters({
        dateRange: { start: 'invalid-date', end: null },
      });

      // Should not crash, return all data or empty based on implementation
      const filtered = applyFilters(mockData, filters);
      expect(Array.isArray(filtered)).toBe(true);
    });

    it('should handle negative amounts in filter', () => {
      const filters = createFilters({
        amountRange: { min: -1000, max: 1000 },
      });

      const filtered = applyFilters(mockData, filters);
      expect(filtered.every(r => r.amount >= -1000 && r.amount <= 1000)).toBe(true);
    });

    it('should be case-sensitive for category and supplier names', () => {
      const filters = createFilters({
        categories: ['office supplies'], // lowercase
      });

      const filtered = applyFilters(mockData, filters);
      // Should not match 'Office Supplies' (capital O and S)
      expect(filtered.length).toBe(0);
    });
  });
});
