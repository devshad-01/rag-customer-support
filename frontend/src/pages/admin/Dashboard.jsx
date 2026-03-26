import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  MessageSquare,
  BarChart3,
  AlertTriangle,
  Clock,
  TrendingUp,
  Shield,
  ArrowRight,
  CheckCircle,
  Activity,
} from "lucide-react";
import { getOverview } from "@/services/analyticsApi";
import { getDocuments } from "@/services/documentApi";

function StatCard({ title, value, subtitle, icon: Icon, tone = "default" }) {
  const toneClass = {
    default: "text-muted-foreground",
    primary: "text-primary",
    success: "text-emerald-600",
    warning: "text-amber-600",
    danger: "text-red-600",
  }[tone];

  return (
    <Card className="border-border/70">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className="rounded-md bg-muted p-1.5">
            <Icon className={`h-4 w-4 ${toneClass}`} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="text-2xl font-semibold tracking-tight">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

function StatSkeleton() {
  return (
    <Card>
      <CardContent className="pt-6">
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16" />
      </CardContent>
    </Card>
  );
}

function formatMs(ms) {
  if (!ms || ms === 0) return "0s";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function AdminDashboard() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => getOverview(),
    refetchInterval: 30000,
  });

  const { data: docs, isLoading: loadingDocs } = useQuery({
    queryKey: ["admin-docs-count"],
    queryFn: () => getDocuments(1, 1),
    refetchInterval: 30000,
  });

  const loading = loadingOverview || loadingDocs;
  const totalDocs = docs?.total ?? 0;

  return (
    <div className="space-y-6">
      <Card className="border-border/70">
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-semibold tracking-tight">Dashboard Overview</h1>
                <Badge variant="secondary" className="text-[11px]">Admin</Badge>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                Monitor system health, support workload, and AI performance at a glance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-foreground">Key Metrics</h2>
          <p className="text-xs text-muted-foreground">Core activity and response indicators</p>
        </div>
      
      {/* Primary Stat Cards */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <StatSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Total Queries"
            value={overview?.total_queries ?? 0}
            subtitle={`${overview?.total_conversations ?? 0} conversations`}
            icon={MessageSquare}
            tone="primary"
          />
          <StatCard
            title="Documents Indexed"
            value={totalDocs}
            subtitle="Knowledge base"
            icon={FileText}
            tone="success"
          />
          <StatCard
            title="Escalations"
            value={overview?.total_escalations ?? 0}
            subtitle={`${overview?.escalation_rate ?? 0}% escalation rate`}
            icon={AlertTriangle}
            tone="danger"
          />
          <StatCard
            title="Avg Response Time"
            value={formatMs(overview?.avg_response_time_ms)}
            subtitle={`${overview?.active_tickets ?? 0} active tickets`}
            icon={Clock}
            tone="warning"
          />
        </div>
      )}
      </div>

      {/* Secondary Stats */}
      {!loading && (
        <div>
          <div className="mb-3">
            <h2 className="text-sm font-semibold text-foreground">Quality Metrics</h2>
            <p className="text-xs text-muted-foreground">Evidence, confidence, and ticket outcomes</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard
              title="Avg Confidence"
              value={`${((overview?.avg_confidence_score ?? 0) * 100).toFixed(1)}%`}
              subtitle="AI response quality"
              icon={Shield}
              tone="primary"
            />
            <StatCard
              title="Evidence Rate"
              value={`${overview?.evidence_rate ?? 0}%`}
              subtitle={`${overview?.queries_with_evidence ?? 0} queries with evidence`}
              icon={CheckCircle}
              tone="success"
            />
            <StatCard
              title="Resolved Tickets"
              value={overview?.resolved_tickets ?? 0}
              subtitle={`${overview?.active_tickets ?? 0} still active`}
              icon={Activity}
              tone="default"
            />
          </div>
        </div>
      )}

      <div>
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-foreground">Quick Actions</h2>
          <p className="text-xs text-muted-foreground">Jump to core admin workflows</p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-border/70">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-600" />
                Knowledge Base
              </CardTitle>
              <CardDescription>
                Upload and manage PDF documents for the AI knowledge base
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" asChild>
                <Link to="/admin/documents">
                  Manage Documents
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-amber-600" />
                Analytics
              </CardTitle>
              <CardDescription>
                View query trends, AI performance, and escalation metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" asChild>
                <Link to="/admin/analytics">
                  View Analytics
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-violet-600" />
                Reports
              </CardTitle>
              <CardDescription>
                Export CSV and PDF reports for offline analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" asChild>
                <Link to="/admin/reports">
                  Export Reports
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
