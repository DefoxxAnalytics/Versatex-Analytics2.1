/**
 * AI Insights Page
 *
 * Displays AI-powered procurement insights including:
 * - Cost optimization opportunities
 * - Supplier risk analysis
 * - Anomaly detection
 * - Consolidation recommendations
 */

import { useState, useMemo } from 'react';
import {
  Sparkles,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  Users,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Target,
  Shield,
  Zap,
  RefreshCw,
  ArrowUpDown,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { StatCard } from '@/components/StatCard';
import { SkeletonCard } from '@/components/SkeletonCard';
import {
  useAIInsights,
  filterInsightsByType,
  getInsightTypeLabel,
  getInsightTypeColor,
  getSeverityColor,
} from '@/hooks/useAIInsights';
import type { AIInsight, AIInsightType } from '@/lib/api';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';

// Sort options type
type SortOption = 'savings' | 'severity' | 'confidence';

// Custom sort function based on selected option
function sortInsightsByOption(insights: AIInsight[], sortBy: SortOption): AIInsight[] {
  return [...insights].sort((a, b) => {
    switch (sortBy) {
      case 'savings':
        return b.potential_savings - a.potential_savings;
      case 'severity': {
        const severityOrder = { high: 0, medium: 1, low: 2 };
        return severityOrder[a.severity] - severityOrder[b.severity];
      }
      case 'confidence':
        return b.confidence - a.confidence;
      default:
        return 0;
    }
  });
}

// Insight card component
interface InsightCardProps {
  insight: AIInsight;
}

function InsightCard({ insight }: InsightCardProps) {
  const [expanded, setExpanded] = useState(false);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getTypeIcon = (type: AIInsightType) => {
    const icons = {
      cost_optimization: DollarSign,
      risk: Shield,
      anomaly: Zap,
      consolidation: Users,
    };
    return icons[type] || Lightbulb;
  };

  const TypeIcon = getTypeIcon(insight.type);

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          {/* Type Icon */}
          <div className={`p-3 rounded-lg ${getInsightTypeColor(insight.type)}`}>
            <TypeIcon className="h-5 w-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="font-semibold text-gray-900 text-sm sm:text-base">
                {insight.title}
              </h3>
              <div className="flex items-center gap-2 shrink-0">
                <Badge className={`${getSeverityColor(insight.severity)} border text-xs`}>
                  {insight.severity.toUpperCase()}
                </Badge>
                {insight.potential_savings > 0 && (
                  <Badge className="bg-green-100 text-green-800 border-green-200 border text-xs">
                    {formatCurrency(insight.potential_savings)} savings
                  </Badge>
                )}
              </div>
            </div>

            <p className="text-gray-600 text-sm mb-3">{insight.description}</p>

            {/* Confidence */}
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs text-gray-500">Confidence:</span>
              <div className="flex-1 max-w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${insight.confidence * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-600 font-medium">
                {Math.round(insight.confidence * 100)}%
              </span>
            </div>

            {/* Expand/Collapse Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="text-blue-600 hover:text-blue-700 p-0 h-auto"
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Hide details
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Show details
                </>
              )}
            </Button>

            {/* Expanded Details */}
            {expanded && (
              <div className="mt-4 space-y-4 border-t pt-4">
                {/* Recommended Actions */}
                {insight.recommended_actions.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Recommended Actions
                    </h4>
                    <ul className="space-y-2">
                      {insight.recommended_actions.map((action, index) => (
                        <li
                          key={index}
                          className="flex items-start gap-2 text-sm text-gray-600"
                        >
                          <Target className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Affected Entities */}
                {insight.affected_entities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Affected Entities
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {insight.affected_entities.map((entity, index) => (
                        <Badge
                          key={index}
                          variant="outline"
                          className="text-xs"
                        >
                          {entity}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Additional Data */}
                {insight.data && Object.keys(insight.data).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Details
                    </h4>
                    <div className="bg-gray-50 rounded-lg p-3 text-xs">
                      <pre className="whitespace-pre-wrap text-gray-600">
                        {JSON.stringify(insight.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Donut chart colors matching insight type colors
const CHART_COLORS = {
  cost_optimization: '#22c55e', // green
  risk: '#ef4444', // red
  anomaly: '#eab308', // yellow
  consolidation: '#3b82f6', // blue
};

export default function AIInsightsPage() {
  const { data, isLoading, error, refetch, isFetching } = useAIInsights();
  const [activeTab, setActiveTab] = useState<AIInsightType | 'all'>('all');
  const [sortBy, setSortBy] = useState<SortOption>('severity');

  // Filter and sort insights
  const filteredInsights = useMemo(() => {
    if (!data?.insights) return [];
    const filtered = filterInsightsByType(data.insights, activeTab);
    return sortInsightsByOption(filtered, sortBy);
  }, [data?.insights, activeTab, sortBy]);

  // Calculate savings by type for donut chart
  const savingsByType = useMemo(() => {
    if (!data?.insights) return [];
    const savingsMap: Record<string, number> = {};

    data.insights.forEach((insight) => {
      if (insight.potential_savings > 0) {
        savingsMap[insight.type] = (savingsMap[insight.type] || 0) + insight.potential_savings;
      }
    });

    return Object.entries(savingsMap).map(([type, value]) => ({
      name: getInsightTypeLabel(type as AIInsightType),
      value,
      type,
    }));
  }, [data?.insights]);

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-8 p-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-yellow-500" />
            AI Insights
          </h1>
          <p className="text-gray-600 mt-2">
            Smart recommendations powered by machine learning
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>

        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg" />
                  <div className="flex-1 space-y-3">
                    <div className="h-5 bg-gray-200 rounded w-2/3" />
                    <div className="h-4 bg-gray-200 rounded w-full" />
                    <div className="h-4 bg-gray-200 rounded w-1/3" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-md">
          <AlertTriangle className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Unable to Load Insights
          </h2>
          <p className="text-gray-600 mb-6">
            There was an error loading AI insights. This may be due to insufficient data or a server issue.
          </p>
          <Button onClick={() => refetch()} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // No data state
  if (!data || data.insights.length === 0) {
    return (
      <div className="space-y-8 p-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-yellow-500" />
            AI Insights
          </h1>
          <p className="text-gray-600 mt-2">
            Smart recommendations powered by machine learning
          </p>
        </div>

        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center max-w-md">
            <Lightbulb className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              No Insights Available
            </h2>
            <p className="text-gray-600">
              Upload more procurement data to generate AI-powered insights and recommendations.
              The system needs sufficient transaction history to identify patterns and opportunities.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { summary } = data;

  return (
    <div className="space-y-8 p-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-yellow-500" />
            AI Insights
          </h1>
          <p className="text-gray-600 mt-2">
            Smart recommendations powered by machine learning
          </p>
        </div>
        <Button
          onClick={() => refetch()}
          variant="outline"
          disabled={isFetching}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <StatCard
          title="Total Insights"
          value={summary.total_insights}
          description="Recommendations found"
          icon={Lightbulb}
        />
        <StatCard
          title="High Priority"
          value={summary.high_priority}
          description="Require attention"
          icon={AlertTriangle}
          className={summary.high_priority > 0 ? 'border-red-200 bg-red-50' : ''}
        />
        <StatCard
          title="Potential Savings"
          value={formatCurrency(summary.total_potential_savings)}
          description="Identified opportunities"
          icon={DollarSign}
          className="border-green-200 bg-green-50"
        />
        <StatCard
          title="Categories"
          value={Object.keys(summary.by_type).length}
          description="Insight types"
          icon={Target}
        />
      </div>

      {/* Savings Visualization and Insights Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Savings by Type Donut Chart */}
        {savingsByType.length > 0 && (
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <div className="flex items-center gap-2">
                <DollarSign className="h-6 w-6 text-green-600" />
                <CardTitle>Savings by Type</CardTitle>
              </div>
              <CardDescription>
                Potential savings breakdown by insight category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={savingsByType}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {savingsByType.map((entry) => (
                      <Cell
                        key={entry.type}
                        fill={CHART_COLORS[entry.type as keyof typeof CHART_COLORS] || '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value) => <span className="text-sm text-gray-600">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="text-center mt-2">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(summary.total_potential_savings)}
                </div>
                <div className="text-sm text-gray-500">Total Potential Savings</div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Insights by Type Summary - spans 2 columns on lg screens */}
        <Card className={`border-0 shadow-lg bg-gradient-to-br from-yellow-50 to-amber-50 ${savingsByType.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-amber-600" />
              <CardTitle className="text-amber-900">Insights Overview</CardTitle>
            </div>
            <CardDescription className="text-amber-700">
              AI-powered analysis of your procurement data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <DollarSign className="h-4 w-4 text-green-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Cost</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {summary.by_type.cost_optimization || 0}
                </div>
                <div className="text-xs text-gray-500">optimization opportunities</div>
              </div>

              <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <Shield className="h-4 w-4 text-red-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Risk</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {summary.by_type.risk || 0}
                </div>
                <div className="text-xs text-gray-500">supplier risks identified</div>
              </div>

              <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Zap className="h-4 w-4 text-yellow-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Anomalies</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {summary.by_type.anomaly || 0}
                </div>
                <div className="text-xs text-gray-500">unusual patterns detected</div>
              </div>

              <div className="bg-white rounded-lg p-4 shadow-sm border border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="h-4 w-4 text-blue-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Consolidation</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {summary.by_type.consolidation || 0}
                </div>
                <div className="text-xs text-gray-500">consolidation opportunities</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights List with Tabs */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle>Detailed Insights</CardTitle>
              <CardDescription>
                Click on each insight to see recommended actions and affected entities
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-4 w-4 text-gray-500" />
              <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="severity">Severity</SelectItem>
                  <SelectItem value="savings">Savings Potential</SelectItem>
                  <SelectItem value="confidence">Confidence</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as AIInsightType | 'all')}>
            <TabsList className="mb-6">
              <TabsTrigger value="all">
                All ({data.insights.length})
              </TabsTrigger>
              <TabsTrigger value="cost_optimization">
                Cost ({summary.by_type.cost_optimization || 0})
              </TabsTrigger>
              <TabsTrigger value="risk">
                Risk ({summary.by_type.risk || 0})
              </TabsTrigger>
              <TabsTrigger value="anomaly">
                Anomalies ({summary.by_type.anomaly || 0})
              </TabsTrigger>
              <TabsTrigger value="consolidation">
                Consolidation ({summary.by_type.consolidation || 0})
              </TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-0">
              {filteredInsights.length > 0 ? (
                <div className="space-y-4">
                  {filteredInsights.map((insight) => (
                    <InsightCard key={insight.id} insight={insight} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Lightbulb className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>No {getInsightTypeLabel(activeTab as AIInsightType)} insights found</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
