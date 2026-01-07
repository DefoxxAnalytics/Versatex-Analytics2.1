/**
 * Reports Module - Main Page
 *
 * Provides report generation, history, and scheduling functionality
 * with a tabbed interface.
 */
import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  FileText, PieChart, Users, BarChart2, Shield, TrendingDown,
  Download, Clock, Calendar, Trash2, Eye, Share2, PlayCircle,
  Loader2, FileSpreadsheet, FileType2, CheckCircle2, XCircle,
  AlertCircle, RefreshCw, Plus, Edit2
} from 'lucide-react';
import {
  useReportTemplates,
  useReportHistory,
  useReportSchedules,
  useGenerateReport,
  useDeleteReport,
  useDownloadReport,
  useReportStatus,
  useCreateSchedule,
  useUpdateSchedule,
  useDeleteSchedule,
  useRunScheduleNow,
} from '@/hooks/useReports';
import {
  ReportTemplate,
  ReportListItem,
  ReportType,
  ReportFormat,
  ReportStatus,
  ScheduleFrequency,
  ReportScheduleRequest,
} from '@/lib/api';
import { SkeletonCard } from '@/components/SkeletonCard';

// Icon mapping for report types
const REPORT_ICONS: Record<string, React.ElementType> = {
  'executive_summary': FileText,
  'spend_analysis': PieChart,
  'supplier_performance': Users,
  'pareto_analysis': BarChart2,
  'contract_compliance': Shield,
  'savings_opportunities': TrendingDown,
  'price_trends': TrendingDown,
  'custom': FileText,
};

// Status badge colors
const STATUS_COLORS: Record<ReportStatus, string> = {
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  generating: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
};

// Format icons
const FORMAT_ICONS: Record<ReportFormat, React.ElementType> = {
  pdf: FileText,
  xlsx: FileSpreadsheet,
  csv: FileType2,
};

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('generate');
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [generatingReportId, setGeneratingReportId] = useState<string | null>(null);

  // Form state for generation
  const [reportName, setReportName] = useState('');
  const [reportDescription, setReportDescription] = useState('');
  const [reportFormat, setReportFormat] = useState<ReportFormat>('pdf');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');

  // Schedule dialog state
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<ReportListItem | null>(null);
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleReportType, setScheduleReportType] = useState<ReportType>('spend_analysis');
  const [scheduleFormat, setScheduleFormat] = useState<ReportFormat>('pdf');
  const [scheduleFrequency, setScheduleFrequency] = useState<ScheduleFrequency>('weekly');

  // Queries
  const { data: templates = [], isLoading: templatesLoading } = useReportTemplates();
  const { data: historyData, isLoading: historyLoading, refetch: refetchHistory } = useReportHistory({ limit: 50 });
  const { data: schedules = [], isLoading: schedulesLoading, refetch: refetchSchedules } = useReportSchedules();

  // Poll for status when generating
  const { data: reportStatus } = useReportStatus(generatingReportId, !!generatingReportId);

  // Mutations
  const generateReport = useGenerateReport();
  const deleteReport = useDeleteReport();
  const downloadReport = useDownloadReport();
  const createSchedule = useCreateSchedule();
  const updateSchedule = useUpdateSchedule();
  const deleteSchedule = useDeleteSchedule();
  const runScheduleNow = useRunScheduleNow();

  // Effect to handle generation completion
  useEffect(() => {
    if (reportStatus?.status === 'completed') {
      toast.success('Report generated successfully');
      setGeneratingReportId(null);
      refetchHistory();
    } else if (reportStatus?.status === 'failed') {
      toast.error(`Report generation failed: ${reportStatus.error_message || 'Unknown error'}`);
      setGeneratingReportId(null);
      refetchHistory();
    }
  }, [reportStatus?.status]);

  const handleGenerateClick = (template: ReportTemplate) => {
    setSelectedTemplate(template);
    setReportName(`${template.name} - ${new Date().toLocaleDateString()}`);
    setReportDescription('');
    setReportFormat('pdf');
    setPeriodStart('');
    setPeriodEnd('');
    setGenerateDialogOpen(true);
  };

  const handleGenerate = async () => {
    if (!selectedTemplate) return;

    try {
      const result = await generateReport.mutateAsync({
        report_type: selectedTemplate.report_type,
        report_format: reportFormat,
        name: reportName,
        description: reportDescription,
        period_start: periodStart || undefined,
        period_end: periodEnd || undefined,
        async_generation: true,
      });

      setGenerateDialogOpen(false);

      if ('message' in result && result.id) {
        // Async generation started
        setGeneratingReportId(result.id);
        toast.info('Report generation started. This may take a moment...');
        setActiveTab('history');
      } else {
        // Sync generation completed
        toast.success('Report generated successfully');
        refetchHistory();
        setActiveTab('history');
      }
    } catch (error) {
      toast.error('Failed to generate report');
    }
  };

  const handleDownload = async (report: ReportListItem) => {
    try {
      await downloadReport.mutateAsync({
        reportId: report.id,
        format: report.report_format,
        filename: `${report.name}.${report.report_format}`,
      });
      toast.success('Download started');
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this report?')) return;

    try {
      await deleteReport.mutateAsync(reportId);
      toast.success('Report deleted');
    } catch (error) {
      toast.error('Failed to delete report');
    }
  };

  const handleRunSchedule = async (scheduleId: string) => {
    try {
      await runScheduleNow.mutateAsync(scheduleId);
      toast.success('Report generation triggered');
      refetchHistory();
    } catch (error) {
      toast.error('Failed to trigger report');
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return;

    try {
      await deleteSchedule.mutateAsync(scheduleId);
      toast.success('Schedule deleted');
    } catch (error) {
      toast.error('Failed to delete schedule');
    }
  };

  const handleOpenScheduleDialog = (schedule?: ReportListItem) => {
    if (schedule) {
      // Editing existing schedule
      setEditingSchedule(schedule);
      setScheduleName(schedule.name);
      setScheduleReportType(schedule.report_type);
      setScheduleFormat(schedule.report_format);
      setScheduleFrequency(schedule.schedule_frequency as ScheduleFrequency || 'weekly');
    } else {
      // Creating new schedule
      setEditingSchedule(null);
      setScheduleName('');
      setScheduleReportType('spend_analysis');
      setScheduleFormat('pdf');
      setScheduleFrequency('weekly');
    }
    setScheduleDialogOpen(true);
  };

  const handleSaveSchedule = async () => {
    if (!scheduleName.trim()) {
      toast.error('Please enter a schedule name');
      return;
    }

    try {
      const scheduleData: ReportScheduleRequest = {
        name: scheduleName,
        report_type: scheduleReportType,
        report_format: scheduleFormat,
        is_scheduled: true,
        schedule_frequency: scheduleFrequency,
      };

      if (editingSchedule) {
        await updateSchedule.mutateAsync({
          scheduleId: editingSchedule.id,
          data: scheduleData,
        });
        toast.success('Schedule updated');
      } else {
        await createSchedule.mutateAsync(scheduleData);
        toast.success('Schedule created');
      }

      setScheduleDialogOpen(false);
      refetchSchedules();
    } catch (error) {
      toast.error(editingSchedule ? 'Failed to update schedule' : 'Failed to create schedule');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground mt-1">
            Generate, schedule, and manage procurement reports
          </p>
        </div>
        {generatingReportId && (
          <Badge variant="outline" className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating report...
          </Badge>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-[400px] grid-cols-3">
          <TabsTrigger value="generate" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Generate
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            History
          </TabsTrigger>
          <TabsTrigger value="schedules" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Schedules
          </TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="mt-6">
          {templatesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => {
                const Icon = REPORT_ICONS[template.report_type] || FileText;
                return (
                  <Card
                    key={template.id}
                    className="cursor-pointer hover:border-primary transition-colors"
                    onClick={() => handleGenerateClick(template)}
                  >
                    <CardHeader>
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                          <Icon className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{template.name}</CardTitle>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{template.description}</CardDescription>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Report History</CardTitle>
              <Button variant="outline" size="sm" onClick={() => refetchHistory()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 bg-muted animate-pulse rounded" />
                  ))}
                </div>
              ) : historyData?.results.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No reports generated yet</p>
                  <Button
                    variant="link"
                    className="mt-2"
                    onClick={() => setActiveTab('generate')}
                  >
                    Generate your first report
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {historyData?.results.map((report) => {
                    const FormatIcon = FORMAT_ICONS[report.report_format] || FileText;
                    return (
                      <div
                        key={report.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <FormatIcon className="h-8 w-8 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{report.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {report.report_type_display} • {formatDateTime(report.generated_at || report.created_at)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge className={STATUS_COLORS[report.status]}>
                            {report.status === 'generating' && (
                              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                            )}
                            {report.status === 'completed' && (
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                            )}
                            {report.status === 'failed' && (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            {report.status_display}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {formatFileSize(report.file_size)}
                          </span>
                          <div className="flex gap-1">
                            {report.status === 'completed' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDownload(report)}
                                disabled={downloadReport.isPending}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(report.id)}
                              disabled={deleteReport.isPending}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedules Tab */}
        <TabsContent value="schedules" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Scheduled Reports</CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => refetchSchedules()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
                <Button size="sm" onClick={() => handleOpenScheduleDialog()}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Schedule
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {schedulesLoading ? (
                <div className="space-y-4">
                  {[1, 2].map((i) => (
                    <div key={i} className="h-16 bg-muted animate-pulse rounded" />
                  ))}
                </div>
              ) : schedules.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No scheduled reports</p>
                  <p className="text-sm mt-1">Scheduled reports will appear here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {schedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <Calendar className="h-8 w-8 text-muted-foreground" />
                        <div>
                          <div className="font-medium">{schedule.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {schedule.report_type_display} • {schedule.schedule_frequency}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-sm text-right">
                          <div className="text-muted-foreground">Next run:</div>
                          <div>{formatDateTime(schedule.next_run)}</div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRunSchedule(schedule.id)}
                            disabled={runScheduleNow.isPending}
                            title="Run now"
                          >
                            <PlayCircle className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleOpenScheduleDialog(schedule)}
                            title="Edit schedule"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteSchedule(schedule.id)}
                            disabled={deleteSchedule.isPending}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Generate Dialog */}
      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Generate {selectedTemplate?.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Report Name</Label>
              <Input
                id="name"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                placeholder="Enter report name"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                value={reportDescription}
                onChange={(e) => setReportDescription(e.target.value)}
                placeholder="Enter description"
                rows={2}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="format">Output Format</Label>
              <Select value={reportFormat} onValueChange={(v) => setReportFormat(v as ReportFormat)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF Document</SelectItem>
                  <SelectItem value="xlsx">Excel Spreadsheet</SelectItem>
                  <SelectItem value="csv">CSV File</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="start">Start Date (optional)</Label>
                <Input
                  id="start"
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="end">End Date (optional)</Label>
                <Input
                  id="end"
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGenerateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleGenerate} disabled={generateReport.isPending}>
              {generateReport.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Report
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingSchedule ? 'Edit Schedule' : 'Create Schedule'}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="schedule-name">Schedule Name</Label>
              <Input
                id="schedule-name"
                value={scheduleName}
                onChange={(e) => setScheduleName(e.target.value)}
                placeholder="e.g., Weekly Spend Report"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="schedule-report-type">Report Type</Label>
              <Select
                value={scheduleReportType}
                onValueChange={(v) => setScheduleReportType(v as ReportType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="spend_analysis">Spend Analysis</SelectItem>
                  <SelectItem value="supplier_performance">Supplier Performance</SelectItem>
                  <SelectItem value="executive_summary">Executive Summary</SelectItem>
                  <SelectItem value="pareto_analysis">Pareto Analysis</SelectItem>
                  <SelectItem value="contract_compliance">Contract Compliance</SelectItem>
                  <SelectItem value="savings_opportunities">Savings Opportunities</SelectItem>
                  <SelectItem value="price_trends">Price Trends</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="schedule-format">Output Format</Label>
              <Select
                value={scheduleFormat}
                onValueChange={(v) => setScheduleFormat(v as ReportFormat)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF Document</SelectItem>
                  <SelectItem value="xlsx">Excel Spreadsheet</SelectItem>
                  <SelectItem value="csv">CSV File</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="schedule-frequency">Frequency</Label>
              <Select
                value={scheduleFrequency}
                onValueChange={(v) => setScheduleFrequency(v as ScheduleFrequency)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="bi_weekly">Bi-Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Reports will be automatically generated on this schedule
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setScheduleDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveSchedule}
              disabled={createSchedule.isPending || updateSchedule.isPending}
            >
              {(createSchedule.isPending || updateSchedule.isPending) ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4 mr-2" />
                  {editingSchedule ? 'Update Schedule' : 'Create Schedule'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
