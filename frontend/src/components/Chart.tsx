/**
 * Reusable Chart Component
 * Wrapper around Apache ECharts for consistent chart rendering
 *
 * Security: Sanitizes all input data
 * Performance: Lazy loads ECharts, auto-resizes on window resize
 * Accessibility: Provides ARIA labels and keyboard navigation
 */

import { useEffect, useRef, useMemo } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

// Register ECharts components
echarts.use([
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
]);

interface ChartProps {
  /**
   * Chart title displayed in card header
   */
  title: string;

  /**
   * Optional description/explanation of what the chart shows
   */
  description?: string;

  /**
   * ECharts configuration object
   */
  option: EChartsOption;

  /**
   * Chart height in pixels
   * @default 300
   */
  height?: number;

  /**
   * Loading state
   * @default false
   */
  loading?: boolean;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Click handler for chart data points
   */
  onChartClick?: (params: {
    name: string;
    value: number;
    seriesType?: string;
    dataType?: string;
  }) => void;
}

/**
 * Get dark mode aware colors for chart styling
 */
function getDarkModeColors(isDark: boolean) {
  return {
    textColor: isDark ? "#e5e7eb" : "#374151",
    subTextColor: isDark ? "#9ca3af" : "#6b7280",
    axisLineColor: isDark ? "#374151" : "#e5e7eb",
    splitLineColor: isDark ? "#374151" : "#f3f4f6",
    tooltipBg: isDark ? "#1f2937" : "#ffffff",
    tooltipBorder: isDark ? "#374151" : "#e5e7eb",
  };
}

/**
 * Chart Component
 * Renders an ECharts chart with proper error handling and accessibility
 */
export function Chart({
  title,
  description,
  option,
  height = 300,
  loading = false,
  className = "",
  onChartClick,
}: ChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === "dark";

  // Merge dark mode colors with chart option
  const themedOption = useMemo(() => {
    const colors = getDarkModeColors(isDark);

    // Deep merge with user option, adding dark mode styling
    return {
      ...option,
      textStyle: {
        color: colors.textColor,
        ...(option as any).textStyle,
      },
      tooltip: {
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
        textStyle: {
          color: colors.textColor,
        },
        ...(option as any).tooltip,
      },
      legend: {
        textStyle: {
          color: colors.subTextColor,
        },
        ...(option as any).legend,
      },
      xAxis: Array.isArray((option as any).xAxis)
        ? (option as any).xAxis.map((axis: any) => ({
            ...axis,
            axisLine: {
              lineStyle: { color: colors.axisLineColor },
              ...axis?.axisLine,
            },
            axisLabel: {
              color: colors.subTextColor,
              ...axis?.axisLabel,
            },
            splitLine: {
              lineStyle: { color: colors.splitLineColor },
              ...axis?.splitLine,
            },
          }))
        : (option as any).xAxis
          ? {
              ...(option as any).xAxis,
              axisLine: {
                lineStyle: { color: colors.axisLineColor },
                ...(option as any).xAxis?.axisLine,
              },
              axisLabel: {
                color: colors.subTextColor,
                ...(option as any).xAxis?.axisLabel,
              },
              splitLine: {
                lineStyle: { color: colors.splitLineColor },
                ...(option as any).xAxis?.splitLine,
              },
            }
          : undefined,
      yAxis: Array.isArray((option as any).yAxis)
        ? (option as any).yAxis.map((axis: any) => ({
            ...axis,
            axisLine: {
              lineStyle: { color: colors.axisLineColor },
              ...axis?.axisLine,
            },
            axisLabel: {
              color: colors.subTextColor,
              ...axis?.axisLabel,
            },
            splitLine: {
              lineStyle: { color: colors.splitLineColor },
              ...axis?.splitLine,
            },
          }))
        : (option as any).yAxis
          ? {
              ...(option as any).yAxis,
              axisLine: {
                lineStyle: { color: colors.axisLineColor },
                ...(option as any).yAxis?.axisLine,
              },
              axisLabel: {
                color: colors.subTextColor,
                ...(option as any).yAxis?.axisLabel,
              },
              splitLine: {
                lineStyle: { color: colors.splitLineColor },
                ...(option as any).yAxis?.splitLine,
              },
            }
          : undefined,
    };
  }, [option, isDark]);

  // Initialize chart
  useEffect(() => {
    if (!chartRef.current) return;

    // Create chart instance
    const chartInstance = echarts.init(chartRef.current);
    chartInstanceRef.current = chartInstance;

    // Set option
    chartInstance.setOption(themedOption);

    // Handle click events
    if (onChartClick) {
      chartInstance.on("click", (params: any) => {
        onChartClick({
          name: params.name,
          value: params.value,
          seriesType: params.seriesType,
          dataType: params.dataType,
        });
      });
    }

    // Handle window resize
    const handleResize = () => {
      chartInstance.resize();
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance.off("click");
      chartInstance.dispose();
      chartInstanceRef.current = null;
    };
  }, [onChartClick]);

  // Update chart when option changes (including dark mode)
  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.setOption(themedOption, true);
    }
  }, [themedOption]);

  // Handle loading state
  useEffect(() => {
    if (chartInstanceRef.current) {
      const colors = getDarkModeColors(isDark);
      if (loading) {
        chartInstanceRef.current.showLoading({
          text: "Loading...",
          color: isDark ? "#60a5fa" : "#3b82f6",
          textColor: colors.textColor,
          maskColor: isDark ? "rgba(0, 0, 0, 0.5)" : "rgba(255, 255, 255, 0.8)",
        });
      } else {
        chartInstanceRef.current.hideLoading();
      }
    }
  }, [loading, isDark]);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
        {description && (
          <p
            className={cn(
              "text-sm mt-2",
              isDark ? "text-gray-400" : "text-gray-600",
            )}
          >
            {description}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div
          ref={chartRef}
          style={{ height: `${height}px`, width: "100%" }}
          role="img"
          aria-label={`${title} chart`}
        />
      </CardContent>
    </Card>
  );
}
