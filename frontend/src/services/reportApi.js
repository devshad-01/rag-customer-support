import api from "./api";

export async function getQueryLogsCSV(params = {}) {
  const { data } = await api.get("/reports/query-logs", {
    params: { ...params, format: "csv" },
    responseType: "blob",
  });
  return data;
}

export async function getAnalyticsPDF(params = {}) {
  const { data } = await api.get("/reports/analytics", {
    params: { ...params, format: "pdf" },
    responseType: "blob",
  });
  return data;
}
