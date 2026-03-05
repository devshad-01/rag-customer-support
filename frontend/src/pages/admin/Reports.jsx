import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Download,
  FileText,
  FileSpreadsheet,
  Loader2,
  CalendarDays,
  BarChart3,
  AlertTriangle,
  Users,
  Search,
  CheckCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  downloadBlob,
  getQueryLogsCSV,
  getEscalationCSV,
  getEscalationPDF,
  getAgentPerformanceCSV,
  getAnalyticsSummaryCSV,
  getAnalyticsPDF,
} from "@/services/reportApi";

// ── Report definitions ──────────────────────────────────────
const REPORTS = [
  {
    id: "analytics-pdf",
    title: "Analytics Report",
    description:
      "Comprehensive PDF report with overview metrics, confidence distribution, escalation breakdown, agent performance, and top queries.",
    icon: BarChart3,
    formats: ["pdf"],
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    useDateFilter: true,
  },
  {
    id: "query-logs",
    title: "Query Logs",
    description:
      "Complete log of all customer queries including confidence scores, sources, escalation status, and response times.",
    icon: Search,
    formats: ["csv"],
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    useDateFilter: true,
  },
  {
    id: "escalations",
    title: "Escalation Report",
    description:
      "All escalated tickets with status, priority, reason, assignment, and resolution times.",
    icon: AlertTriangle,
    formats: ["csv", "pdf"],
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    useDateFilter: true,
  },
  {
    id: "agent-performance",
    title: "Agent Performance",
    description:
      "Agent workload summary — tickets assigned, resolved, pending, and average resolution time.",
    icon: Users,
    formats: ["csv"],
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    useDateFilter: false,
  },
  {
    id: "analytics-summary",
    title: "Analytics Summary",
    description:
      "Overview metrics, confidence distribution, escalation breakdown, and daily trends in tabular CSV format.",
    icon: FileSpreadsheet,
    formats: ["csv"],
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    useDateFilter: true,
  },
];

// ── API mapping ─────────────────────────────────────────────
const DOWNLOAD_FNS = {
  "analytics-pdf__pdf": { fn: getAnalyticsPDF, filename: "analytics_report.pdf" },
  "query-logs__csv": { fn: getQueryLogsCSV, filename: "query_logs.csv" },
  "escalations__csv": { fn: getEscalationCSV, filename: "escalations.csv" },
  "escalations__pdf": { fn: getEscalationPDF, filename: "escalation_report.pdf" },
  "agent-performance__csv": { fn: getAgentPerformanceCSV, filename: "agent_performance.csv" },
  "analytics-summary__csv": { fn: getAnalyticsSummaryCSV, filename: "analytics_summary.csv" },
};

export default function Reports() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [downloading, setDownloading] = useState(null); // "id__format"

  const handleDownload = async (reportId, format) => {
    const key = `${reportId}__${format}`;
    const cfg = DOWNLOAD_FNS[key];
    if (!cfg) return;

    setDownloading(key);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const blob = await cfg.fn(params);
      downloadBlob(blob, cfg.filename);
      toast.success(`${format.toUpperCase()} downloaded successfully`);
    } catch (err) {
      console.error("Download failed:", err);
      toast.error("Download failed — please try again");
    } finally {
      setDownloading(null);
    }
  };

  const clearDates = () => {
    setStartDate("");
    setEndDate("");
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-muted-foreground">
          Export query logs, analytics, and performance data as CSV or PDF
        </p>
      </div>

      {/* Date Range Filter */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Date Range Filter</CardTitle>
          </div>
          <CardDescription>
            Apply a date range to all reports that support filtering. Leave empty
            for all-time data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-44"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-44"
              />
            </div>
            {(startDate || endDate) && (
              <Button variant="ghost" size="sm" onClick={clearDates}>
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Report Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {REPORTS.map((report) => {
          const Icon = report.icon;
          return (
            <Card key={report.id} className="flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className={`rounded-lg p-2 ${report.bgColor}`}>
                    <Icon className={`h-5 w-5 ${report.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base">{report.title}</CardTitle>
                    <div className="flex gap-1.5 mt-1">
                      {report.formats.map((f) => (
                        <Badge key={f} variant="secondary" className="text-[10px] px-1.5 py-0">
                          {f.toUpperCase()}
                        </Badge>
                      ))}
                      {report.useDateFilter && (startDate || endDate) && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                          Filtered
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="flex flex-col flex-1">
                <p className="text-sm text-muted-foreground mb-4 flex-1">
                  {report.description}
                </p>

                <div className="flex gap-2">
                  {report.formats.map((format) => {
                    const key = `${report.id}__${format}`;
                    const isDownloading = downloading === key;
                    const isCSV = format === "csv";

                    return (
                      <Button
                        key={format}
                        variant={isCSV ? "outline" : "default"}
                        size="sm"
                        className="flex-1"
                        disabled={downloading !== null}
                        onClick={() => handleDownload(report.id, format)}
                      >
                        {isDownloading ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : isCSV ? (
                          <FileSpreadsheet className="mr-2 h-4 w-4" />
                        ) : (
                          <FileText className="mr-2 h-4 w-4" />
                        )}
                        {isDownloading
                          ? "Generating…"
                          : `Download ${format.toUpperCase()}`}
                      </Button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Footer info */}
      <Separator className="my-6" />
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <CheckCircle className="h-3.5 w-3.5" />
        <span>
          All reports are generated on-demand from live data. PDF reports include
          formatted tables and metrics. CSV files can be opened in Excel or Google
          Sheets for further analysis.
        </span>
      </div>
    </div>
  );
}
