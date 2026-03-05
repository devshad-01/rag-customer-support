import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import {
  MessageSquare,
  AlertTriangle,
  TrendingUp,
  Clock,
  BarChart3,
  Search,
  Users,
  CalendarDays,
  RefreshCw,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  getOverview,
  getQueryTrends,
  getResponsePerformance,
  getConfidenceTrend,
  getEscalationMetrics,
  getEscalationTrend,
  getAgentPerformance,
  getTopQueries,
} from "@/services/analyticsApi";

const PIE_COLORS = ["#22c55e", "#eab308", "#ef4444"];

function formatMs(ms) {
  if (!ms || ms === 0) return "0s";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
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

function ChartSkeleton() {
  return (
    <div className="space-y-3 p-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-[200px] w-full" />
    </div>
  );
}

export default function Analytics() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [interval, setInterval] = useState("day");

  const dateParams = useMemo(() => {
    const p = {};
    if (startDate) p.start_date = startDate;
    if (endDate) p.end_date = endDate;
    return p;
  }, [startDate, endDate]);

  const trendParams = useMemo(
    () => ({ ...dateParams, interval }),
    [dateParams, interval]
  );

  // ── Queries ──────────────────────────────────────────────
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["analytics-overview", dateParams],
    queryFn: () => getOverview(dateParams),
    refetchInterval: 30000,
  });

  const { data: queryTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ["analytics-query-trends", trendParams],
    queryFn: () => getQueryTrends(trendParams),
  });

  const { data: performance, isLoading: loadingPerf } = useQuery({
    queryKey: ["analytics-response-perf", dateParams],
    queryFn: () => getResponsePerformance(dateParams),
  });

  const { data: confTrend, isLoading: loadingConfTrend } = useQuery({
    queryKey: ["analytics-conf-trend", trendParams],
    queryFn: () => getConfidenceTrend(trendParams),
  });

  const { data: escMetrics, isLoading: loadingEsc } = useQuery({
    queryKey: ["analytics-escalations", dateParams],
    queryFn: () => getEscalationMetrics(dateParams),
  });

  const { data: escTrend, isLoading: loadingEscTrend } = useQuery({
    queryKey: ["analytics-esc-trend", trendParams],
    queryFn: () => getEscalationTrend(trendParams),
  });

  const { data: agentPerf, isLoading: loadingAgents } = useQuery({
    queryKey: ["analytics-agents"],
    queryFn: getAgentPerformance,
  });

  const { data: topQueries, isLoading: loadingTop } = useQuery({
    queryKey: ["analytics-top-queries"],
    queryFn: () => getTopQueries({ limit: 10 }),
  });

  // ── Chart data ───────────────────────────────────────────
  const pieData = useMemo(() => {
    if (!performance?.confidence_distribution) return [];
    const d = performance.confidence_distribution;
    return [
      { name: "High (≥0.7)", value: d.high },
      { name: "Medium (0.4–0.7)", value: d.medium },
      { name: "Low (<0.4)", value: d.low },
    ].filter((i) => i.value > 0);
  }, [performance]);

  const escByReasonData = useMemo(() => {
    if (!escMetrics?.by_reason) return [];
    const r = escMetrics.by_reason;
    return [
      { name: "Low Confidence", count: r.low_confidence },
      { name: "Customer Request", count: r.customer_requested },
      { name: "Other", count: r.other },
    ].filter((i) => i.count > 0);
  }, [escMetrics]);

  const clearDates = () => {
    setStartDate("");
    setEndDate("");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header + Date Filters */}
      <div className="flex flex-col sm:flex-row sm:items-end gap-4 justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground text-sm">
            Query trends, AI performance, and escalation metrics
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5">
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-36 h-8 text-xs"
              placeholder="Start date"
            />
            <span className="text-muted-foreground text-xs">to</span>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-36 h-8 text-xs"
              placeholder="End date"
            />
          </div>
          <Select value={interval} onValueChange={setInterval}>
            <SelectTrigger className="w-24 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Daily</SelectItem>
              <SelectItem value="week">Weekly</SelectItem>
              <SelectItem value="month">Monthly</SelectItem>
            </SelectContent>
          </Select>
          {(startDate || endDate) && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 text-xs"
              onClick={clearDates}
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* ── Overview Cards ────────────────────────────────── */}
      {loadingOverview ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Queries"
            value={overview?.total_queries?.toLocaleString() ?? 0}
            subtitle={`${overview?.total_conversations ?? 0} conversations`}
            icon={MessageSquare}
          />
          <StatCard
            title="Escalation Rate"
            value={`${overview?.escalation_rate ?? 0}%`}
            subtitle={`${overview?.total_escalations ?? 0} escalated`}
            icon={AlertTriangle}
          />
          <StatCard
            title="Avg Confidence"
            value={`${((overview?.avg_confidence_score ?? 0) * 100).toFixed(1)}%`}
            subtitle={`${overview?.evidence_rate ?? 0}% with evidence`}
            icon={TrendingUp}
          />
          <StatCard
            title="Avg Response Time"
            value={formatMs(overview?.avg_response_time_ms)}
            subtitle={`${overview?.active_tickets ?? 0} active / ${overview?.resolved_tickets ?? 0} resolved tickets`}
            icon={Clock}
          />
        </div>
      )}

      {/* ── Query Trends + Confidence Distribution ────────── */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Query Trends
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingTrends ? (
              <ChartSkeleton />
            ) : !queryTrends?.trends?.length ? (
              <div className="h-[250px] flex items-center justify-center text-sm text-muted-foreground">
                No query data available yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={queryTrends.trends}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="query_count"
                    name="Queries"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="escalation_count"
                    name="Escalations"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Confidence Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingPerf ? (
              <ChartSkeleton />
            ) : !pieData.length ? (
              <div className="h-[250px] flex items-center justify-center text-sm text-muted-foreground">
                No data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name.split(" ")[0]} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {pieData.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
            {performance && (
              <div className="grid grid-cols-3 gap-2 mt-2 text-center text-xs">
                <div>
                  <div className="font-semibold text-green-500">
                    {performance.confidence_distribution.high}
                  </div>
                  <div className="text-muted-foreground">High</div>
                </div>
                <div>
                  <div className="font-semibold text-yellow-500">
                    {performance.confidence_distribution.medium}
                  </div>
                  <div className="text-muted-foreground">Medium</div>
                </div>
                <div>
                  <div className="font-semibold text-red-500">
                    {performance.confidence_distribution.low}
                  </div>
                  <div className="text-muted-foreground">Low</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Confidence Trend + Escalation Trend ──────────── */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Confidence Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingConfTrend ? (
              <ChartSkeleton />
            ) : !confTrend?.trends?.length ? (
              <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                No data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={confTrend.trends}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                  />
                  <YAxis
                    domain={[0, 1]}
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v) => `${(v * 100).toFixed(1)}%`}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_confidence"
                    name="Avg Confidence"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> Escalation Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingEscTrend ? (
              <ChartSkeleton />
            ) : !escTrend?.trends?.length ? (
              <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                No data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={escTrend.trends}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar
                    dataKey="escalation_count"
                    name="Escalations"
                    fill="#ef4444"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Escalation Breakdown + Summary ───────────────── */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Escalation Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingEsc ? (
              <ChartSkeleton />
            ) : !escByReasonData.length ? (
              <div className="h-[200px] flex items-center justify-center text-sm text-muted-foreground">
                No escalation data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={escByReasonData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 11 }}
                    className="fill-muted-foreground"
                    allowDecimals={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 11 }}
                    width={120}
                    className="fill-muted-foreground"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar
                    dataKey="count"
                    name="Count"
                    fill="#f97316"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Escalation Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingEsc ? (
              <div className="space-y-3">
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
                <Skeleton className="h-6 w-full" />
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    Total Escalations
                  </span>
                  <span className="font-bold">
                    {escMetrics?.total_escalations ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    Escalation Rate
                  </span>
                  <span className="font-bold">
                    {escMetrics?.escalation_rate ?? 0}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    Resolved
                  </span>
                  <Badge variant="outline" className="text-green-600">
                    {escMetrics?.resolved_count ?? 0}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">
                    Pending
                  </span>
                  <Badge variant="outline" className="text-yellow-600">
                    {escMetrics?.pending_count ?? 0}
                  </Badge>
                </div>
                {escMetrics?.avg_resolution_time_hours != null && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">
                      Avg Resolution
                    </span>
                    <span className="font-bold">
                      {escMetrics.avg_resolution_time_hours}h
                    </span>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Agent Performance Table ──────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4" /> Agent Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loadingAgents ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !agentPerf?.agents?.length ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No agent data available
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent</TableHead>
                  <TableHead className="text-center">Assigned</TableHead>
                  <TableHead className="text-center">Resolved</TableHead>
                  <TableHead className="text-center">Pending</TableHead>
                  <TableHead className="text-center">Avg Resolution</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agentPerf.agents.map((agent) => (
                  <TableRow key={agent.agent_id}>
                    <TableCell className="font-medium">
                      {agent.agent_name}
                    </TableCell>
                    <TableCell className="text-center">
                      {agent.tickets_assigned}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline" className="text-green-600">
                        {agent.tickets_resolved}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {agent.pending_tickets > 0 ? (
                        <Badge variant="outline" className="text-yellow-600">
                          {agent.pending_tickets}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {agent.avg_resolution_time_hours != null
                        ? `${agent.avg_resolution_time_hours}h`
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ── Top Queries ──────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Search className="h-4 w-4" /> Top Queries
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loadingTop ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : !topQueries?.queries?.length ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No query data available yet
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Query</TableHead>
                  <TableHead className="text-center">Count</TableHead>
                  <TableHead className="text-center">Avg Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topQueries.queries.map((q, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="text-muted-foreground">
                      {idx + 1}
                    </TableCell>
                    <TableCell className="max-w-md truncate text-sm">
                      {q.query_text}
                    </TableCell>
                    <TableCell className="text-center font-medium">
                      {q.count}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge
                        variant="outline"
                        className={
                          q.avg_confidence >= 0.7
                            ? "text-green-600"
                            : q.avg_confidence >= 0.4
                              ? "text-yellow-600"
                              : "text-red-600"
                        }
                      >
                        {(q.avg_confidence * 100).toFixed(0)}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
