/**
 * Custom hooks for Contract Analytics data from Django API
 *
 * All hooks include organization_id in query keys to properly
 * invalidate cache when switching organizations (superuser feature).
 */
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI, getOrganizationParam } from '@/lib/api';
import type { ContractStatus } from '@/lib/api';

/**
 * Get the current organization ID for query key inclusion.
 * Returns undefined if viewing own org (default behavior).
 */
function getOrgKeyPart(): number | undefined {
  const param = getOrganizationParam();
  return param.organization_id;
}

/**
 * Get contract portfolio overview
 */
export function useContractOverview() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-overview', { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getContractOverview();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
}

/**
 * Get list of all contracts
 */
export function useContracts() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contracts-list', { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getContracts();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get detailed information for a specific contract
 */
export function useContractDetail(contractId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-detail', contractId, { orgId }],
    queryFn: async () => {
      if (!contractId) return null;
      const response = await analyticsAPI.getContractDetail(contractId);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    enabled: contractId !== null && contractId > 0,
  });
}

/**
 * Get contracts expiring within specified days
 */
export function useExpiringContracts(days: number = 90) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['expiring-contracts', days, { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getExpiringContracts(days);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get performance metrics for a specific contract
 */
export function useContractPerformance(contractId: number | null) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-performance', contractId, { orgId }],
    queryFn: async () => {
      if (!contractId) return null;
      const response = await analyticsAPI.getContractPerformance(contractId);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    enabled: contractId !== null && contractId > 0,
  });
}

/**
 * Get contract savings opportunities
 */
export function useContractSavings() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-savings', { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getContractSavings();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get contract renewal recommendations
 */
export function useContractRenewals() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-renewals', { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getContractRenewals();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get contract vs actual spend comparison
 */
export function useContractVsActual(contractId?: number) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ['contract-vs-actual', contractId, { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getContractVsActual(contractId);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get contract status display info
 */
export function getContractStatusDisplay(status: ContractStatus): {
  label: string;
  color: string;
  bgColor: string;
} {
  const displays: Record<ContractStatus, { label: string; color: string; bgColor: string }> = {
    draft: {
      label: 'Draft',
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
    active: {
      label: 'Active',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    expiring: {
      label: 'Expiring Soon',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    },
    expired: {
      label: 'Expired',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    renewed: {
      label: 'Renewed',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    terminated: {
      label: 'Terminated',
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
  };
  return displays[status] || displays.draft;
}

/**
 * Get recommendation display info
 */
export function getRecommendationDisplay(recommendation: 'renew' | 'renegotiate' | 'terminate' | 'review'): {
  label: string;
  color: string;
  bgColor: string;
  icon: string;
} {
  const displays = {
    renew: {
      label: 'Renew',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      icon: 'check-circle',
    },
    renegotiate: {
      label: 'Renegotiate',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
      icon: 'refresh',
    },
    terminate: {
      label: 'Terminate',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      icon: 'x-circle',
    },
    review: {
      label: 'Review',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      icon: 'eye',
    },
  };
  return displays[recommendation] || displays.review;
}

/**
 * Get utilization status based on percentage
 */
export function getUtilizationStatus(percentage: number): {
  label: string;
  color: string;
  bgColor: string;
} {
  if (percentage >= 90) {
    return {
      label: 'High',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    };
  } else if (percentage >= 50) {
    return {
      label: 'Moderate',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    };
  } else if (percentage >= 25) {
    return {
      label: 'Low',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    };
  } else {
    return {
      label: 'Underutilized',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    };
  }
}

/**
 * Format days until expiry
 */
export function formatDaysUntilExpiry(days: number): string {
  if (days < 0) {
    return `Expired ${Math.abs(days)} days ago`;
  } else if (days === 0) {
    return 'Expires today';
  } else if (days === 1) {
    return 'Expires tomorrow';
  } else if (days < 30) {
    return `${days} days remaining`;
  } else if (days < 365) {
    const months = Math.floor(days / 30);
    return `${months} month${months > 1 ? 's' : ''} remaining`;
  } else {
    const years = Math.floor(days / 365);
    return `${years} year${years > 1 ? 's' : ''} remaining`;
  }
}

/**
 * Get savings opportunity type display
 */
export function getSavingsTypeDisplay(type: 'underutilized' | 'off_contract' | 'consolidation' | 'price_variance'): {
  label: string;
  color: string;
  bgColor: string;
} {
  const displays = {
    underutilized: {
      label: 'Underutilized Contract',
      color: 'text-amber-600',
      bgColor: 'bg-amber-100',
    },
    off_contract: {
      label: 'Off-Contract Spend',
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    consolidation: {
      label: 'Consolidation Opportunity',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    price_variance: {
      label: 'Price Variance',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  };
  return displays[type] || displays.underutilized;
}
