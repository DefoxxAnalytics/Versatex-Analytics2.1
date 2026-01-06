/**
 * Custom hooks for AI Insights data from Django API
 */
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '@/lib/api';
import type { AIInsight, AIInsightType } from '@/lib/api';

/**
 * Get all AI insights combined
 */
export function useAIInsights() {
  return useQuery({
    queryKey: ['ai-insights'],
    queryFn: async () => {
      const response = await analyticsAPI.getAIInsights();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes (expensive computation)
    retry: 2,
  });
}

/**
 * Get cost optimization insights only
 */
export function useAIInsightsCost() {
  return useQuery({
    queryKey: ['ai-insights-cost'],
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
  return useQuery({
    queryKey: ['ai-insights-risk'],
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
  return useQuery({
    queryKey: ['ai-insights-anomalies', sensitivity],
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
export function filterInsightsByType(insights: AIInsight[], type: AIInsightType | 'all'): AIInsight[] {
  if (type === 'all') return insights;
  return insights.filter(insight => insight.type === type);
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
    cost_optimization: 'Cost Optimization',
    risk: 'Supplier Risk',
    anomaly: 'Anomaly',
    consolidation: 'Consolidation',
  };
  return labels[type] || type;
}

/**
 * Get insight type icon color
 */
export function getInsightTypeColor(type: AIInsightType): string {
  const colors: Record<AIInsightType, string> = {
    cost_optimization: 'text-green-600 bg-green-100',
    risk: 'text-red-600 bg-red-100',
    anomaly: 'text-yellow-600 bg-yellow-100',
    consolidation: 'text-blue-600 bg-blue-100',
  };
  return colors[type] || 'text-gray-600 bg-gray-100';
}

/**
 * Get severity badge color
 */
export function getSeverityColor(severity: 'high' | 'medium' | 'low'): string {
  const colors = {
    high: 'bg-red-100 text-red-800 border-red-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
  };
  return colors[severity];
}
