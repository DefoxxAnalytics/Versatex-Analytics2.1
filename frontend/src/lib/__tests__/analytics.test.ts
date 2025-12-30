import { describe, it, expect } from 'vitest';
import {
  calculateTotalSpend,
  calculateSupplierCount,
  calculateCategoryCount,
  calculateAverageTransaction,
  getTopSuppliers,
  getSpendByCategory,
  getLargestTransaction,
  getMostFrequentSupplier,
  getHighestSpendingCategory,
  applyFilters,
} from '../analytics';
import type { ProcurementRecord } from '../csvParser';
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
 * Test suite for analytics utilities
 * Validates all calculation functions for procurement data
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

describe('Analytics Utilities', () => {
  describe('calculateTotalSpend', () => {
    it('should calculate total spend correctly', () => {
      const total = calculateTotalSpend(mockData);
      expect(total).toBe(11500);
    });

    it('should return 0 for empty data', () => {
      const total = calculateTotalSpend([]);
      expect(total).toBe(0);
    });

    it('should handle single record', () => {
      const total = calculateTotalSpend([mockData[0]]);
      expect(total).toBe(1500);
    });
  });

  describe('calculateSupplierCount', () => {
    it('should count unique suppliers correctly', () => {
      const count = calculateSupplierCount(mockData);
      expect(count).toBe(3); // Acme Corp, Tech Solutions, Office Depot
    });

    it('should return 0 for empty data', () => {
      const count = calculateSupplierCount([]);
      expect(count).toBe(0);
    });

    it('should handle duplicate suppliers', () => {
      const duplicates: ProcurementRecord[] = [
        { ...mockData[0] },
        { ...mockData[0] },
      ];
      const count = calculateSupplierCount(duplicates);
      expect(count).toBe(1);
    });
  });

  describe('calculateCategoryCount', () => {
    it('should count unique categories correctly', () => {
      const count = calculateCategoryCount(mockData);
      expect(count).toBe(2); // Office Supplies, IT Equipment
    });

    it('should return 0 for empty data', () => {
      const count = calculateCategoryCount([]);
      expect(count).toBe(0);
    });
  });

  describe('calculateAverageTransaction', () => {
    it('should calculate average transaction correctly', () => {
      const avg = calculateAverageTransaction(mockData);
      expect(avg).toBe(2300); // 11500 / 5
    });

    it('should return 0 for empty data', () => {
      const avg = calculateAverageTransaction([]);
      expect(avg).toBe(0);
    });

    it('should round to 2 decimal places', () => {
      const data: ProcurementRecord[] = [
        { ...mockData[0], amount: 100 },
        { ...mockData[1], amount: 150 },
        { ...mockData[2], amount: 175 },
      ];
      const avg = calculateAverageTransaction(data);
      expect(avg).toBe(141.67);
    });
  });

  describe('getTopSuppliers', () => {
    it('should return top suppliers by spend', () => {
      const top = getTopSuppliers(mockData, 2);
      expect(top).toHaveLength(2);
      expect(top[0].supplier).toBe('Tech Solutions');
      expect(top[0].totalSpend).toBe(8000);
      expect(top[1].supplier).toBe('Acme Corp');
      expect(top[1].totalSpend).toBe(2300);
    });

    it('should return all suppliers if limit exceeds count', () => {
      const top = getTopSuppliers(mockData, 10);
      expect(top).toHaveLength(3);
    });

    it('should return empty array for empty data', () => {
      const top = getTopSuppliers([], 5);
      expect(top).toEqual([]);
    });

    it('should include transaction count', () => {
      const top = getTopSuppliers(mockData, 3);
      expect(top[0].transactionCount).toBe(2); // Tech Solutions
      expect(top[1].transactionCount).toBe(2); // Acme Corp
    });
  });

  describe('getSpendByCategory', () => {
    it('should group spend by category', () => {
      const byCategory = getSpendByCategory(mockData);
      expect(byCategory).toHaveLength(2);
      
      const itEquipment = byCategory.find(c => c.category === 'IT Equipment');
      expect(itEquipment?.totalSpend).toBe(8000);
      expect(itEquipment?.percentage).toBeCloseTo(69.57, 1);
      
      const officeSupplies = byCategory.find(c => c.category === 'Office Supplies');
      expect(officeSupplies?.totalSpend).toBe(3500);
      expect(officeSupplies?.percentage).toBeCloseTo(30.43, 1);
    });

    it('should return empty array for empty data', () => {
      const byCategory = getSpendByCategory([]);
      expect(byCategory).toEqual([]);
    });

    it('should sort by spend descending', () => {
      const byCategory = getSpendByCategory(mockData);
      expect(byCategory[0].totalSpend).toBeGreaterThanOrEqual(byCategory[1].totalSpend);
    });
  });

  describe('getLargestTransaction', () => {
    it('should return the largest transaction', () => {
      const largest = getLargestTransaction(mockData);
      expect(largest).toBeDefined();
      expect(largest?.amount).toBe(5000);
      expect(largest?.supplier).toBe('Tech Solutions');
    });

    it('should return null for empty data', () => {
      const largest = getLargestTransaction([]);
      expect(largest).toBeNull();
    });
  });

  describe('getMostFrequentSupplier', () => {
    it('should return the most frequent supplier', () => {
      const frequent = getMostFrequentSupplier(mockData);
      expect(frequent).toBeDefined();
      // Both Acme Corp and Tech Solutions have 2 transactions
      expect(['Acme Corp', 'Tech Solutions']).toContain(frequent?.supplier);
      expect(frequent?.count).toBe(2);
    });

    it('should return null for empty data', () => {
      const frequent = getMostFrequentSupplier([]);
      expect(frequent).toBeNull();
    });
  });

  describe('getHighestSpendingCategory', () => {
    it('should return the highest spending category', () => {
      const highest = getHighestSpendingCategory(mockData);
      expect(highest).toBeDefined();
      expect(highest?.category).toBe('IT Equipment');
      expect(highest?.totalSpend).toBe(8000);
    });

    it('should return null for empty data', () => {
      const highest = getHighestSpendingCategory([]);
      expect(highest).toBeNull();
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero amounts', () => {
      const dataWithZero: ProcurementRecord[] = [
        { ...mockData[0], amount: 0 },
        { ...mockData[1], amount: 100 },
      ];
      const total = calculateTotalSpend(dataWithZero);
      expect(total).toBe(100);
    });

    it('should handle negative amounts', () => {
      const dataWithNegative: ProcurementRecord[] = [
        { ...mockData[0], amount: -500 }, // refund
        { ...mockData[1], amount: 1000 },
      ];
      const total = calculateTotalSpend(dataWithNegative);
      expect(total).toBe(500);
    });

    it('should handle very large numbers', () => {
      const dataWithLarge: ProcurementRecord[] = [
        { ...mockData[0], amount: 999999999 },
        { ...mockData[1], amount: 1 },
      ];
      const total = calculateTotalSpend(dataWithLarge);
      expect(total).toBe(1000000000);
    });
  });
});

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
