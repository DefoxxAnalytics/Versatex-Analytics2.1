import { describe, it, expect } from 'vitest';
import { parseExcel } from '../excelParser';
import * as XLSX from 'xlsx';

describe('Excel Parser', () => {
  describe('parseExcel', () => {
    it('should parse a valid Excel file with procurement data', async () => {
      // Create a mock Excel file
      const worksheet = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category', 'Subcategory', 'Amount', 'Date', 'Location'],
        ['Acme Corp', 'Office Supplies', 'Pens', 1500.50, '2024-01-15', 'HQ'],
        ['Tech Solutions', 'IT Services', 'Cloud', 5000.00, '2024-01-20', 'Remote'],
        ['Office Depot', 'Office Supplies', 'Paper', 750.25, '2024-01-22', 'Branch'],
      ]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');

      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      const file = new File([excelBuffer], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const result = await parseExcel(file);

      expect(result).toHaveLength(3);
      expect(result[0].supplier).toBe('Acme Corp');
      expect(result[0].category).toBe('Office Supplies');
      expect(result[0].subcategory).toBe('Pens');
      expect(result[0].amount).toBe(1500.50);
      expect(result[0].date).toBe('2024-01-15');
      expect(result[0].location).toBe('HQ');
    });

    it('should handle empty Excel files', async () => {
      const worksheet = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category', 'Subcategory', 'Amount', 'Date', 'Location'],
      ]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');

      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      const file = new File([excelBuffer], 'empty.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const result = await parseExcel(file);

      expect(result).toHaveLength(0);
    });

    it('should throw error for missing required columns', async () => {
      const worksheet = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category'], // Missing Subcategory, Amount, Date, Location
        ['Test Corp', 'Services'],
      ]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');

      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      const file = new File([excelBuffer], 'invalid.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      await expect(parseExcel(file)).rejects.toThrow('Missing required columns');
    });

    it('should handle numeric dates from Excel', async () => {
      // Excel stores dates as numbers (days since 1900-01-01)
      const worksheet = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category', 'Subcategory', 'Amount', 'Date', 'Location'],
        ['Test Corp', 'Services', 'General', 1000, 45292, 'Main'], // Excel date number for 2024-01-01
      ]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');

      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      const file = new File([excelBuffer], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const result = await parseExcel(file);

      expect(result).toHaveLength(1);
      expect(result[0].date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });

    it('should read from the first sheet by default', async () => {
      const worksheet1 = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category', 'Subcategory', 'Amount', 'Date', 'Location'],
        ['First Sheet Corp', 'Services', 'General', 1000, '2024-01-01', 'Main'],
      ]);

      const worksheet2 = XLSX.utils.aoa_to_sheet([
        ['Supplier', 'Category', 'Subcategory', 'Amount', 'Date', 'Location'],
        ['Second Sheet Corp', 'Products', 'General', 2000, '2024-01-02', 'Branch'],
      ]);

      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet1, 'Sheet1');
      XLSX.utils.book_append_sheet(workbook, worksheet2, 'Sheet2');

      const excelBuffer = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      const file = new File([excelBuffer], 'test.xlsx', {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const result = await parseExcel(file);

      expect(result).toHaveLength(1);
      expect(result[0].supplier).toBe('First Sheet Corp');
    });
  });
});
