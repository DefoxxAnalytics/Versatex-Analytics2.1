/**
 * Custom hooks for P2P (Procure-to-Pay) Analytics data from Django API
 *
 * All hooks include organization_id in query keys to properly
 * invalidate cache when switching organizations (superuser feature).
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { p2pAnalyticsAPI, getOrganizationParam, ExceptionType } from '@/lib/api';

/**
 * Get the current organization ID for query key inclusion.
 * Returns undefined if viewing own org (default behavior).
 */
function getOrgKeyPart(): number | undefined {
  const param = getOrganizationParam();
  return param.organization_id;
}

// =============================================================================
// P2P Cycle Time Analysis Hooks
// =============================================================================

/**
 * Get P2P cycle overview with stage-by-stage metrics
 */
export function useP2PCycleOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-cycle-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getCycleOverview();
      return response.data;
    },
  });
}

/**
 * Get P2P cycle times by category
 */
export function useP2PCycleByCategory() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-cycle-by-category', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getCycleByCategory();
      return response.data;
    },
  });
}

/**
 * Get P2P cycle times by supplier
 */
export function useP2PCycleBySupplier() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-cycle-by-supplier', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getCycleBySupplier();
      return response.data;
    },
  });
}

/**
 * Get P2P cycle time trends over months
 */
export function useP2PCycleTrends(months: number = 12) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-cycle-trends', months, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getCycleTrends(months);
      return response.data;
    },
  });
}

/**
 * Get P2P bottleneck analysis
 */
export function useP2PBottlenecks() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-bottlenecks', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getBottlenecks();
      return response.data;
    },
  });
}

/**
 * Get P2P process funnel visualization data
 */
export function useP2PProcessFunnel(months: number = 12) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-process-funnel', months, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getProcessFunnel(months);
      return response.data;
    },
  });
}

/**
 * Get stage drilldown - top slowest items in a specific stage
 */
export function useP2PStageDrilldown(stage: string | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['p2p-stage-drilldown', stage, { orgId }],
    queryFn: async () => {
      if (!stage) return null;
      const response = await p2pAnalyticsAPI.getStageDrilldown(stage);
      return response.data;
    },
    enabled: !!stage,
  });
}

// =============================================================================
// 3-Way Matching Hooks
// =============================================================================

/**
 * Get 3-way matching overview metrics
 */
export function useMatchingOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['matching-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getMatchingOverview();
      return response.data;
    },
  });
}

/**
 * Get matching exceptions list with filtering
 */
export function useMatchingExceptions(params?: {
  status?: 'open' | 'resolved' | 'all';
  exception_type?: ExceptionType;
  limit?: number;
}) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['matching-exceptions', params, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getMatchingExceptions(params);
      return response.data;
    },
  });
}

/**
 * Get exceptions breakdown by type
 */
export function useExceptionsByType() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['exceptions-by-type', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getExceptionsByType();
      return response.data;
    },
  });
}

/**
 * Get exceptions breakdown by supplier
 */
export function useExceptionsBySupplier() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['exceptions-by-supplier', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getExceptionsBySupplier();
      return response.data;
    },
  });
}

/**
 * Get price variance analysis
 */
export function usePriceVarianceAnalysis() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['price-variance-analysis', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPriceVarianceAnalysis();
      return response.data;
    },
  });
}

/**
 * Get quantity variance analysis
 */
export function useQuantityVarianceAnalysis() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['quantity-variance-analysis', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getQuantityVarianceAnalysis();
      return response.data;
    },
  });
}

/**
 * Get invoice match detail for a specific invoice
 */
export function useInvoiceMatchDetail(invoiceId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['invoice-match-detail', invoiceId, { orgId }],
    queryFn: async () => {
      if (!invoiceId) return null;
      const response = await p2pAnalyticsAPI.getInvoiceMatchDetail(invoiceId);
      return response.data;
    },
    enabled: !!invoiceId,
  });
}

/**
 * Resolve a single invoice exception
 */
export function useResolveException() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async ({ invoiceId, resolutionNotes }: { invoiceId: number; resolutionNotes: string }) => {
      const response = await p2pAnalyticsAPI.resolveException(invoiceId, resolutionNotes);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate matching-related queries
      queryClient.invalidateQueries({ queryKey: ['matching-overview', { orgId }] });
      queryClient.invalidateQueries({ queryKey: ['matching-exceptions'] });
      queryClient.invalidateQueries({ queryKey: ['exceptions-by-type', { orgId }] });
      queryClient.invalidateQueries({ queryKey: ['exceptions-by-supplier', { orgId }] });
    },
  });
}

/**
 * Bulk resolve multiple invoice exceptions
 */
export function useBulkResolveExceptions() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async ({ invoiceIds, resolutionNotes }: { invoiceIds: number[]; resolutionNotes: string }) => {
      const response = await p2pAnalyticsAPI.bulkResolveExceptions(invoiceIds, resolutionNotes);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate matching-related queries
      queryClient.invalidateQueries({ queryKey: ['matching-overview', { orgId }] });
      queryClient.invalidateQueries({ queryKey: ['matching-exceptions'] });
      queryClient.invalidateQueries({ queryKey: ['exceptions-by-type', { orgId }] });
      queryClient.invalidateQueries({ queryKey: ['exceptions-by-supplier', { orgId }] });
    },
  });
}

// =============================================================================
// Invoice Aging / AP Analysis Hooks
// =============================================================================

/**
 * Get aging overview with bucket totals
 */
export function useAgingOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['aging-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getAgingOverview();
      return response.data;
    },
  });
}

/**
 * Get aging breakdown by supplier
 */
export function useAgingBySupplier() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['aging-by-supplier', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getAgingBySupplier();
      return response.data;
    },
  });
}

/**
 * Get payment terms compliance analysis
 */
export function usePaymentTermsCompliance() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['payment-terms-compliance', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPaymentTermsCompliance();
      return response.data;
    },
  });
}

/**
 * Get DPO trends over time
 */
export function useDPOTrends(months: number = 12) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['dpo-trends', months, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getDPOTrends(months);
      return response.data;
    },
  });
}

/**
 * Get cash flow forecast
 */
export function useCashFlowForecast(weeks: number = 4) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['cash-flow-forecast', weeks, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getCashFlowForecast(weeks);
      return response.data;
    },
  });
}

// =============================================================================
// Purchase Requisition Hooks
// =============================================================================

/**
 * Get PR overview metrics
 */
export function usePROverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['pr-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPROverview();
      return response.data;
    },
  });
}

/**
 * Get PR approval analysis
 */
export function usePRApprovalAnalysis() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['pr-approval-analysis', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPRApprovalAnalysis();
      return response.data;
    },
  });
}

/**
 * Get PRs by department
 */
export function usePRByDepartment() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['pr-by-department', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPRByDepartment();
      return response.data;
    },
  });
}

/**
 * Get pending PR approvals
 */
export function usePRPending(limit: number = 50) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['pr-pending', limit, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPRPending(limit);
      return response.data;
    },
  });
}

/**
 * Get PR detail
 */
export function usePRDetail(prId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['pr-detail', prId, { orgId }],
    queryFn: async () => {
      if (!prId) return null;
      const response = await p2pAnalyticsAPI.getPRDetail(prId);
      return response.data;
    },
    enabled: !!prId,
  });
}

// =============================================================================
// Purchase Order Hooks
// =============================================================================

/**
 * Get PO overview metrics
 */
export function usePOOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['po-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPOOverview();
      return response.data;
    },
  });
}

/**
 * Get PO leakage (maverick spend) analysis
 */
export function usePOLeakage() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['po-leakage', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPOLeakage();
      return response.data;
    },
  });
}

/**
 * Get PO amendment analysis
 */
export function usePOAmendments() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['po-amendments', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPOAmendments();
      return response.data;
    },
  });
}

/**
 * Get POs by supplier
 */
export function usePOBySupplier() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['po-by-supplier', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getPOBySupplier();
      return response.data;
    },
  });
}

/**
 * Get PO detail
 */
export function usePODetail(poId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['po-detail', poId, { orgId }],
    queryFn: async () => {
      if (!poId) return null;
      const response = await p2pAnalyticsAPI.getPODetail(poId);
      return response.data;
    },
    enabled: !!poId,
  });
}

// =============================================================================
// Supplier Payment Performance Hooks
// =============================================================================

/**
 * Get supplier payments overview
 */
export function useSupplierPaymentsOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['supplier-payments-overview', { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getSupplierPaymentsOverview();
      return response.data;
    },
  });
}

/**
 * Get supplier payments scorecard
 */
export function useSupplierPaymentsScorecard(limit: number = 50) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['supplier-payments-scorecard', limit, { orgId }],
    queryFn: async () => {
      const response = await p2pAnalyticsAPI.getSupplierPaymentsScorecard(limit);
      return response.data;
    },
  });
}

/**
 * Get supplier payment detail
 */
export function useSupplierPaymentDetail(supplierId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['supplier-payment-detail', supplierId, { orgId }],
    queryFn: async () => {
      if (!supplierId) return null;
      const response = await p2pAnalyticsAPI.getSupplierPaymentDetail(supplierId);
      return response.data;
    },
    enabled: !!supplierId,
  });
}

/**
 * Get supplier payment history
 */
export function useSupplierPaymentHistory(supplierId: number | null, months: number = 12) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['supplier-payment-history', supplierId, months, { orgId }],
    queryFn: async () => {
      if (!supplierId) return null;
      const response = await p2pAnalyticsAPI.getSupplierPaymentHistory(supplierId, months);
      return response.data;
    },
    enabled: !!supplierId,
  });
}
