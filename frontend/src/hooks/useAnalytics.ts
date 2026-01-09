/**
 * Custom hooks for analytics data from Django API
 *
 * All hooks include organization_id in query keys to properly
 * invalidate cache when switching organizations (superuser feature).
 */
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI, procurementAPI, getOrganizationParam } from "@/lib/api";
import { queryKeys } from "@/lib/queryKeys";

/**
 * Get the current organization ID for query key inclusion.
 * Returns undefined if viewing own org (default behavior).
 */
function getOrgKeyPart(): number | undefined {
  const param = getOrganizationParam();
  return param.organization_id;
}

/**
 * Get overview statistics (total spend, supplier count, category count, etc.)
 */
export function useOverviewStats() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.overview(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getOverview();
      return response.data;
    },
  });
}

/**
 * Get spend by category
 */
export function useSpendByCategory() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.spendByCategory(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getSpendByCategory();
      return response.data;
    },
  });
}

/**
 * Get detailed category analysis (includes subcategories, suppliers, risk levels)
 * Use this for the Categories dashboard page
 */
export function useCategoryDetails() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.categoryDetails(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getCategoryDetails();
      return response.data;
    },
  });
}

/**
 * Get spend by supplier
 */
export function useSpendBySupplier() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.spendBySupplier(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getSpendBySupplier();
      return response.data;
    },
  });
}

/**
 * Get detailed supplier analysis (includes HHI score, concentration metrics, category diversity)
 * Use this for the Suppliers dashboard page
 */
export function useSupplierDetails() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.supplierDetails(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getSupplierDetails();
      return response.data;
    },
  });
}

/**
 * Get monthly trend
 */
export function useMonthlyTrend(months: number = 12) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.monthlyTrend(months, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getMonthlyTrend(months);
      return response.data;
    },
  });
}

/**
 * Get Pareto analysis
 */
export function useParetoAnalysis() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.pareto(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getParetoAnalysis();
      return response.data;
    },
  });
}

/**
 * Get supplier drill-down data for Pareto Analysis modal
 * Fetches on-demand when a supplier is selected
 */
export function useSupplierDrilldown(supplierId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.supplierDrilldown(supplierId!, orgId),
    queryFn: async () => {
      if (!supplierId) return null;
      const response = await analyticsAPI.getSupplierDrilldown(supplierId);
      return response.data;
    },
    enabled: !!supplierId, // Only fetch when supplierId is provided
  });
}

/**
 * Get tail spend analysis
 */
export function useTailSpend(threshold: number = 20) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.tailSpend(threshold, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getTailSpend(threshold);
      return response.data;
    },
  });
}

/**
 * Get detailed tail spend analysis with dollar threshold.
 * Use this for the TailSpend dashboard page.
 *
 * @param threshold - Dollar threshold for tail classification (default $50,000)
 */
export function useDetailedTailSpend(threshold: number = 50000) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.tailSpendDetailed(threshold, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getDetailedTailSpend(threshold);
      return response.data;
    },
  });
}

/**
 * Get tail spend category drill-down data for TailSpend page modal.
 * Fetches vendor-level breakdown on-demand when a category is selected.
 */
export function useTailSpendCategoryDrilldown(
  categoryId: number | null,
  threshold: number = 50000,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.tailSpendCategoryDrilldown(
      categoryId!,
      threshold,
      orgId,
    ),
    queryFn: async () => {
      if (!categoryId) return null;
      const response = await analyticsAPI.getTailSpendCategoryDrilldown(
        categoryId,
        threshold,
      );
      return response.data;
    },
    enabled: !!categoryId, // Only fetch when categoryId is provided
  });
}

/**
 * Get tail spend vendor drill-down data for TailSpend page modal.
 * Fetches category breakdown, locations, and monthly spend.
 */
export function useTailSpendVendorDrilldown(
  supplierId: number | null,
  threshold: number = 50000,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.tailSpendVendorDrilldown(
      supplierId!,
      threshold,
      orgId,
    ),
    queryFn: async () => {
      if (!supplierId) return null;
      const response = await analyticsAPI.getTailSpendVendorDrilldown(
        supplierId,
        threshold,
      );
      return response.data;
    },
    enabled: !!supplierId, // Only fetch when supplierId is provided
  });
}

/**
 * Get spend stratification
 */
export function useStratification() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.stratification(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getStratification();
      return response.data;
    },
  });
}

/**
 * Get detailed spend stratification (by spend bands)
 * Use this for the SpendStratification dashboard page
 */
export function useDetailedStratification() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.stratificationDetailed(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getDetailedStratification();
      return response.data;
    },
  });
}

/**
 * Get segment drill-down data for SpendStratification modal
 * Fetches on-demand when a segment is selected
 */
export function useSegmentDrilldown(segmentName: string | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.segmentDrilldown(segmentName!, orgId),
    queryFn: async () => {
      if (!segmentName) return null;
      const response = await analyticsAPI.getSegmentDrilldown(segmentName);
      return response.data;
    },
    enabled: !!segmentName, // Only fetch when segmentName is provided
  });
}

/**
 * Get spend band drill-down data for SpendStratification modal
 * Fetches on-demand when a spend band is selected
 */
export function useBandDrilldown(bandName: string | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.bandDrilldown(bandName!, orgId),
    queryFn: async () => {
      if (!bandName) return null;
      const response = await analyticsAPI.getBandDrilldown(bandName);
      return response.data;
    },
    enabled: !!bandName, // Only fetch when bandName is provided
  });
}

/**
 * Get seasonality analysis
 */
export function useSeasonality() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.seasonality(false, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getSeasonality();
      return response.data;
    },
  });
}

/**
 * Get detailed seasonality analysis with fiscal year support, category breakdowns,
 * seasonal indices, and savings potential calculations.
 * Use this for the Seasonality dashboard page.
 */
export function useDetailedSeasonality(useFiscalYear: boolean = true) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.seasonalityDetailed(useFiscalYear, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getDetailedSeasonality(useFiscalYear);
      return response.data;
    },
  });
}

/**
 * Get seasonality category drill-down data for Seasonality page modal.
 * Fetches supplier-level seasonal patterns on-demand when a category is selected.
 */
export function useSeasonalityCategoryDrilldown(
  categoryId: number | null,
  useFiscalYear: boolean = true,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.seasonalityCategoryDrilldown(
      categoryId!,
      useFiscalYear,
      orgId,
    ),
    queryFn: async () => {
      if (!categoryId) return null;
      const response = await analyticsAPI.getSeasonalityCategoryDrilldown(
        categoryId,
        useFiscalYear,
      );
      return response.data;
    },
    enabled: !!categoryId, // Only fetch when categoryId is provided
  });
}

/**
 * Get year over year comparison
 */
export function useYearOverYear() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.yearOverYear(false, 0, 0, orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getYearOverYear();
      return response.data;
    },
  });
}

/**
 * Get detailed year over year comparison with fiscal year support,
 * category/supplier comparisons, monthly trends, and top gainers/decliners.
 * Use this for the YearOverYear dashboard page.
 */
export function useDetailedYearOverYear(
  useFiscalYear: boolean = true,
  year1?: number,
  year2?: number,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.yoyDetailed(
      useFiscalYear,
      year1 ?? 0,
      year2 ?? 0,
      orgId,
    ),
    queryFn: async () => {
      const response = await analyticsAPI.getDetailedYearOverYear(
        useFiscalYear,
        year1,
        year2,
      );
      return response.data;
    },
  });
}

/**
 * Get YoY category drill-down data for YearOverYear page modal.
 * Fetches supplier-level YoY breakdown on-demand when a category is selected.
 */
export function useYoYCategoryDrilldown(
  categoryId: number | null,
  useFiscalYear: boolean = true,
  year1?: number,
  year2?: number,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.yoyCategoryDrilldown(
      categoryId!,
      useFiscalYear,
      year1 ?? 0,
      year2 ?? 0,
      orgId,
    ),
    queryFn: async () => {
      if (!categoryId) return null;
      const response = await analyticsAPI.getYoYCategoryDrilldown(
        categoryId,
        useFiscalYear,
        year1,
        year2,
      );
      return response.data;
    },
    enabled: !!categoryId, // Only fetch when categoryId is provided
  });
}

/**
 * Get YoY supplier drill-down data for YearOverYear page modal.
 * Fetches category-level YoY breakdown on-demand when a supplier is selected.
 */
export function useYoYSupplierDrilldown(
  supplierId: number | null,
  useFiscalYear: boolean = true,
  year1?: number,
  year2?: number,
) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.yoySupplierDrilldown(
      supplierId!,
      useFiscalYear,
      year1 ?? 0,
      year2 ?? 0,
      orgId,
    ),
    queryFn: async () => {
      if (!supplierId) return null;
      const response = await analyticsAPI.getYoYSupplierDrilldown(
        supplierId,
        useFiscalYear,
        year1,
        year2,
      );
      return response.data;
    },
    enabled: !!supplierId, // Only fetch when supplierId is provided
  });
}

/**
 * Get consolidation opportunities
 */
export function useConsolidation() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.analytics.consolidation(orgId),
    queryFn: async () => {
      const response = await analyticsAPI.getConsolidation();
      return response.data;
    },
  });
}

/**
 * Get all transactions
 */
export function useTransactions(params?: Record<string, unknown>) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.procurement.transactions.list(params, orgId),
    queryFn: async () => {
      const response = await procurementAPI.getTransactions(params);
      return response.data;
    },
  });
}

/**
 * Get all suppliers
 */
export function useSuppliers() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.procurement.suppliers.list(undefined, orgId),
    queryFn: async () => {
      const response = await procurementAPI.getSuppliers();
      return response.data;
    },
  });
}

/**
 * Get all categories
 */
export function useCategories() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: queryKeys.procurement.categories.list(undefined, orgId),
    queryFn: async () => {
      const response = await procurementAPI.getCategories();
      return response.data;
    },
  });
}
