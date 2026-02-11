import api from "./api";

export async function getOverview(params = {}) {
  const { data } = await api.get("/analytics/overview", { params });
  return data;
}

export async function getQueryTrends(params = {}) {
  const { data } = await api.get("/analytics/query-trends", { params });
  return data;
}

export async function getEscalationStats(params = {}) {
  const { data } = await api.get("/analytics/escalations", { params });
  return data;
}

export async function getConfidenceDistribution(params = {}) {
  const { data } = await api.get("/analytics/confidence-distribution", { params });
  return data;
}
