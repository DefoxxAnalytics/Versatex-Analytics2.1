/**
 * MSW handlers for API mocking in tests
 */
import { http, HttpResponse } from 'msw';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

// Mock user data
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  profile: {
    id: 1,
    organization: {
      id: 1,
      name: 'Test Organization',
      slug: 'test-org',
    },
    role: 'admin',
    is_active: true,
  },
};

// Mock suppliers
const mockSuppliers = [
  {
    id: 1,
    name: 'Supplier A',
    code: 'SUP-A',
    contact_email: 'a@supplier.com',
    is_active: true,
    transaction_count: 10,
    total_spend: '50000.00',
  },
  {
    id: 2,
    name: 'Supplier B',
    code: 'SUP-B',
    contact_email: 'b@supplier.com',
    is_active: true,
    transaction_count: 5,
    total_spend: '25000.00',
  },
];

// Mock categories
const mockCategories = [
  {
    id: 1,
    name: 'Office Supplies',
    description: 'Office supplies and stationery',
    is_active: true,
    transaction_count: 8,
    total_spend: '15000.00',
  },
  {
    id: 2,
    name: 'IT Equipment',
    description: 'Computers and IT equipment',
    is_active: true,
    transaction_count: 6,
    total_spend: '45000.00',
  },
];

// Mock transactions
const mockTransactions = [
  {
    id: 1,
    supplier: 1,
    supplier_name: 'Supplier A',
    category: 1,
    category_name: 'Office Supplies',
    amount: '1500.00',
    date: '2024-01-15',
    description: 'Monthly supplies',
    invoice_number: 'INV-001',
  },
  {
    id: 2,
    supplier: 2,
    supplier_name: 'Supplier B',
    category: 2,
    category_name: 'IT Equipment',
    amount: '25000.00',
    date: '2024-01-20',
    description: 'New laptops',
    invoice_number: 'INV-002',
  },
];

// Mock analytics overview
const mockOverviewStats = {
  total_spend: 75000.0,
  transaction_count: 15,
  supplier_count: 2,
  category_count: 2,
  avg_transaction: 5000.0,
};

// Mock spend by category
const mockSpendByCategory = [
  { category: 'IT Equipment', amount: 45000.0, count: 6 },
  { category: 'Office Supplies', amount: 15000.0, count: 8 },
];

// Mock monthly trend
const mockMonthlyTrend = [
  { month: '2024-01', amount: 25000.0, count: 5 },
  { month: '2024-02', amount: 30000.0, count: 6 },
  { month: '2024-03', amount: 20000.0, count: 4 },
];

export const handlers = [
  // Authentication handlers
  http.post(`${API_URL}/v1/auth/login/`, async ({ request }) => {
    const body = (await request.json()) as { username?: string; password?: string };
    if (body.username === 'testuser' && body.password === 'TestPass123!') {
      return HttpResponse.json(
        {
          user: mockUser,
          message: 'Login successful',
        },
        {
          headers: {
            'Set-Cookie': 'access_token=mock-access-token; HttpOnly; Path=/',
          },
        }
      );
    }
    return HttpResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  http.post(`${API_URL}/v1/auth/logout/`, () => {
    return HttpResponse.json({ message: 'Logout successful' });
  }),

  http.post(`${API_URL}/v1/auth/register/`, async ({ request }) => {
    const body = (await request.json()) as { username?: string };
    return HttpResponse.json(
      {
        user: { ...mockUser, username: body.username || 'newuser' },
        message: 'User registered successfully',
      },
      { status: 201 }
    );
  }),

  http.get(`${API_URL}/v1/auth/user/`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/v1/auth/token/refresh/`, () => {
    return HttpResponse.json({ message: 'Token refreshed successfully' });
  }),

  // Procurement handlers
  http.get(`${API_URL}/v1/procurement/suppliers/`, () => {
    return HttpResponse.json(mockSuppliers);
  }),

  http.post(`${API_URL}/v1/procurement/suppliers/`, async ({ request }) => {
    const body = (await request.json()) as { name?: string };
    return HttpResponse.json(
      { id: 3, ...body, is_active: true },
      { status: 201 }
    );
  }),

  http.get(`${API_URL}/v1/procurement/suppliers/:id/`, ({ params }) => {
    const supplier = mockSuppliers.find((s) => s.id === Number(params.id));
    if (supplier) {
      return HttpResponse.json(supplier);
    }
    return HttpResponse.json({ error: 'Not found' }, { status: 404 });
  }),

  http.get(`${API_URL}/v1/procurement/categories/`, () => {
    return HttpResponse.json(mockCategories);
  }),

  http.post(`${API_URL}/v1/procurement/categories/`, async ({ request }) => {
    const body = (await request.json()) as { name?: string };
    return HttpResponse.json(
      { id: 3, ...body, is_active: true },
      { status: 201 }
    );
  }),

  http.get(`${API_URL}/v1/procurement/transactions/`, () => {
    return HttpResponse.json(mockTransactions);
  }),

  http.post(`${API_URL}/v1/procurement/transactions/`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),

  http.post(`${API_URL}/v1/procurement/transactions/upload_csv/`, () => {
    return HttpResponse.json(
      {
        id: 1,
        file_name: 'upload.csv',
        batch_id: 'batch-001',
        total_rows: 100,
        successful_rows: 98,
        failed_rows: 2,
        duplicate_rows: 0,
        status: 'completed',
      },
      { status: 201 }
    );
  }),

  http.post(`${API_URL}/v1/procurement/transactions/bulk_delete/`, async ({ request }) => {
    const body = (await request.json()) as { ids?: number[] };
    const ids = body.ids || [];
    return HttpResponse.json({
      message: `${ids.length} transactions deleted successfully`,
      count: ids.length,
    });
  }),

  http.get(`${API_URL}/v1/procurement/transactions/export/`, () => {
    return new HttpResponse('supplier,category,amount,date\nTest,Test,1000,2024-01-01', {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="transactions.csv"',
      },
    });
  }),

  http.get(`${API_URL}/v1/procurement/uploads/`, () => {
    return HttpResponse.json([
      {
        id: 1,
        file_name: 'data.csv',
        batch_id: 'batch-001',
        total_rows: 100,
        successful_rows: 100,
        status: 'completed',
        created_at: '2024-01-15T10:00:00Z',
      },
    ]);
  }),

  // Analytics handlers
  http.get(`${API_URL}/v1/analytics/overview/`, () => {
    return HttpResponse.json(mockOverviewStats);
  }),

  http.get(`${API_URL}/v1/analytics/spend-by-category/`, () => {
    return HttpResponse.json(mockSpendByCategory);
  }),

  http.get(`${API_URL}/v1/analytics/spend-by-supplier/`, () => {
    return HttpResponse.json([
      { supplier: 'Supplier A', amount: 50000.0, count: 10 },
      { supplier: 'Supplier B', amount: 25000.0, count: 5 },
    ]);
  }),

  http.get(`${API_URL}/v1/analytics/monthly-trend/`, () => {
    return HttpResponse.json(mockMonthlyTrend);
  }),

  http.get(`${API_URL}/v1/analytics/pareto/`, () => {
    return HttpResponse.json([
      { supplier: 'Supplier A', amount: 50000.0, cumulative_percentage: 66.67 },
      { supplier: 'Supplier B', amount: 25000.0, cumulative_percentage: 100.0 },
    ]);
  }),

  http.get(`${API_URL}/v1/analytics/tail-spend/`, () => {
    return HttpResponse.json({
      tail_suppliers: [{ supplier: 'Supplier B', amount: 25000.0, transaction_count: 5 }],
      tail_count: 1,
      tail_spend: 25000.0,
      tail_percentage: 33.33,
    });
  }),

  http.get(`${API_URL}/v1/analytics/stratification/`, () => {
    return HttpResponse.json({
      strategic: [{ category: 'IT Equipment', spend: 45000.0, supplier_count: 1 }],
      leverage: [],
      bottleneck: [],
      tactical: [{ category: 'Office Supplies', spend: 15000.0, supplier_count: 2 }],
    });
  }),

  http.get(`${API_URL}/v1/analytics/seasonality/`, () => {
    return HttpResponse.json([
      { month: 'Jan', average_spend: 25000.0, occurrences: 1 },
      { month: 'Feb', average_spend: 30000.0, occurrences: 1 },
      { month: 'Mar', average_spend: 20000.0, occurrences: 1 },
      { month: 'Apr', average_spend: 0, occurrences: 0 },
      { month: 'May', average_spend: 0, occurrences: 0 },
      { month: 'Jun', average_spend: 0, occurrences: 0 },
      { month: 'Jul', average_spend: 0, occurrences: 0 },
      { month: 'Aug', average_spend: 0, occurrences: 0 },
      { month: 'Sep', average_spend: 0, occurrences: 0 },
      { month: 'Oct', average_spend: 0, occurrences: 0 },
      { month: 'Nov', average_spend: 0, occurrences: 0 },
      { month: 'Dec', average_spend: 0, occurrences: 0 },
    ]);
  }),

  http.get(`${API_URL}/v1/analytics/yoy/`, () => {
    return HttpResponse.json([
      { year: 2023, total_spend: 500000.0, transaction_count: 100, avg_transaction: 5000.0 },
      {
        year: 2024,
        total_spend: 75000.0,
        transaction_count: 15,
        avg_transaction: 5000.0,
        growth_percentage: -85.0,
      },
    ]);
  }),

  http.get(`${API_URL}/v1/analytics/consolidation/`, () => {
    return HttpResponse.json([
      {
        category: 'Office Supplies',
        supplier_count: 3,
        total_spend: 15000.0,
        suppliers: [
          { name: 'Supplier A', spend: 8000.0 },
          { name: 'Supplier B', spend: 5000.0 },
          { name: 'Supplier C', spend: 2000.0 },
        ],
        potential_savings: 1500.0,
      },
    ]);
  }),

  // Legacy API endpoints (backwards compatibility)
  http.post(`${API_URL}/auth/login/`, async ({ request }) => {
    const body = (await request.json()) as { username?: string; password?: string };
    if (body.username === 'testuser' && body.password === 'TestPass123!') {
      return HttpResponse.json({ user: mockUser, message: 'Login successful' });
    }
    return HttpResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  }),

  http.get(`${API_URL}/auth/user/`, () => {
    return HttpResponse.json(mockUser);
  }),
];
