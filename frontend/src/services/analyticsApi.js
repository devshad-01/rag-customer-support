import api from "./api";

export async function getOverview(params = {}) {
  const { data } = await api.get("/analytics/overview", { params });
  return data;
}

export async function getQueryTrends(params = {}) {
  const { data } = await api.get("/analytics/query-trends", { params });
  return data;
}

export async function getPeakHours() {
  const { data } = await api.get("/analytics/peak-hours");
  return data;
}

export async function getResponsePerformance(params = {}) {
  const { data } = await api.get("/analytics/response-performance", { params });
  return data;
}

export async function getConfidenceTrend(params = {}) {
  const { data } = await api.get("/analytics/confidence-trend", { params });
  return data;
}

export async function getEscalationMetrics(params = {}) {
  const { data } = await api.get("/analytics/escalations", { params });
  return data;
}

export async function getEscalationTrend(params = {}) {
  const { data } = await api.get("/analytics/escalation-trend", { params });
  return data;
}

export async function getAgentPerformance() {
  const { data } = await api.get("/analytics/agents");
  return data;
}

export async function getTopQueries(params = {}) {
  const { data } = await api.get("/analytics/top-queries", { params });
  return data;
}
