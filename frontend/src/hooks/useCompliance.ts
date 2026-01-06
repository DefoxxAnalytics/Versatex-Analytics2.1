/**
 * Custom hooks for Compliance & Maverick Spend data from Django API
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsAPI } from '@/lib/api';
import type { ViolationType, ViolationSeverity, RiskLevel } from '@/lib/api';

/**
 * Get compliance overview statistics
 */
export function useComplianceOverview() {
  return useQuery({
    queryKey: ['compliance-overview'],
    queryFn: async () => {
      const response = await analyticsAPI.getComplianceOverview();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Get maverick spend analysis
 */
export function useMaverickSpendAnalysis() {
  return useQuery({
    queryKey: ['maverick-spend-analysis'],
    queryFn: async () => {
      const response = await analyticsAPI.getMaverickSpendAnalysis();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get policy violations with optional filtering
 */
export function usePolicyViolations(params?: {
  resolved?: boolean;
  severity?: ViolationSeverity;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['policy-violations', params],
    queryFn: async () => {
      const response = await analyticsAPI.getPolicyViolations(params);
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // Shorter stale time for violations
  });
}

/**
 * Get violation trends over time
 */
export function useViolationTrends(months: number = 12) {
  return useQuery({
    queryKey: ['violation-trends', months],
    queryFn: async () => {
      const response = await analyticsAPI.getViolationTrends(months);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get supplier compliance scores
 */
export function useSupplierComplianceScores() {
  return useQuery({
    queryKey: ['supplier-compliance-scores'],
    queryFn: async () => {
      const response = await analyticsAPI.getSupplierComplianceScores();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get spending policies
 */
export function useSpendingPolicies() {
  return useQuery({
    queryKey: ['spending-policies'],
    queryFn: async () => {
      const response = await analyticsAPI.getSpendingPolicies();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Resolve a policy violation
 */
export function useResolveViolation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ violationId, resolutionNotes }: { violationId: number; resolutionNotes: string }) => {
      const response = await analyticsAPI.resolveViolation(violationId, resolutionNotes);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['policy-violations'] });
      queryClient.invalidateQueries({ queryKey: ['compliance-overview'] });
      queryClient.invalidateQueries({ queryKey: ['supplier-compliance-scores'] });
    },
  });
}

/**
 * Get violation severity display info
 */
export function getViolationSeverityDisplay(severity: ViolationSeverity): {
  label: string;
  color: string;
  bgColor: string;
} {
  const displays: Record<ViolationSeverity, { label: string; color: string; bgColor: string }> = {
    critical: {
      label: 'Critical',
      color: 'text-red-700',
      bgColor: 'bg-red-100',
    },
    high: {
      label: 'High',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    medium: {
      label: 'Medium',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    },
    low: {
      label: 'Low',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
  };
  return displays[severity] || displays.medium;
}

/**
 * Get violation type display info
 */
export function getViolationTypeDisplay(type: ViolationType): {
  label: string;
  icon: string;
} {
  const displays: Record<ViolationType, { label: string; icon: string }> = {
    amount_exceeded: {
      label: 'Amount Exceeded',
      icon: 'dollar-sign',
    },
    non_preferred_supplier: {
      label: 'Non-Preferred Supplier',
      icon: 'user-x',
    },
    restricted_category: {
      label: 'Restricted Category',
      icon: 'ban',
    },
    no_contract: {
      label: 'No Contract',
      icon: 'file-x',
    },
    approval_missing: {
      label: 'Approval Missing',
      icon: 'check-circle',
    },
  };
  return displays[type] || { label: type, icon: 'alert-triangle' };
}

/**
 * Get risk level display info
 */
export function getRiskLevelDisplay(level: RiskLevel): {
  label: string;
  color: string;
  bgColor: string;
} {
  const displays: Record<RiskLevel, { label: string; color: string; bgColor: string }> = {
    high: {
      label: 'High Risk',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    medium: {
      label: 'Medium Risk',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    },
    low: {
      label: 'Low Risk',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
  };
  return displays[level] || displays.medium;
}

/**
 * Get compliance score color based on value
 */
export function getComplianceScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-amber-600';
  return 'text-red-600';
}

/**
 * Get compliance rate status
 */
export function getComplianceRateStatus(rate: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (rate >= 95) {
    return {
      label: 'Excellent',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    };
  } else if (rate >= 85) {
    return {
      label: 'Good',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    };
  } else if (rate >= 70) {
    return {
      label: 'Needs Improvement',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    };
  } else {
    return {
      label: 'Critical',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    };
  }
}

/**
 * Format maverick spend percentage
 */
export function formatMaverickPercentage(percentage: number): string {
  return `${percentage.toFixed(1)}% off-contract`;
}
