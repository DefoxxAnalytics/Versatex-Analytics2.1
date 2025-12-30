import { describe, it, expect } from 'vitest';
import { parseCSV, validateProcurementData } from '../csvParser';

describe('CSV Parser', () => {
  describe('parseCSV', () => {
    it('should parse a valid CSV file with procurement data', async () => {
      const csvContent = `Supplier,Category,Subcategory,Amount,Date,Location
Acme Corp,Office Supplies,Pens,1500.50,2024-01-15,HQ
Tech Solutions,IT Services,Cloud,5000.00,2024-01-20,Remote
Office Depot,Office Supplies,Paper,750.25,2024-01-22,Branch`;

      const file = new File([csvContent], 'test.csv', { type: 'text/csv' });
      const result = await parseCSV(file);

      expect(result).toHaveLength(3);
      expect(result[0].supplier).toBe('Acme Corp');
      expect(result[0].category).toBe('Office Supplies');
      expect(result[0].subcategory).toBe('Pens');
      expect(result[0].amount).toBe(1500.50);
      expect(result[0].date).toBe('2024-01-15');
      expect(result[0].location).toBe('HQ');
    });

    it('should handle empty CSV files', async () => {
      const csvContent = 'Supplier,Category,Subcategory,Amount,Date,Location';
      const file = new File([csvContent], 'empty.csv', { type: 'text/csv' });
      const result = await parseCSV(file);

      expect(result).toHaveLength(0);
    });

    it('should throw error for invalid CSV structure', async () => {
      const csvContent = 'Invalid,Data\nNo,Headers';
      const file = new File([csvContent], 'invalid.csv', { type: 'text/csv' });

      await expect(parseCSV(file)).rejects.toThrow('Missing required columns');
    });

    it('should convert amount strings to numbers', async () => {
      const csvContent = `Supplier,Category,Subcategory,Amount,Date,Location
Test Supplier,Test Category,General,2500.75,2024-01-01,Main`;

      const file = new File([csvContent], 'test.csv', { type: 'text/csv' });
      const result = await parseCSV(file);

      expect(typeof result[0].amount).toBe('number');
      expect(result[0].amount).toBe(2500.75);
    });
  });

  describe('validateProcurementData', () => {
    it('should validate correct procurement data', () => {
      const data = {
        supplier: 'Test Corp',
        category: 'Services',
        amount: 1000,
        date: '2024-01-01',
      };

      expect(() => validateProcurementData(data)).not.toThrow();
    });

    it('should throw error for missing supplier', () => {
      const data = {
        supplier: '',
        category: 'Services',
        amount: 1000,
        date: '2024-01-01',
      };

      expect(() => validateProcurementData(data)).toThrow('Supplier is required');
    });

    it('should throw error for invalid amount', () => {
      const data = {
        supplier: 'Test Corp',
        category: 'Services',
        amount: -100,
        date: '2024-01-01',
      };

      expect(() => validateProcurementData(data)).toThrow('Amount must be positive');
    });

    it('should throw error for invalid date format', () => {
      const data = {
        supplier: 'Test Corp',
        category: 'Services',
        amount: 1000,
        date: 'invalid-date',
      };

      expect(() => validateProcurementData(data)).toThrow('Invalid date format');
    });
  });
});
