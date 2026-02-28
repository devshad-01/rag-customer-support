gitimport { useQuery } from "@tanstack/react-query";
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
  Users,
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

function StatCard({ title, value, subtitle, icon: Icon, color }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className={`h-4 w-4 ${color || "text-muted-foreground"}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
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
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground">
          System overview and management
        </p>
      </div>

      {/* Primary Stat Cards */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <StatSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Queries"
            value={overview?.total_queries ?? 0}
            subtitle={`${overview?.total_conversations ?? 0} conversations`}
            icon={MessageSquare}
            color="text-blue-500"
          />
          <StatCard
            title="Documents Indexed"
            value={totalDocs}
            subtitle="Knowledge base"
            icon={FileText}
            color="text-green-500"
          />
          <StatCard
            title="Escalations"
            value={overview?.total_escalations ?? 0}
            subtitle={`${overview?.escalation_rate ?? 0}% escalation rate`}
            icon={AlertTriangle}
            color="text-red-500"
          />
          <StatCard
            title="Avg Response Time"
            value={formatMs(overview?.avg_response_time_ms)}
            subtitle={`${overview?.active_tickets ?? 0} active tickets`}
            icon={Clock}
            color="text-orange-500"
          />
        </div>
      )}

      {/* Secondary Stats */}
      {!loading && (
        <div className="grid gap-4 md:grid-cols-3 mt-4">
          <StatCard
            title="Avg Confidence"
            value={`${((overview?.avg_confidence_score ?? 0) * 100).toFixed(1)}%`}
            subtitle="AI response quality"
            icon={Shield}
            color="text-purple-500"
          />
          <StatCard
            title="Evidence Rate"
            value={`${overview?.evidence_rate ?? 0}%`}
            subtitle={`${overview?.queries_with_evidence ?? 0} queries with evidence`}
            icon={CheckCircle}
            color="text-emerald-500"
          />
          <StatCard
            title="Resolved Tickets"
            value={overview?.resolved_tickets ?? 0}
            subtitle={`${overview?.active_tickets ?? 0} still active`}
            icon={Activity}
            color="text-cyan-500"
          />
        </div>
      )}

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3 mt-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4 text-green-500" />
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

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-orange-500" />
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

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-purple-500" />
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
  );
}
