/**
 * Custom hooks for AI Insights data from Django API
 *
 * All hooks include organization_id in query keys to properly
 * invalidate cache when switching organizations (superuser feature).
 *
 * Features:
 * - Structured AI enhancement from tool calling
 * - Redis caching with cache_hit indicator
 * - Manual refresh support to bypass cache
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { analyticsAPI, getOrganizationParam } from "@/lib/api";
import type {
  AIInsight,
  AIInsightType,
  AIEnhancement,
  AIRecommendation,
  AIImpactLevel,
  AIEffortLevel,
  InsightFeedbackRequest,
  InsightOutcomeUpdateRequest,
  InsightActionTaken,
  InsightOutcome,
  InsightFeedbackItem,
  InsightEffectivenessMetrics,
} from "@/lib/api";

/**
 * Get the current organization ID for query key inclusion.
 * Returns undefined if viewing own org (default behavior).
 */
function getOrgKeyPart(): number | undefined {
  const param = getOrganizationParam();
  return param.organization_id;
}

/**
 * Get all AI insights combined with optional AI enhancement
 */
export function useAIInsights() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["ai-insights", { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getAIInsights(false);
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes (expensive computation)
    retry: 2,
  });
}

/**
 * Mutation to force refresh AI insights (bypasses backend cache)
 */
export function useRefreshAIInsights() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async () => {
      const response = await analyticsAPI.getAIInsights(true);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["ai-insights", { orgId }], data);
    },
  });
}

/**
 * Get cost optimization insights only
 */
export function useAIInsightsCost() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["ai-insights-cost", { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getAIInsightsCost();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get supplier risk insights only
 */
export function useAIInsightsRisk() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["ai-insights-risk", { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getAIInsightsRisk();
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get anomaly detection insights
 */
export function useAIInsightsAnomalies(sensitivity: number = 2.0) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["ai-insights-anomalies", sensitivity, { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getAIInsightsAnomalies(sensitivity);
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Filter insights by type
 */
export function filterInsightsByType(
  insights: AIInsight[],
  type: AIInsightType | "all",
): AIInsight[] {
  if (type === "all") return insights;
  return insights.filter((insight) => insight.type === type);
}

/**
 * Sort insights by severity and potential savings
 */
export function sortInsights(insights: AIInsight[]): AIInsight[] {
  const severityOrder = { high: 0, medium: 1, low: 2 };
  return [...insights].sort((a, b) => {
    // First sort by severity
    const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
    if (severityDiff !== 0) return severityDiff;
    // Then by potential savings (descending)
    return b.potential_savings - a.potential_savings;
  });
}

/**
 * Get insight type display label
 */
export function getInsightTypeLabel(type: AIInsightType): string {
  const labels: Record<AIInsightType, string> = {
    cost_optimization: "Cost Optimization",
    risk: "Supplier Risk",
    anomaly: "Anomaly",
    consolidation: "Consolidation",
  };
  return labels[type] || type;
}

/**
 * Get insight type icon color
 */
export function getInsightTypeColor(type: AIInsightType): string {
  const colors: Record<AIInsightType, string> = {
    cost_optimization: "text-green-600 bg-green-100",
    risk: "text-red-600 bg-red-100",
    anomaly: "text-yellow-600 bg-yellow-100",
    consolidation: "text-blue-600 bg-blue-100",
  };
  return colors[type] || "text-gray-600 bg-gray-100";
}

/**
 * Get severity badge color
 */
export function getSeverityColor(severity: "high" | "medium" | "low"): string {
  const colors = {
    high: "bg-red-100 text-red-800 border-red-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    low: "bg-green-100 text-green-800 border-green-200",
  };
  return colors[severity];
}

/**
 * Get impact level badge color for AI recommendations
 */
export function getImpactColor(impact: AIImpactLevel): string {
  const colors: Record<AIImpactLevel, string> = {
    high: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-blue-100 text-blue-800 border-blue-200",
    low: "bg-gray-100 text-gray-800 border-gray-200",
  };
  return colors[impact];
}

/**
 * Get effort level badge color for AI recommendations
 */
export function getEffortColor(effort: AIEffortLevel): string {
  const colors: Record<AIEffortLevel, string> = {
    low: "bg-green-100 text-green-700",
    medium: "bg-yellow-100 text-yellow-700",
    high: "bg-red-100 text-red-700",
  };
  return colors[effort];
}

/**
 * Get risk level color for AI risk assessment
 */
export function getRiskLevelColor(
  level: "critical" | "high" | "moderate" | "low",
): string {
  const colors = {
    critical: "bg-red-600 text-white",
    high: "bg-red-100 text-red-800",
    moderate: "bg-yellow-100 text-yellow-800",
    low: "bg-green-100 text-green-800",
  };
  return colors[level];
}

/**
 * Sort recommendations by impact/effort ratio (high impact, low effort first)
 */
export function sortRecommendationsByValue(
  recommendations: AIRecommendation[],
): AIRecommendation[] {
  const impactScore: Record<AIImpactLevel, number> = {
    high: 3,
    medium: 2,
    low: 1,
  };
  const effortScore: Record<AIEffortLevel, number> = {
    low: 3,
    medium: 2,
    high: 1,
  };

  return [...recommendations].sort((a, b) => {
    const aValue = impactScore[a.impact] * effortScore[a.effort];
    const bValue = impactScore[b.impact] * effortScore[b.effort];
    return bValue - aValue;
  });
}

// ============================================================================
// AI Insight Feedback Hooks (ROI Tracking)
// ============================================================================

/**
 * Record user action on an AI insight
 */
export function useRecordInsightFeedback() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async (data: InsightFeedbackRequest) => {
      const response = await analyticsAPI.recordInsightFeedback(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["insight-feedback", { orgId }],
      });
      queryClient.invalidateQueries({
        queryKey: ["insight-effectiveness", { orgId }],
      });
    },
  });
}

/**
 * Update the outcome of a previously recorded insight action
 */
export function useUpdateInsightOutcome() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async ({
      feedbackId,
      data,
    }: {
      feedbackId: string;
      data: InsightOutcomeUpdateRequest;
    }) => {
      const response = await analyticsAPI.updateInsightOutcome(
        feedbackId,
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["insight-feedback", { orgId }],
      });
      queryClient.invalidateQueries({
        queryKey: ["insight-effectiveness", { orgId }],
      });
    },
  });
}

/**
 * Delete an insight feedback entry.
 * Only the creator or an admin can delete feedback.
 */
export function useDeleteInsightFeedback() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async (feedbackId: string) => {
      const response = await analyticsAPI.deleteInsightFeedback(feedbackId);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["insight-feedback", { orgId }],
      });
      queryClient.invalidateQueries({
        queryKey: ["insight-effectiveness", { orgId }],
      });
    },
  });
}

/**
 * Get effectiveness metrics for AI insights
 */
export function useInsightEffectiveness() {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["insight-effectiveness", { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getInsightEffectiveness();
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });
}

/**
 * List insight feedback with optional filters
 */
export function useInsightFeedbackList(params?: {
  insight_type?: AIInsightType;
  action_taken?: InsightActionTaken;
  outcome?: InsightOutcome;
  limit?: number;
  offset?: number;
}) {
  const orgId = getOrgKeyPart();
  return useQuery({
    queryKey: ["insight-feedback", params, { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.listInsightFeedback(params);
      return response.data;
    },
    staleTime: 60 * 1000, // Cache for 1 minute
  });
}

/**
 * Get action taken display label
 */
export function getActionLabel(action: InsightActionTaken): string {
  const labels: Record<InsightActionTaken, string> = {
    implemented: "Implemented",
    dismissed: "Dismissed",
    deferred: "Deferred",
    investigating: "Investigating",
    partial: "Partially Implemented",
  };
  return labels[action] || action;
}

/**
 * Get action taken badge color
 */
export function getActionColor(action: InsightActionTaken): string {
  const colors: Record<InsightActionTaken, string> = {
    implemented: "bg-green-100 text-green-800 border-green-200",
    dismissed: "bg-gray-100 text-gray-800 border-gray-200",
    deferred: "bg-yellow-100 text-yellow-800 border-yellow-200",
    investigating: "bg-blue-100 text-blue-800 border-blue-200",
    partial: "bg-purple-100 text-purple-800 border-purple-200",
  };
  return colors[action] || "bg-gray-100 text-gray-800 border-gray-200";
}

/**
 * Get outcome display label
 */
export function getOutcomeLabel(outcome: InsightOutcome): string {
  const labels: Record<InsightOutcome, string> = {
    pending: "Pending",
    success: "Success",
    partial_success: "Partial Success",
    no_change: "No Change",
    failed: "Failed",
  };
  return labels[outcome] || outcome;
}

/**
 * Get outcome badge color
 */
export function getOutcomeColor(outcome: InsightOutcome): string {
  const colors: Record<InsightOutcome, string> = {
    pending: "bg-gray-100 text-gray-600",
    success: "bg-green-100 text-green-800",
    partial_success: "bg-yellow-100 text-yellow-800",
    no_change: "bg-orange-100 text-orange-800",
    failed: "bg-red-100 text-red-800",
  };
  return colors[outcome] || "bg-gray-100 text-gray-600";
}

// ============================================================================
// Async AI Enhancement Hooks
// ============================================================================

/**
 * Request async AI enhancement for insights
 */
export function useRequestAsyncEnhancement() {
  const queryClient = useQueryClient();
  const orgId = getOrgKeyPart();

  return useMutation({
    mutationFn: async (insights: AIInsight[]) => {
      const response = await analyticsAPI.requestAsyncEnhancement({ insights });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["async-enhancement-status", { orgId }],
      });
    },
  });
}

/**
 * Poll for async AI enhancement status
 *
 * @param enabled - Whether to enable polling
 * @param pollInterval - Polling interval in ms (default: 2000)
 */
export function useAsyncEnhancementStatus(
  enabled: boolean = true,
  pollInterval: number = 2000,
) {
  const orgId = getOrgKeyPart();

  return useQuery({
    queryKey: ["async-enhancement-status", { orgId }],
    queryFn: async () => {
      const response = await analyticsAPI.getAsyncEnhancementStatus();
      return response.data;
    },
    enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "processing" || data?.status === "queued") {
        return pollInterval;
      }
      return false;
    },
    staleTime: 0,
    retry: false,
  });
}

// ============================================================================
// Deep Analysis Hooks
// ============================================================================

/**
 * Request deep analysis for a specific insight
 */
export function useRequestDeepAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (insight: AIInsight) => {
      const response = await analyticsAPI.requestDeepAnalysis({ insight });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["deep-analysis-status", data.insight_id],
      });
    },
  });
}

/**
 * Poll for deep analysis status for a specific insight
 *
 * @param insightId - The insight ID to check status for
 * @param enabled - Whether to enable polling
 * @param pollInterval - Polling interval in ms (default: 2000)
 */
export function useDeepAnalysisStatus(
  insightId: string | null,
  enabled: boolean = true,
  pollInterval: number = 2000,
) {
  const orgId = getOrgKeyPart();

  return useQuery({
    queryKey: ["deep-analysis-status", insightId, { orgId }],
    queryFn: async () => {
      if (!insightId) throw new Error("Insight ID required");
      const response = await analyticsAPI.getDeepAnalysisStatus(insightId);
      return response.data;
    },
    enabled: enabled && !!insightId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "processing") {
        return pollInterval;
      }
      return false;
    },
    staleTime: 0,
    retry: false,
  });
}

/**
 * Get risk level color for deep analysis risk factors
 */
export function getDeepAnalysisRiskColor(
  likelihood: "high" | "medium" | "low",
  impact: "high" | "medium" | "low",
): string {
  const score =
    (likelihood === "high" ? 3 : likelihood === "medium" ? 2 : 1) *
    (impact === "high" ? 3 : impact === "medium" ? 2 : 1);

  if (score >= 6) return "bg-red-100 text-red-800 border-red-200";
  if (score >= 4) return "bg-yellow-100 text-yellow-800 border-yellow-200";
  return "bg-green-100 text-green-800 border-green-200";
}

/**
 * Get phase status color for implementation roadmap
 */
export function getPhaseColor(phaseIndex: number, totalPhases: number): string {
  const colors = [
    "bg-blue-100 text-blue-800 border-blue-200",
    "bg-indigo-100 text-indigo-800 border-indigo-200",
    "bg-purple-100 text-purple-800 border-purple-200",
    "bg-violet-100 text-violet-800 border-violet-200",
  ];
  return colors[phaseIndex % colors.length];
}

// Re-export types for convenience
export type {
  AIEnhancement,
  AIRecommendation,
  AIImpactLevel,
  AIEffortLevel,
  InsightActionTaken,
  InsightOutcome,
  InsightFeedbackItem,
  InsightEffectivenessMetrics,
  // Async Enhancement types
  AsyncEnhancementStatus,
  AsyncEnhancementStatusResponse,
  // Deep Analysis types
  DeepAnalysis,
  DeepAnalysisStatus,
  DeepAnalysisStatusResponse,
  DeepAnalysisRootCause,
  DeepAnalysisPhase,
  DeepAnalysisFinancialImpact,
  DeepAnalysisRiskFactor,
  DeepAnalysisSuccessMetric,
} from "@/lib/api";
