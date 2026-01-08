/**
 * Centralized query key factory for React Query.
 *
 * This module provides a single source of truth for all query keys used with
 * TanStack Query. Using a factory pattern ensures:
 * - Consistent key structure across the application
 * - Type-safe query key generation
 * - Easy cache invalidation by key prefix
 * - Organization-scoped keys for multi-tenant support
 *
 * Convention:
 * - All keys are readonly arrays
 * - Organization-scoped keys include orgId as the last element in an object
 * - Use factory functions for parameterized keys
 *
 * Usage:
 *   import { queryKeys } from '@/lib/queryKeys';
 *
 *   // In a hook:
 *   useQuery({
 *     queryKey: queryKeys.analytics.overview(orgId),
 *     queryFn: () => analyticsAPI.getOverview(),
 *   });
 *
 *   // Invalidate all analytics queries:
 *   queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });
 *
 * @module queryKeys
 */

export const queryKeys = {
  // =========================================================================
  // Procurement
  // =========================================================================
  procurement: {
    all: ['procurement'] as const,
    data: (orgId?: number) => ['procurement', 'data', { orgId }] as const,
    filtered: (orgId?: number) => ['procurement', 'filtered', { orgId }] as const,
    suppliers: {
      all: ['procurement', 'suppliers'] as const,
      list: (params?: Record<string, unknown>, orgId?: number) =>
        ['procurement', 'suppliers', 'list', params, { orgId }] as const,
      detail: (supplierId: number, orgId?: number) =>
        ['procurement', 'suppliers', 'detail', supplierId, { orgId }] as const,
    },
    categories: {
      all: ['procurement', 'categories'] as const,
      list: (params?: Record<string, unknown>, orgId?: number) =>
        ['procurement', 'categories', 'list', params, { orgId }] as const,
      detail: (categoryId: number, orgId?: number) =>
        ['procurement', 'categories', 'detail', categoryId, { orgId }] as const,
    },
    transactions: {
      all: ['procurement', 'transactions'] as const,
      list: (params?: Record<string, unknown>, orgId?: number) =>
        ['procurement', 'transactions', 'list', params, { orgId }] as const,
      detail: (transactionId: number, orgId?: number) =>
        ['procurement', 'transactions', 'detail', transactionId, { orgId }] as const,
    },
    uploads: {
      all: ['procurement', 'uploads'] as const,
      list: (orgId?: number) => ['procurement', 'uploads', 'list', { orgId }] as const,
      detail: (uploadId: number, orgId?: number) =>
        ['procurement', 'uploads', 'detail', uploadId, { orgId }] as const,
    },
  },

  // =========================================================================
  // Analytics - Core
  // =========================================================================
  analytics: {
    all: ['analytics'] as const,
    overview: (orgId?: number) => ['analytics', 'overview', { orgId }] as const,
    spendByCategory: (orgId?: number) => ['analytics', 'spend-by-category', { orgId }] as const,
    spendBySupplier: (orgId?: number) => ['analytics', 'spend-by-supplier', { orgId }] as const,
    monthlyTrend: (months: number, orgId?: number) =>
      ['analytics', 'monthly-trend', months, { orgId }] as const,

    // Pareto Analysis
    pareto: (orgId?: number) => ['analytics', 'pareto', { orgId }] as const,
    paretoDetailed: (orgId?: number) => ['analytics', 'pareto-detailed', { orgId }] as const,
    paretoDrilldown: (supplierId: number, orgId?: number) =>
      ['analytics', 'pareto-drilldown', supplierId, { orgId }] as const,

    // Drilldowns
    supplierDrilldown: (supplierId: number, orgId?: number) =>
      ['analytics', 'supplier-drilldown', supplierId, { orgId }] as const,
    categoryDrilldown: (categoryId: number, orgId?: number) =>
      ['analytics', 'category-drilldown', categoryId, { orgId }] as const,

    // Stratification
    stratification: (orgId?: number) => ['analytics', 'stratification', { orgId }] as const,
    stratificationDetailed: (orgId?: number) =>
      ['analytics', 'stratification-detailed', { orgId }] as const,
    stratificationSegment: (segment: string, orgId?: number) =>
      ['analytics', 'stratification-segment', segment, { orgId }] as const,
    stratificationBand: (band: string, orgId?: number) =>
      ['analytics', 'stratification-band', band, { orgId }] as const,

    // Seasonality
    seasonality: (useFiscalYear: boolean, orgId?: number) =>
      ['analytics', 'seasonality', useFiscalYear, { orgId }] as const,
    seasonalityDetailed: (useFiscalYear: boolean, orgId?: number) =>
      ['analytics', 'seasonality-detailed', useFiscalYear, { orgId }] as const,
    seasonalityCategoryDrilldown: (
      categoryId: number,
      useFiscalYear: boolean,
      orgId?: number
    ) => ['analytics', 'seasonality-category', categoryId, useFiscalYear, { orgId }] as const,

    // Year over Year
    yearOverYear: (useFiscalYear: boolean, year1: number, year2: number, orgId?: number) =>
      ['analytics', 'yoy', useFiscalYear, year1, year2, { orgId }] as const,
    yoyDetailed: (useFiscalYear: boolean, year1: number, year2: number, orgId?: number) =>
      ['analytics', 'yoy-detailed', useFiscalYear, year1, year2, { orgId }] as const,
    yoyCategoryDrilldown: (
      categoryId: number,
      useFiscalYear: boolean,
      year1: number,
      year2: number,
      orgId?: number
    ) =>
      ['analytics', 'yoy-category', categoryId, useFiscalYear, year1, year2, { orgId }] as const,
    yoySupplierDrilldown: (
      supplierId: number,
      useFiscalYear: boolean,
      year1: number,
      year2: number,
      orgId?: number
    ) =>
      ['analytics', 'yoy-supplier', supplierId, useFiscalYear, year1, year2, { orgId }] as const,

    // Tail Spend
    tailSpend: (threshold: number, orgId?: number) =>
      ['analytics', 'tail-spend', threshold, { orgId }] as const,
    tailSpendDetailed: (threshold: number, orgId?: number) =>
      ['analytics', 'tail-spend-detailed', threshold, { orgId }] as const,
    tailSpendCategoryDrilldown: (categoryId: number, threshold: number, orgId?: number) =>
      ['analytics', 'tail-spend-category', categoryId, threshold, { orgId }] as const,
    tailSpendVendorDrilldown: (vendorId: number, threshold: number, orgId?: number) =>
      ['analytics', 'tail-spend-vendor', vendorId, threshold, { orgId }] as const,

    // Consolidation
    consolidation: (orgId?: number) => ['analytics', 'consolidation', { orgId }] as const,
  },

  // =========================================================================
  // P2P Analytics
  // =========================================================================
  p2p: {
    all: ['p2p'] as const,

    // Cycle Time
    cycleOverview: (orgId?: number) => ['p2p', 'cycle-overview', { orgId }] as const,
    cycleByCategory: (orgId?: number) => ['p2p', 'cycle-by-category', { orgId }] as const,
    cycleBySupplier: (orgId?: number) => ['p2p', 'cycle-by-supplier', { orgId }] as const,
    cycleTrends: (months: number, orgId?: number) =>
      ['p2p', 'cycle-trends', months, { orgId }] as const,
    bottlenecks: (orgId?: number) => ['p2p', 'bottlenecks', { orgId }] as const,
    processFunnel: (orgId?: number) => ['p2p', 'process-funnel', { orgId }] as const,
    stageDrilldown: (stage: string, orgId?: number) =>
      ['p2p', 'stage-drilldown', stage, { orgId }] as const,

    // Matching
    matchingOverview: (orgId?: number) => ['p2p', 'matching-overview', { orgId }] as const,
    matchingExceptions: (orgId?: number) => ['p2p', 'matching-exceptions', { orgId }] as const,
    exceptionsByType: (orgId?: number) => ['p2p', 'exceptions-by-type', { orgId }] as const,
    exceptionsBySupplier: (orgId?: number) =>
      ['p2p', 'exceptions-by-supplier', { orgId }] as const,
    priceVariance: (orgId?: number) => ['p2p', 'price-variance', { orgId }] as const,
    quantityVariance: (orgId?: number) => ['p2p', 'quantity-variance', { orgId }] as const,
    invoiceMatchDetail: (invoiceId: number, orgId?: number) =>
      ['p2p', 'invoice-match', invoiceId, { orgId }] as const,

    // Aging
    agingOverview: (orgId?: number) => ['p2p', 'aging-overview', { orgId }] as const,
    agingBySupplier: (orgId?: number) => ['p2p', 'aging-by-supplier', { orgId }] as const,
    paymentTermsCompliance: (orgId?: number) =>
      ['p2p', 'payment-terms-compliance', { orgId }] as const,
    dpoTrends: (months: number, orgId?: number) =>
      ['p2p', 'dpo-trends', months, { orgId }] as const,
    cashForecast: (weeks: number, orgId?: number) =>
      ['p2p', 'cash-forecast', weeks, { orgId }] as const,

    // Requisitions
    prOverview: (orgId?: number) => ['p2p', 'pr-overview', { orgId }] as const,
    prApprovalAnalysis: (orgId?: number) => ['p2p', 'pr-approval-analysis', { orgId }] as const,
    prByDepartment: (orgId?: number) => ['p2p', 'pr-by-department', { orgId }] as const,
    prPending: (orgId?: number) => ['p2p', 'pr-pending', { orgId }] as const,
    prDetail: (prId: number, orgId?: number) => ['p2p', 'pr-detail', prId, { orgId }] as const,

    // Purchase Orders
    poOverview: (orgId?: number) => ['p2p', 'po-overview', { orgId }] as const,
    poLeakage: (orgId?: number) => ['p2p', 'po-leakage', { orgId }] as const,
    poAmendments: (orgId?: number) => ['p2p', 'po-amendments', { orgId }] as const,
    poBySupplier: (orgId?: number) => ['p2p', 'po-by-supplier', { orgId }] as const,
    poDetail: (poId: number, orgId?: number) => ['p2p', 'po-detail', poId, { orgId }] as const,

    // Supplier Payments
    supplierPaymentsOverview: (orgId?: number) =>
      ['p2p', 'supplier-payments-overview', { orgId }] as const,
    supplierPaymentsScorecard: (orgId?: number) =>
      ['p2p', 'supplier-payments-scorecard', { orgId }] as const,
    supplierPaymentDetail: (supplierId: number, orgId?: number) =>
      ['p2p', 'supplier-payment-detail', supplierId, { orgId }] as const,
    supplierPaymentHistory: (supplierId: number, orgId?: number) =>
      ['p2p', 'supplier-payment-history', supplierId, { orgId }] as const,
  },

  // =========================================================================
  // Reports
  // =========================================================================
  reports: {
    all: ['reports'] as const,
    templates: (orgId?: number) => ['reports', 'templates', { orgId }] as const,
    history: (params?: Record<string, unknown>, orgId?: number) =>
      ['reports', 'history', params, { orgId }] as const,
    detail: (reportId: string, orgId?: number) =>
      ['reports', 'detail', reportId, { orgId }] as const,
    status: (reportId: string, orgId?: number) =>
      ['reports', 'status', reportId, { orgId }] as const,
    schedules: (orgId?: number) => ['reports', 'schedules', { orgId }] as const,
    scheduleDetail: (scheduleId: string, orgId?: number) =>
      ['reports', 'schedule-detail', scheduleId, { orgId }] as const,
  },

  // =========================================================================
  // Contracts
  // =========================================================================
  contracts: {
    all: ['contracts'] as const,
    overview: (orgId?: number) => ['contracts', 'overview', { orgId }] as const,
    list: (orgId?: number) => ['contracts', 'list', { orgId }] as const,
    detail: (contractId: number, orgId?: number) =>
      ['contracts', 'detail', contractId, { orgId }] as const,
  },

  // =========================================================================
  // Compliance
  // =========================================================================
  compliance: {
    all: ['compliance'] as const,
    overview: (orgId?: number) => ['compliance', 'overview', { orgId }] as const,
    violations: (params?: Record<string, unknown>, orgId?: number) =>
      ['compliance', 'violations', params, { orgId }] as const,
    maverick: (orgId?: number) => ['compliance', 'maverick', { orgId }] as const,
  },

  // =========================================================================
  // AI & Predictive Analytics
  // =========================================================================
  ai: {
    all: ['ai'] as const,
    insights: (params?: Record<string, unknown>, orgId?: number) =>
      ['ai', 'insights', params, { orgId }] as const,
    predictions: (months: number, orgId?: number) =>
      ['ai', 'predictions', months, { orgId }] as const,
    anomalies: (orgId?: number) => ['ai', 'anomalies', { orgId }] as const,
  },

  // =========================================================================
  // Settings (not org-scoped)
  // =========================================================================
  settings: {
    all: ['settings'] as const,
    user: () => ['settings', 'user'] as const,
    preferences: () => ['settings', 'preferences'] as const,
  },

  // =========================================================================
  // Auth (not org-scoped)
  // =========================================================================
  auth: {
    all: ['auth'] as const,
    user: () => ['auth', 'user'] as const,
    organizations: () => ['auth', 'organizations'] as const,
  },
} as const;

// Type exports for consumers
export type QueryKeys = typeof queryKeys;
export type AnalyticsQueryKeys = typeof queryKeys.analytics;
export type P2PQueryKeys = typeof queryKeys.p2p;
export type ReportsQueryKeys = typeof queryKeys.reports;
